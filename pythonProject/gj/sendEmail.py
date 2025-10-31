import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header

def sendWithDocx(smtp_server,smtp_port,sender,password,receiver,filePaths):
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = Header('带 docx 附件的邮件', 'utf-8')  # 邮件主题

    # 添加邮件正文
    text_content = '这是一封包含 docx 附件的测试邮件，请查收！'
    message.attach(MIMEText(text_content, 'plain', 'utf-8'))

    # 添加 docx 附件
    for filePath in filePaths:
        docx_path = filePath  # 替换为你的 docx 文件路径（相对或绝对路径）
        if not os.path.exists(docx_path):
            print(f"错误：文件 {docx_path} 不存在！")
        else:
            with open(docx_path, 'rb') as f:
                # 创建附件对象（MIME类型用application/vnd.openxmlformats-officedocument.wordprocessingml.document更标准）
                part = MIMEBase(
                    'application',
                    'vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                part.set_payload(f.read())  # 读取文件内容

            encoders.encode_base64(part)  # 用base64编码（邮件传输要求）

            # 设置附件文件名（关键：解决中文文件名乱码问题）
            filename = os.path.basename(docx_path)
            # 对文件名进行编码处理（兼容不同邮件客户端）
            part.add_header(
                'Content-Disposition',
                'attachment',
                filename=('utf-8', '', filename)  # 显式指定编码为utf-8
            )
            message.attach(part)  # 将附件添加到邮件

    # 发送邮件
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender, password)
        server.sendmail(sender, [receiver], message.as_string())
        print("邮件发送成功！")
    except smtplib.SMTPException as e:
        print(f"邮件发送失败：{e}")
    finally:
        server.quit()


smtp_server = 'smtp.qq.com'  # 邮件服务器（QQ邮箱示例，其他邮箱替换为对应SMTP地址）
smtp_port = 465  # SSL加密端口（大多数邮箱通用）
sender = '3379810020@qq.com'  # 发送者邮箱
password = 'owqsgilkatlycibi'  # 邮箱SMTP授权码（非登录密码）
receiver = '3379810020@qq.com'  # 收件人邮箱（多个用列表：['a@xx.com', 'b@xx.com']）
