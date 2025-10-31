import requests

def getUrl(access_token="at.5n0ylpft5o4a9cgc6txldovpb0u82may-1hsmfxehkl-05jabme-airupkbml", device_serial="J85851220", channel_no=1):
    url = "https://open.ys7.com/api/lapp/v2/live/address/get"
    data = {
        "appKey": "39d292f0b8924db19f3d2e76cfede33a",  # ← 替换为你的appKey
        "appSecret": "f8bf15b21c1513b4396c9b4d6e5213da",  # ← 替换为你的appSecret
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "channelNo": channel_no,
        "protocol": "2"
    }
    resp = requests.post(url, data=data).json()
    if resp.get("code") != "200":
        print("❌ 获取失败:", resp)
        return None

    rtmp_url = resp["data"]["url"]
    print("✅ RTMP 地址获取成功:", rtmp_url)
    return resp
