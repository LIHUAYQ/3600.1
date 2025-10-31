import os
import base64
import cv2
import json
from volcenginesdkarkruntime import Ark
import re
from PIL import ImageFont, ImageDraw, Image
import numpy as np
import random
def AiToAnalyze(imgPath="./static/frontend_screenshot/screenshot.png",outPath='./static/frontend_screenshot/'):
    # 在 import 区域下方补充：
    SEP_PATTERN = r'^\s*===\s*分隔线\s*===\s*$'

    def split_four_parts(text: str):
        """将模型回复按 '=== 分隔线 ===' 切成四段并做基本清洗。"""
        # 统一换行与空白
        t = text.replace('\r\n', '\n').replace('\u00A0', ' ').strip()
        # 按独立成行的分隔线拆分，最多拆成 4 段
        parts = re.split(SEP_PATTERN, t, maxsplit=3, flags=re.MULTILINE)
        # 兜底：长度不足 4 段时补空串并报错提示（可按需改成 raise）
        if len(parts) < 4:
            parts = (parts + ["", "", "", ""])[:4]
            print("[WARN] 未检测到完整的四段输出，请检查提示词或模型回复格式。")
        return [p.strip() for p in parts[:4]]

    # 配置参数
    # DEFAULT_MODEL = "doubao-seed-1-6-vision-250815"  # 替换为实际的模型ID
    # DEFAULT_MODEL = "ep-20250909143705-sg8sb"  # 替换为实际的模型ID
    DEFAULT_MODEL = "doubao-seed-1-6-flash-250828"  # 替换为实际的模型ID

    IMAGE_PATH =imgPath  # 待检测的图像路径（需确保该路径下有此图片）

    PROMPT = """
    你是一名施工安全检测专家。请基于输入的施工现场图片完成检测，并**严格**遵循下列输出规范。

    【总体结构（必须四段，且用分隔符隔开）】
    第一部分：隐患检测 JSON（仅 JSON 数组）
    === 分隔线 ===
    第二部分：隐患汇总表
    === 分隔线 ===
    第三部分：隐患详情分析
    === 分隔线 ===
    第四部分：安全建议

    【第一部分：隐患检测 JSON（关键，严格按下述规则）】
    1) 仅输出一个合法的 JSON 数组，不得出现任何额外文字、注释、解释、代码围栏```。
    2) 每个对象字段：
       - "category"：从下列**固定枚举**中选择（与程序颜色表一致）：
         ["基坑安全隐患","桩基设备隐患","脚手架安全隐患","起重设备隐患","高空作业隐患",
          "施工用电隐患","设备安全隐患","人员个体防护隐患","材料堆放隐患","环境安全隐患",
          "管理安全隐患","其他隐患"]
       - "bbox"：矩形边界框，字符串格式 "<bbox>x1 y1 x2 y2</bbox>"
         · 坐标一律采用**相对归一化**到 0~1000 的整数（四舍五入）
         · 顺序为 xmin ymin xmax ymax
         · 必须满足 0 ≤ x1 < x2 ≤ 1000，0 ≤ y1 < y2 ≤ 1000
    3) **至少输出 1 条目标**。若不确定，也必须标出最可能的风险点（如"人员个体防护隐患"或"高空作业隐患"等）并给出大致 bbox。
    4) 对同类多个目标分别输出多条；禁止返回空数组 []、"无隐患" 等。

    【JSON 示例（示例无需完全照抄，仅示格式）】
    [{"category":"人员个体防护隐患","bbox":"<bbox>530 637 670 864</bbox>"},
     {"category":"基坑安全隐患","bbox":"<bbox>150 0 450 245</bbox>"}]

    === 分隔线 ===

    【第二部分：隐患汇总表】
    - 以列表或表格形式，包含：隐患类别、隐患位置（文字描述）、风险等级（高/中/低）、数量。
    - 类别名称必须与上方**固定枚举**一致（例如"人员个体防护隐患"，不要写成"个人防护装备隐患"）。

    === 分隔线 ===

    【第三部分：隐患详情分析】
        - 逐条对应规范条款（如《建筑施工安全检查标准》JGJ59-2011、《施工现场临时用电安全技术规范》JGJ46-2005 等）与条款内容要点。
        - 分析该隐患造成的后果与事故机理。
        - 只输出若干个块（至少 1 个），每个块对应 1 条隐患详情。
        - 每个块内必须按以下“固定顺序与固定字段名”逐行输出；每行只放一个字段：

        （从固定枚举中选择）
        隐患位置: （一句话精确描述）
        场景状况: （一句话）
        对应规范: 《规范编号-年份》第x.x.x条：条文要点
        后果分析: （一句话）
        相关案例: （无相关案例则写“无”）


        - 规则：
          1) 字段名必须使用以上 8 个固定关键词之一，且置于行首；冒号可为半角“:”或全角“：”。
          2) 每行一个字段，字段值不得换行；若需列多点，用中文分号“；”在同一行内分隔。
          3) 不得使用表格、项目符号（- 、•）、Markdown 标题、代码块或额外说明文字。
          4) 仅在第三部分输出上述块；块与块之间可以空一行增强可读性。

        【第三部分-正例】
        人员个体防护隐患
        隐患位置: 东侧脚手架底部通道处
        场景状况: 2名作业人员未佩戴安全帽
        对应规范: 《建筑施工安全检查标准-2011》6.2.1条：进入施工现场必须正确佩戴安全帽
        后果分析: 物体打击致伤风险；坠落时头部防护不足
        相关案例: 无

        施工用电隐患
        隐患位置: 配电箱右侧地面
        场景状况: 电缆沿地面明设且有车辆碾压痕迹
        对应规范: 《施工现场临时用电安全技术规范-2024》7.2.1条：电缆应埋地或架空敷设，严禁沿地面明设
        后果分析: 绝缘损伤引发触电与短路起火风险
        相关案例: 无

        【第三部分-反例（禁止）】
        场景状况: 未戴安全帽；对应规范见JGJ59...  ← 多字段挤在一行，错误
         …  之外还有普通段落文字        ← 出现模板外自由文本，错误

    === 分隔线 ===

    【第四部分：安全建议】
    - **严格格式要求**：每个整改措施必须换行，使用规范的Markdown格式
    - 每个大建议标题使用 `### 针对[隐患类别]整改措施`
    - 每个小建议使用 `- [具体措施]` 格式，并且每个小建议单独一行
    - 示例格式：
    ### 针对环境安全隐患整改措施
    - 立即组织人员清理垃圾房内溢出垃圾，分类存放至指定地点
    - 每日下班前检查垃圾房卫生，设置"日产日清"标识
    - 在垃圾房周边设置防火沙箱和灭火器

    ### 针对设备安全隐患整改措施  
    - 规范摆放键盘、显示器等设备，保持操作区域整洁
    - 对办公设备进行定期检查，清理设备表面积尘
    - 划分设备存放区与通道区域，通道宽度不小于0.8米

    【输出合规检查表（在你生成内容前自检）】
    - [ ] 第一部分只有纯 JSON 数组；无任何额外文本/符号/代码围栏。
    - [ ] bbox 坐标均为 0~1000 的**整数**，顺序与不等式关系正确。
    - [ ] 类别严格来自固定枚举；若拿不准，用"其他隐患"或最接近的类别，但不要新造名称。
    - [ ] 至少 1 条检测结果。
    - [ ] 第四部分每个小建议都单独一行，格式规范
    """

    # 读取API密钥
    # api_key = "6d67b8ed-8769-4dfc-85c3-761fe5b82eb2"  # doubao-seed-1-6-flash-250715模型
    api_key = "3702a65f-dfa0-43d7-a023-9f7cbde1fab8"  # doubao-seed-1-6-vision-250815模型
    # api_key = "3702a65f-dfa0-43d7-a023-9f7cbde1fab8"   # doubao-seed-1-6-flash-250828模型

    # 创建Ark客户端
    client = Ark(
        api_key=api_key,
    )  # 初始化模型客户端

    def extract_json_array(text: str) -> str:
        """从返回文本中抽取首个 JSON 数组字符串。"""
        m = re.search(r"```(?:json)?\s*(\[\s*[\s\S]*?\])\s*```", text, re.IGNORECASE)
        if m:
            return m.group(1)

        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == '[':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0 and start != -1:
                    return text[start:i + 1]
        return text.strip()

    def strip_bbox_tags(bbox: str) -> str:
        """去掉<bbox>…</bbox>标签，保留坐标。"""
        s = bbox.strip()
        s = re.sub(r"</?bbox>", "", s, flags=re.IGNORECASE).strip()
        return s

    # 读取图像并转为base64编码
    with open(IMAGE_PATH, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode('utf-8')  # 编码后转字符串

    # 调用模型：发送图像+提示词，获取检测结果
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,  # 指定使用的模型
        messages=[{
            "role": "user",
            "content": [{
                "type": "image_url",  # 图片输入
                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
            }, {
                "type": "text",  # 文本提示
                "text": PROMPT
            }]
        }],
        temperature=0.2,
        top_p=1,
        max_tokens=32768
    )
    bbox_content = response.choices[0].message.content  # 提取模型返回的检测结果
    # ① 先按分隔线拆分
    part1_json_raw, part2_summary, part3_details, part4_advice = split_four_parts(bbox_content)
    # ② 第一段提取纯 JSON 并解析
    # 转成 Python list 对象
    try:
        json_text = extract_json_array(part1_json_raw)  # 兼容 ```json 块 或 纯数组
        objects = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"第一部分不是合法 JSON，请检查：{e}\n片段：{part1_json_raw[:200]}...")

    # ③（可选）把其余三段各自落盘/入库/打印，便于后续处理或展示
    with open(outPath+"隐患汇总表.md", "w", encoding="utf-8") as f:
        f.write(part2_summary)
    with open(outPath+"隐患详情分析.md", "w", encoding="utf-8") as f:
        f.write(part3_details)
    with open(outPath+"安全建议.md", "w", encoding="utf-8") as f:
        f.write(part4_advice)

    image = cv2.imread(IMAGE_PATH)
    if image is None:  # NEW：防止读图失败直接崩
        raise RuntimeError(f"OpenCV读取图片失败，请确认路径：{IMAGE_PATH}")

    # 循环次数 = category 的数量
    for i in range(len(objects)):
        category = objects[i]["category"]
        bbox = objects[i]["bbox"]
        if not bbox:
            print(f"[WARN] 第 {i + 1} 个缺少 bbox，已跳过。")
            continue
        # print(f"第 {i+1} 个：类别={category}, 边界框={bbox}")

        # 大类固定色（BGR）
        rng = random.Random()  # 如需可复现，设置种子：random.Random(1234)

        detected_cats = sorted({obj.get("category", "其他隐患") for obj in objects})
        hues = rng.sample(range(0, 180), k=len(detected_cats))  # 为每类抽一个色相

        category_colors = {}
        for cat, h in zip(detected_cats, hues):
            s, v = 200, 255
            bgr = cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2BGR)[0][0]
            category_colors[cat] = (int(bgr[0]), int(bgr[1]), int(bgr[2]))

        color = category_colors.get(category, (255, 255, 255))  # 默认白色

        coords_str = strip_bbox_tags(bbox)  # CHANGED：去掉<bbox>标签
        coords = list(map(int, coords_str.split()))  # 分割字符串并转为整数
        if len(coords) != 4:  # 验证坐标数量(xmin, ymin, xmax, ymax) 边界框需要4个坐标（左上角x、y，右下角x、y）
            raise ValueError(f"坐标数量不正确，需要4个数值；实际：{coords_str}")
        x_min, y_min, x_max, y_max = coords  # 解包坐标

        # 获取图像尺寸并缩放坐标(模型输出范围为0-1000)
        h, w = image.shape[:2]
        x_min_real = int(x_min * w / 1000)
        y_min_real = int(y_min * h / 1000)
        x_max_real = int(x_max * w / 1000)
        y_max_real = int(y_max * h / 1000)

        # === 半透明填充 + 细边框 + 更小字体 ===
        # 半透明填充（覆盖整块 bbox）
        overlay = image.copy()
        alpha_fill = 0.25  # 透明度：0~1，数值越大越不透明
        cv2.rectangle(
            overlay,
            (x_min_real, y_min_real),
            (x_max_real, y_max_real),
            color,
            -1  # 填充
        )
        image = cv2.addWeighted(overlay, alpha_fill, image, 1 - alpha_fill, 0)

        # 细边框（将粗细改为 1）
        cv2.rectangle(image, (x_min_real, y_min_real), (x_max_real, y_max_real), color, 1)

        # 更小中文字体
        font_size = 10
        font = ImageFont.truetype("./font/simhei.ttf", font_size)
        text = category
        pad = 5

        # 计算中文文本大小，用于标签背景
        try:
            x0, y0, x1, y1 = font.getbbox(text)  # Pillow ≥ 8.0
        except AttributeError:
            _tmp = Image.new("RGB", (1, 1))
            _draw = ImageDraw.Draw(_tmp)
            x0, y0, x1, y1 = _draw.textbbox((0, 0), text, font=font)
        text_width = x1 - x0
        text_height = y1 - y0
        bg_width = text_width + 2 * pad
        bg_height = text_height + 2 * pad

        # 标签背景也做半透明
        overlay2 = image.copy()
        alpha_label = 0.6
        cv2.rectangle(
            overlay2,
            (x_min_real, y_min_real),
            (x_min_real + bg_width, y_min_real + bg_height),
            color,
            -1
        )
        image = cv2.addWeighted(overlay2, alpha_label, image, 1 - alpha_label, 0)

        # 写中文（黑色）到半透明标签上
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        draw.text((x_min_real + pad, y_min_real + pad), text, font=font, fill=(0, 0, 0))
        image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # 保存标注后的图片（在原图文件名后加"_with_bboxes"）
    output_path =os.path.splitext(IMAGE_PATH)[0] + "_with_bboxes.png"

    cv2.imwrite(output_path, image)
    print(f"成功保存标注图片: {output_path}")

    # 返回文本信息
    dataDict = {}
    print(part2_summary.split("\n"))
    if '隐患汇总表' in part2_summary.split("\n")[0]:
        lines=part2_summary.split("\n")
        dataDict['part2_summary']="\n".join(lines[1:])
    else:
        dataDict['part2_summary'] = part2_summary
    if '隐患详情分析' in part3_details.split("\n")[0]:
        lines = part3_details.split("\n")
        dataDict['part3_details'] = "\n".join(lines[1:])
    else:
        dataDict['part3_details'] = part3_details

    dataDict['part4_advice'] = part4_advice
    print(dataDict)
    return dataDict