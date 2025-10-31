import shutil
import requests
from flask import jsonify, Flask, request, send_file
from flask_cors import CORS
import concurrent.futures
import os
import base64
import cv2
import json
from volcenginesdkarkruntime import Ark
import re
from PIL import ImageFont, ImageDraw, Image
import numpy as np
import random
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import time
from pathlib import Path
import logging
import argparse


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置参数
DEFAULT_MODEL = "doubao-seed-1-6-vision-250815"  # 替换为实际的模型ID
# DEFAULT_MODEL = "ep-20250909143705-sg8sb"  # 替换为实际的模型ID
# DEFAULT_MODEL = "doubao-seed-1-6-flash-250828"  # 替换为实际的模型ID
API_KEY = "3702a65f-dfa0-43d7-a023-9f7cbde1fab8"
picture_path = './static/frontend_screenshots'

PROMPT = """
    你是一名施工安全检测专家。请基于输入的施工现场图片完成检测，并**只输出一个 JSON 数组**，不允许出现任何额外文字、注释或代码围栏。

【任务要求】
- 对图中的隐患进行排查，仅列出置信度高的隐患，若看不清或模棱两可的隐患不需要列出，并设置 uncertain=true 且给出 uncertain_reason。
- 图中风险度低的隐患不需要列出
- uncertain<0.7的隐患不需要列出
- 所有 bbox 坐标均为**相对归一化**到 0~1000 的整数（四舍五入），字段为：
  "bbox": {"x1":int,"y1":int,"x2":int,"y2":int}，且 0 ≤ x1 < x2 ≤ 1000、0 ≤ y1 < y2 ≤ 1000。
- 类别（category）必须取自以下**固定枚举**：
  ["基坑安全隐患","桩基设备隐患","脚手架安全隐患","起重设备隐患","高空作业隐患",
   "施工用电隐患","设备安全隐患","人员个体防护隐患","材料堆放隐患","环境安全隐患",
   "管理安全隐患","其他隐患"]

【每个数组元素（即一条隐患）必须包含字段】
{
  "version": "hazard_v1",
  "id": "h1",
  "category": <枚举>,
  "bbox": {"x1": <int 0..1000>, "y1": <int 0..1000>, "x2": <int 0..1000>, "y2": <int 0..1000>},
  "risk_level": "Ⅰ" | "Ⅱ" | "Ⅲ" | "Ⅳ" | "Ⅴ", 其中，Ⅰ级风险等级最高，V级最弱
  "location_text": "<≤40字的一句话>",
  "scene": "<≤60字的一句话>",
  "standard_ref": "《规范名-年份》条款号：条款要点",
  "consequence": "<≤40字>",
  "case_ref": "<一句话或“无”>",
  "recommendations": ["<整改建议1>","<整改建议2>", "..."],
  "confidence": <0~1 的数字>,
  "uncertain": <true|false>,
  "uncertain_reason": "<若 uncertain=true 则必填，≤30字>"
}

【输出格式硬性要求（模型必须遵守）】
1) 只输出 JSON 数组，不允许任何额外字符（如“===分隔线===”或自然语言）。
2) 坐标一律为整数；risk_level 仅能是“高/中/低”；category 仅能取固定枚举值。
3) 若无法完全确定，请输出最可能的隐患并设置 uncertain=true，同时给出 uncertain_reason。
    """

class SafetyInspector:
    def __init__(self, api_key, model_id=DEFAULT_MODEL, output_dir="output", max_workers=9):
        self.client = Ark(api_key=api_key)
        self.model_id = model_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers

        # 初始化字体
        try:
            self.font = ImageFont.truetype("./font/simhei.ttf", 10)
        except OSError:
            logger.warning("未找到 simhei.ttf 字体，使用默认字体")
            self.font = ImageFont.load_default()

        # 固定随机种子以保证颜色一致性
        self.rng = random.Random(42)

    def strip_bbox_tags(self, bbox: str) -> str:
        """去掉bbox标签"""
        s = bbox.strip()
        s = re.sub(r"</?bbox>", "", s, flags=re.IGNORECASE).strip()
        return s

    def get_category_colors(self, objects):
        """为每个类别分配颜色"""
        detected_cats = sorted({obj.get("category", "其他隐患") for obj in objects})
        hues = self.rng.sample(range(0, 180), k=len(detected_cats))
        category_colors = {}
        for cat, h in zip(detected_cats, hues):
            s, v = 200, 255
            bgr = cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2BGR)[0][0]
            category_colors[cat] = (int(bgr[0]), int(bgr[1]), int(bgr[2]))
        return category_colors

    def draw_bboxes(self, image_path, objects, output_path):
        """在图像上绘制边界框"""
        image = cv2.imread(str(image_path))
        if image is None:
            raise RuntimeError(f"无法读取图片: {image_path}")

        category_colors = self.get_category_colors(objects)

        for i, obj in enumerate(objects):
            category = obj.get("category", "其他隐患")
            bbox = obj.get("bbox", "")

            if not bbox:
                logger.warning(f"第 {i + 1} 个对象缺少 bbox，已跳过")
                continue

            try:
                x_min, y_min, x_max, y_max = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
                h, w = image.shape[:2]
                x_min_real = int(x_min * w / 1000)
                y_min_real = int(y_min * h / 1000)
                x_max_real = int(x_max * w / 1000)
                y_max_real = int(y_max * h / 1000)

                color = category_colors.get(category, (255, 255, 255))

                # 半透明填充
                overlay = image.copy()
                alpha_fill = 0.25
                cv2.rectangle(overlay, (x_min_real, y_min_real), (x_max_real, y_max_real), color, -1)
                image = cv2.addWeighted(overlay, alpha_fill, image, 1 - alpha_fill, 0)

                # 细边框
                cv2.rectangle(image, (x_min_real, y_min_real), (x_max_real, y_max_real), color, 1)

                # 标签背景和文字
                text = category
                pad = 5

                try:
                    x0, y0, x1, y1 = self.font.getbbox(text)
                except AttributeError:
                    _tmp = Image.new("RGB", (1, 1))
                    _draw = ImageDraw.Draw(_tmp)
                    x0, y0, x1, y1 = _draw.textbbox((0, 0), text, font=self.font)

                text_width = x1 - x0
                text_height = y1 - y0
                bg_width = text_width + 2 * pad
                bg_height = text_height + 2 * pad

                overlay2 = image.copy()
                alpha_label = 0.40
                cv2.rectangle(overlay2, (x_min_real, y_min_real),
                              (x_min_real + bg_width, y_min_real + bg_height), color, -1)
                image = cv2.addWeighted(overlay2, alpha_label, image, 1 - alpha_label, 0)

                pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_img)
                draw.text((x_min_real + pad, y_min_real + pad), text, font=self.font, fill=(0, 0, 0))
                image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            except Exception as e:
                logger.error(f"绘制第 {i + 1} 个边界框时出错: {e}")
                continue

        cv2.imwrite(str(output_path), image)
        logger.info(f"成功保存标注图片: {output_path}")

    def process_single_image(self, image_path):
        try:
            logger.info(f"开始处理图片: {image_path}")

            # 读取图像并转为base64编码
            with open(image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')

            # 调用模型
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{
                    "role": "user",
                    "content": [{
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                    }, {
                        "type": "text",
                        "text": PROMPT
                    }]
                }],
                temperature=0.2,
                top_p=0.6,
                max_tokens=32000,
            )
            model_time = time.time() - start_time

            bbox_content = response.choices[0].message.content

            # 解析JSON
            objects = json.loads(bbox_content)

            # 保存文本结果
            image_name = Path(image_path).stem
            result_dir = self.output_dir / image_name
            result_dir.mkdir(exist_ok=True)

            # 保存JSON结果
            with open(result_dir / "检测结果.json", "w", encoding="utf-8") as f:
                json.dump(objects, f, ensure_ascii=False, indent=2)

            # 绘制边界框
            output_image_path = result_dir / f"{image_name}_with_bboxes.png"
            self.draw_bboxes(image_path, objects, output_image_path)

            logger.info(f"完成处理图片: {image_path} (耗时: {model_time:.2f}秒)")

            return {
                "success": True,
                "image_path": str(image_path),
                "result_dir": str(result_dir),
                "objects_count": len(objects),
                "processing_time": model_time
            }

        except Exception as e:
            logger.error(f"处理图片 {image_path} 时出错: {e}")
            return {
                "success": False,
                "image_path": str(image_path),
                "error": str(e)
            }

    def process_batch(self, image_paths, max_workers=None):
        max_workers = max_workers or self.max_workers
        results = []

        logger.info(f"开始批量处理 {len(image_paths)} 张图片，最大并发数: {max_workers}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_path = {
                executor.submit(self.process_single_image, path): path
                for path in image_paths
            }

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_path):
                try:
                    result = future.result()
                    results.append(result)
                    if result["success"]:
                        logger.info(f"✓ {result['image_path']} 处理成功")
                    else:
                        logger.error(f"✗ {result['image_path']} 处理失败: {result['error']}")
                except Exception as e:
                    path = future_to_path[future]
                    logger.error(f"✗ {path} 处理异常: {e}")
                    results.append({
                        "success": False,
                        "image_path": str(path),
                        "error": str(e)
                    })

        # 统计结果
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        total_time = max(r.get("processing_time", 0) for r in results if r["success"])
        logger.info(f"批量处理完成: 成功 {successful} 张，失败 {failed} 张，总耗时 {total_time:.2f}秒")

        return results

app = Flask(__name__)
CORS(app, resources=r'/*')
app.json.ensure_ascii = False

@app.route('/hello', methods=['GET'])
def holle():
    try:
        return jsonify({
            'code': 200,
            'msg': '交互成功',
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': '交互失败',
            'data': 'bye'
        })

@app.route("/reset", methods=['POST'])
def reset():
    folder_path = "./static/batch_output"

    # 列出文件夹内的所有内容（包括文件和子文件夹）
    if os.path.exists(folder_path):
        contents = os.listdir(folder_path)
        print("batch_output里的内容：", contents)
        try:
            # 直接删除整个文件夹及其所有内容
            shutil.rmtree(folder_path)
            print(f"已彻底删除文件夹及其所有内容: {folder_path}")
        except Exception as e:
            print(f"删除失败: {e}")
    print("重置成功")
    return jsonify({
        'code': 200,
        'msg': '成功reset',
    })

@app.route('/save-screenshots', methods=['POST'])
def save_screenshots_base64(folder_path='./static/frontend_screenshots'):
    # folder_path='./static/frontend_screenshots'
    # 声明使用全局变量
    count=0
    print("上传成功")
    print(request.files)
    files = request.files.getlist("file")

    # 确保上传目录存在
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    print(files)
    for file in files:
        print(file)
        if file and file.filename != '':
            count += 1
            print(count)
            # 获取文件后缀
            file_ext = os.path.splitext(file.filename)[1].lower()
            # 使用计数器生成唯一文件名
            new_filename = f"screenshot_{count}{file_ext}"

            # new_filename = f"screenshot{file_ext}"
            print(new_filename)
            file_path = os.path.join(folder_path, new_filename)

            # 保存文件
            file.save(file_path)
        else:
            return jsonify({
                'code': 200,
                'msg': str(count)+'图片保存失败',
            })
            # 记录文件信息
    return jsonify({
        'code': 200,
        'msg': '图片保存成功',
        'data': {
            'upload_count': count,  # 返回当前计数
        }
    })

@app.route("/aitoanalyzes",methods=['GET'])
def aitoanalyzes():
    upload_count=request.args.get("upload_count")
    print("分析中...")
    try:
    # 创建检测器实例
        inspector = SafetyInspector(
            api_key=API_KEY,
            model_id=DEFAULT_MODEL,
            output_dir="static/batch_output",
            max_workers=9  # 根据API限制调整并发数
        )
        upload_count = len(os.listdir(picture_path))
        folder = Path(picture_path)
        allowed_exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif", ".tif", ".tiff"}
        image_list = []
        for i in range(int(upload_count)):
            base = f"screenshot_{i+1}"
            # 匹配 screenshot_i.*，再按允许的后缀过滤（大小写不敏感）
            candidates = [p for p in folder.glob(base + ".*") if p.suffix.lower() in allowed_exts]
            if candidates:
                # 可选：按你偏好的后缀优先级取第一个
                order = {".png":0, ".jpg":1, ".jpeg":2, ".bmp":3, ".webp":4, ".gif":5, ".tif":6, ".tiff":7}
                candidates.sort(key=lambda p: order.get(p.suffix.lower(), 999))
                image_list.append(str(candidates[0]))
            else:
                print(f"未找到：{base}.[{', '.join(e.strip('.') for e in allowed_exts)}]")
        print(upload_count)
        print(image_list)
        # 过滤存在的图片
        existing_images = [img for img in image_list if os.path.exists(img)]
        if existing_images:
            results = inspector.process_batch(existing_images)
            print(f"处理完成: {len([r for r in results if r['success']])}/{len(results)} 成功")
        else:
            return jsonify({'code': 500,'msg': '分析失败',})
        return jsonify({'code': 200,'msg': '正在分析',})
    except Exception as e:
        print(e)
        return jsonify({'code':500,"message": "数据接收失败","data": ""}),
    # try:
    #     # 创建检测器实例
    #     inspector = SafetyInspector(
    #         api_key=API_KEY,
    #         model_id=DEFAULT_MODEL,
    #         output_dir="static/batch_output",
    #         max_workers=9  # 根据API限制调整并发数
    #     )
    #
    #     # 方式1: 处理指定图片列表
    #     image_list = [
    #         "./static/frontend_screenshots/screenshot_"+str(i+1)+".png" for i in range(int(upload_count))
    #     ]
    #     print(upload_count)
    #     print(image_list)
    #     # 过滤存在的图片
    #     existing_images = [img for img in image_list if os.path.exists(img)]
    #     if existing_images:
    #         results = inspector.process_batch(existing_images)
    #         print(f"处理完成: {len([r for r in results if r['success']])}/{len(results)} 成功")
    #     else:
    #         return jsonify({
    #             'code': 500,
    #             'msg': '分析失败',
    #         })
    #     return jsonify({
    #         'code': 200,
    #         'msg': '正在分析',
    #     })
    except Exception as e:
        print(e)
        return jsonify({
            "message": "数据接收失败",
            "data": ""
        }), 500

@app.route('/issuccess/<id>')
def issSuccess(id):
    folder_path = "./static/batch_output"
    # 列出文件夹内的所有内容（包括文件和子文件夹）
    contents = os.listdir(folder_path)
    print("batch_output里的内容：", contents)

    filesData= {}

    if "screenshot_"+str(id) in contents:
        print(id+"分析成功")
        files_path='./static/batch_output/' + "screenshot_" + str(id)
        for filename in os.listdir(files_path):
            if filename.endswith(".md"):
                file_path = files_path + '/' + filename
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                print(text_content)
                # {'part2_summary': part2_summary, 'part3_details': part3_details, 'part4_advice': part4_advice}
                if filename == '隐患汇总表.md':
                    filesData['part2_summary'] = text_content
                if filename == '隐患详情分析.md':
                    filesData['part3_details'] = text_content
                if filename == '安全建议.md':
                    filesData['part4_advice'] = text_content
        return jsonify({
            'code': 200,
            'msg': id+'文件分析成功',
            'data':filesData
        })
    else:
        return jsonify({
            'code': 201,
            'msg': id+'文件还在分析',
        })

if __name__ == '__main__':
    # 运行后端服务（debug=True仅开发环境用）
    app.run(host='0.0.0.0', port=5000, debug=True)


