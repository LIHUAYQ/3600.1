import subprocess


def capture_hls_frame(hls_url, output_path):
    """
    从指定HLS流截取一帧并保存
    :param hls_url: 你的HLS直播流地址
    :param output_path: 图片保存路径（如snapshot.jpg）
    """
    # ffmpeg命令：适配HLS协议，无多余参数，避免报错
    cmd = [
        "ffmpeg",
        "-i", hls_url,  # 输入你的HLS流地址
        "-vframes", "1",  # 仅截取1帧画面
        "-y",  # 覆盖已存在的同名图片
        "-timeout", "15000000",  # 15秒超时，防止网络卡顿时程序卡死
        output_path
    ]

    try:
        # 执行命令并捕获输出
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,  # 隐藏正常输出
            stderr=subprocess.PIPE,  # 捕获错误信息
            text=True  # 输出转为字符串，便于阅读
        )
        # 判断执行结果
        if result.returncode == 0:
            print(f"✅ 帧截取成功！已保存到：{output_path}")
        else:
            print(f"❌ 截取失败，错误信息：{result.stderr}")
    except Exception as e:
        print(f"❌ 程序执行出错：{str(e)}")