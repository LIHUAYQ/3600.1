from apscheduler.schedulers.blocking import BlockingScheduler
from flask import jsonify, Flask, request
from flask_cors import CORS
import os
import base64
import logging
import gj.AITofx as doubao
import gj.getUrl as videoUrl
import gj.docxJob as docx
import gj.sendEmail as emailSend
import gj.dailyJob as daily_job

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources=r'/*')
app.json.ensure_ascii = False

@app.route("/getUrl", methods=["POST"])
def get_rtsp_url():
    print('getUrl')
    ACCESS_TOKEN = "at.49p6sc21c0zvbpl8ac7kl7atb6rbes8a-8l0i61tsq7-0fxihh4-ziauijolv"  # ← 替换为你的accessToken
    DEVICE_SERIAL = "J85851220"  # ← 替换为你的设备序列号
    CHANNEL_NO = 1  # 通常为1
    resp=videoUrl.getUrl(ACCESS_TOKEN,DEVICE_SERIAL,CHANNEL_NO)
    return jsonify({
        "message": "收到POST数据",
        "data": resp["data"]
    }), 200


@app.route('/aitoanalyze', methods=['GET'])
def aitoanalyze():
    print('aitoanalyze')
    screenshot="./static/frontend_screenshot/screenshot.png"
    screenshotWithBboxes='./static/frontend_screenshot/screenshot_with_bboxes.png'
    outPath='./static/frontend_screenshot/'
    md='./static/frontend_screenshot/隐患详情分析.md'
    
    data = doubao.AiToAnalyze(screenshot,outPath)
    docx.todocx('监控一号',screenshotWithBboxes,md,outPath)
    docx.todocx2('监控一号',screenshot,md,outPath)

    # 配置邮箱信息
    smtp_server = 'smtp.qq.com'  # 邮件服务器（QQ邮箱示例，其他邮箱替换为对应SMTP地址）
    smtp_port = 465  # SSL加密端口（大多数邮箱通用）
    sender = '3379810020@qq.com'  # 发送者邮箱
    password = 'owqsgilkatlycibi'  # 邮箱SMTP授权码（非登录密码）
    receiver = '3379810020@qq.com'  # 收件人邮箱（多个用列表：['a@xx.com', 'b@xx.com']）
    emailSend.sendWithDocx(smtp_server,smtp_port,sender,password,receiver,['static/frontend_screenshot/监控一号文档报告.docx','static/frontend_screenshot/监控一号问题报告.docx'])
    try:
        return jsonify({
            "message": "收到分析数据",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({
            "message": "数据接收失败",
            "data": ""
        }), 500


@app.route('/hello', methods=['GET'])
def holle():
    try:
        return jsonify({
            'code': 200,
            'msg': '交互成功',
            'data': '你好'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': '交互失败',
            'data': 'bye'
        })

@app.route('/save-screenshot', methods=['POST'])
def save_screenshot_base64():
    try:
        # 1. 接收前端传递的JSON数据
        data = request.get_json()
        base64_str = data.get('image_base64')  # 获取Base64字符串
        custom_filename = data.get('filename')  # 获取自定义文件名（可选）

        # 2. 验证Base64格式（必须包含data:image前缀）
        if not base64_str or not base64_str.startswith('data:image/'):
            return jsonify({'code': 400, 'msg': '无效的Base64图片格式'})

        # 3. 提取Base64核心数据（去掉前缀：data:image/png;base64,）
        base64_data = base64_str.split(',')[1]

        # 4. 解码Base64为二进制数据
        image_bytes = base64.b64decode(base64_data)

        # 5. 生成保存文件名
        filename = custom_filename
        # 6. 保存图片到指定目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        subfolder = "frontend_screenshot"
        static = "static"
        if not os.path.exists(os.path.join(script_dir, static, subfolder)):
            os.makedirs(os.path.join(script_dir, static, subfolder))  # 新建子文件夹
        save_path = os.path.join(script_dir, static, subfolder, filename)
        with open(save_path, 'wb') as f:  # 'wb'=二进制写入模式
            f.write(image_bytes)

        # 7. 返回成功响应（包含保存路径）
        return jsonify({
            'code': 200,
            'msg': '图片保存成功',
            'data': {
                'save_path': save_path,
                'filename': filename
            }
        })

    except Exception as e:
        # 捕获异常（如Base64解码失败、文件写入错误）
        return jsonify({'code': 500, 'msg': f'保存失败：{str(e)}'})

# def daily_job():
#     print('我是定时')

workIdsList={}
scheduler = BlockingScheduler()
@app.route('/findtime',methods=['GET'])
def findtime():
    print("findtime")
    return jsonify({'code': 200, 'msg': '查看成功','data':workIdsList})


@app.route('/deltime',methods=['GET'])
def deltime():
    print('deltime')
    workId = request.args.get('workid')
    print(workId)
    if scheduler.get_job(workId):
        scheduler.remove_job(workId)
        print('成功移除旧任务')
        workIdsList.pop(workId)
        return jsonify({'code': 200, 'msg': '删除成功'})

@app.route('/settime',methods=['GET'])
def setTime():
    # 添加任务：每天 9:30 执行（用 CRON 表达式）
    # 语法：minute, hour, day, month, day_of_week（* 表示任意）
    try:
        HH=request.args.get('HH')
        mm=request.args.get('mm')
        time=HH+":"+mm
        workId=request.args.get('workid')
        print(time)
        print(workId)
        scheduler.add_job(
            daily_job.task1,
            'cron',
            hour=HH,  # 小时（0-23）
            minute=mm,# 分钟（0-59）
            id=workId,
            replace_existing=True  # 防止重复添加
        )
        workIdsList[workId]=time
        print(workIdsList)
        scheduler.start()
        return jsonify({'code': 200, 'msg': '设置成功'})

    except Exception as e:
        return jsonify({'code': 500, 'msg': f'设置失败：{str(e)}'})
if __name__ == '__main__':
    # 运行后端服务（debug=True仅开发环境用）
    app.run(host='0.0.0.0', port=5000, debug=True)
