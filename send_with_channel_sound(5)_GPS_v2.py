import time
from datetime import datetime
import meshtastic
import meshtastic.serial_interface
import winsound  # 用於播放提示音

# 基本設定參數
COM_PORT = "COM3"             # ← 請根據實際連接的 COM port 修改
CHANNEL_INDEX = 2             # 傳送訊息使用的 Meshtastic 頻道 index（通常為 0~7）
INTERVAL = 600                 # 每隔幾秒傳送一次訊息
BASE_MESSAGE = "Hello"        # 傳送的固定訊息內容
RETRY_DELAY = 10              # 裝置連線失敗後，等待幾秒再重試

# 訊息記錄列印用
def log_message(text):
    print(text)

# 播放不同狀態的提示音
def play_sound_success():
    winsound.Beep(1000, 300)  # 成功音：1000 Hz，持續 0.3 秒

def play_sound_gps_missing():
    winsound.Beep(600, 600)   # GPS 無座標音：600 Hz，持續 0.6 秒

def play_sound_error():
    winsound.Beep(400, 700)   # 錯誤音：400 Hz，持續 0.7 秒

# 從裝置取得節點資訊與 GPS 狀態
def get_info(interface):
    try:
        my_info = interface.getMyNodeInfo()  # 取得本地節點資訊
        node_num = my_info.get('num', 'UnknownNode')  # 節點編號
        position = my_info.get('position', {})
        sats = position.get('sats', '?')               # 可見衛星數
        lat = position.get('latitude', '?')            # 緯度
        lon = position.get('longitude', '?')           # 經度
        alt = position.get('altitude', '?')            # 高度（公尺）
        return node_num, sats, lat, lon, alt
    except Exception as e:
        log_message(f"⚠ 無法取得節點資訊：{e}")
        return 'UnknownNode', '?', '?', '?', '?'

# 傳送訊息函式
def send_message(interface):
    node_id, sats, lat, lon, alt = get_info(interface)
    now = datetime.now().strftime("%H:%M:%S")  # 當前時間（時:分:秒）
    msg = f"[{now}] {node_id} | {BASE_MESSAGE} | GPS: {lat}, {lon}, Alt: {alt}m"
    log_message(f"📡 傳送中：{msg}")
    interface.sendText(msg, channelIndex=CHANNEL_INDEX)  # 實際傳送訊息

    # 根據 GPS 資訊播放不同提示音
    if lat == '?' or lon == '?':
        play_sound_gps_missing()
    else:
        play_sound_success()

# 建立與 Meshtastic 裝置的連線
def connect():
    while True:
        try:
            log_message("🔌 嘗試連接 Meshtastic 裝置...")
            interface = meshtastic.serial_interface.SerialInterface(devPath=COM_PORT)
            log_message("✅ 已成功連接！")
            return interface
        except Exception as e:
            log_message(f"❗ 連線失敗：{e}")
            log_message(f"🔁 {RETRY_DELAY} 秒後重試...")
            play_sound_error()
            time.sleep(RETRY_DELAY)

# 主程式進入點
if __name__ == "__main__":
    interface = connect()

    while True:
        try:
            send_message(interface)
            time.sleep(INTERVAL)
        except Exception as e:
            log_message(f"❌ 傳送或連線錯誤：{e}")
            log_message("🔄 嘗試重新連接裝置...")
            play_sound_error()
            interface = connect()
