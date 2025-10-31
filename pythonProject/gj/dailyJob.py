import os.path
import gj.docxJob as docx
import gj.sendEmail as emailSend
import gj.AITofx as doubao
import gj.LiveToScreenshot as toScreenshot
import gj.getUrl as videoUrl

# 图片保存路径（可自定义，如"./camera_snapshot.jpg"）
IMAGE_PATH = "./static/job_screenshot/screenshot.png"

def task1():
    screenshot='./static/job_screenshot/screenshot.png'
    screenshotWithBboxes='./static/job_screenshot/screenshot_with_bboxes.png'
    jobPath='./static/job_screenshot/'
    md='./static/job_screenshot/隐患详情分析.md'
    print('task1')
    ACCESS_TOKEN = "at.49p6sc21c0zvbpl8ac7kl7atb6rbes8a-8l0i61tsq7-0fxihh4-ziauijolv"  # ← 替换为你的accessToken
    DEVICE_SERIAL = "J85851220"  # ← 替换为你的设备序列号
    CHANNEL_NO = 1  # 通常为1
    resp=videoUrl.getUrl(ACCESS_TOKEN,DEVICE_SERIAL,CHANNEL_NO)["data"]["url"]

    toScreenshot.capture_hls_frame(resp, IMAGE_PATH)

    if(os.path.exists(screenshot)):
        doubao.AiToAnalyze(screenshot, jobPath)
        docx.todocx('监控一号', screenshotWithBboxes,
                    md, jobPath)
        docx.todocx2('监控一号', screenshot,
                    md, jobPath)
        # 配置邮箱信息
        smtp_server = 'smtp.qq.com'  # 邮件服务器（QQ邮箱示例，其他邮箱替换为对应SMTP地址）
        smtp_port = 465  # SSL加密端口（大多数邮箱通用）
        sender = '3379810020@qq.com'  # 发送者邮箱
        password = 'owqsgilkatlycibi'  # 邮箱SMTP授权码（非登录密码）
        receiver = '3379810020@qq.com'  # 收件人邮箱（多个用列表：['a@xx.com', 'b@xx.com']）
        emailSend.sendWithDocx(smtp_server, smtp_port, sender, password, receiver,
                               ['./static/job_screenshot/监控一号文档报告.docx','./static/job_screenshot/监控一号问题报告.docx'])
