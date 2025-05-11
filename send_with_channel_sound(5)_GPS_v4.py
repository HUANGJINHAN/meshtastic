import time
from datetime import datetime
import meshtastic
import meshtastic.serial_interface
import winsound  # 用於播放不同狀態的提示音

# ========= 使用者可調整的設定 =========
COM_PORT = "COM3"                 # ← 請修改為實際 Meshtastic 裝置的 COM 埠
CHANNEL_INDEX = 2                 # 傳送訊息的頻道 index（通常為 0~7）
INTERVAL = 30                     # 每隔幾秒傳送一次訊息
BASE_MESSAGE = "Hello"            # 傳送的固定訊息內容
RETRY_DELAY = 10                  # 裝置連接失敗後的重試間隔（秒）
MAX_SEND_RETRIES = 3              # 單次訊息最多重送次數
RETRY_SEND_INTERVAL = 2           # 傳送失敗時每次重試間隔秒數

# ========= 工具函式區 =========

# 顯示日誌訊息（可擴充為寫入檔案）
def log_message(text):
    print(text)

# 成功傳送提示音
def play_sound_success():
    winsound.Beep(1000, 300)  # 頻率 1000Hz，持續 0.3 秒

# GPS 資訊缺失提示音
def play_sound_gps_missing():
    winsound.Beep(600, 600)   # 頻率 600Hz，持續 0.6 秒

# 發生錯誤提示音
def play_sound_error():
    winsound.Beep(400, 700)   # 頻率 400Hz，持續 0.7 秒

# 取得節點與 GPS 資訊
def get_info(interface):
    try:
        my_info = interface.getMyNodeInfo()  # 從 Meshtastic 裝置取得節點資訊
        node_num = my_info.get('num', 'UnknownNode')  # 節點編號
        position = my_info.get('position', {})        # 位置資訊（dict）
        sats = position.get('sats', '?')              # 可見衛星數
        lat = position.get('latitude', '?')           # 緯度
        lon = position.get('longitude', '?')          # 經度
        alt = position.get('altitude', '?')           # 高度（公尺）
        return node_num, sats, lat, lon, alt
    except Exception as e:
        log_message(f"⚠ 無法取得節點資訊：{e}")
        return 'UnknownNode', '?', '?', '?', '?'

# 新增：封包接收回呼函式
def on_receive(packet, interface):
    from_node = packet.get("from", "unknown")
    decoded = packet.get("decoded", {})
    payload = decoded.get("text", "(無內容)")
    log_message(f"📥 來自 {from_node} 的封包：{payload}")


# 傳送訊息（包含重送機制）
def send_message(interface):
    node_id, sats, lat, lon, alt = get_info(interface)
    now = datetime.now().strftime("%H:%M:%S")  # 當前時間
    msg = f"[{now}] {node_id} | {BASE_MESSAGE} | GPS: {lat}, {lon}, Alt: {alt}m"

    # 嘗試傳送，最多重試 MAX_SEND_RETRIES 次
    for attempt in range(1, MAX_SEND_RETRIES + 1):
        try:
            log_message(f"📡 傳送中（第 {attempt} 次）：{msg}")
            interface.sendText(msg, channelIndex=CHANNEL_INDEX)

            # 根據 GPS 資訊是否完整，播放不同音效
            if lat == '?' or lon == '?':
                play_sound_gps_missing()
            else:
                play_sound_success()
            break  # 傳送成功，跳出重試
        except Exception as e:
            log_message(f"❌ 傳送失敗：{e}")
            if attempt < MAX_SEND_RETRIES:
                log_message(f"⏳ {RETRY_SEND_INTERVAL} 秒後重試...")
                time.sleep(RETRY_SEND_INTERVAL)
            else:
                log_message("🚫 達到最大重試次數，放棄此訊息。")
                play_sound_error()

# 建立與裝置連線，並註冊 onReceive 回呼
def connect():
    while True:
        try:
            log_message("🔌 嘗試連接 Meshtastic 裝置...")
            interface = meshtastic.serial_interface.SerialInterface(devPath=COM_PORT)

            # 註冊封包接收事件
            interface.onReceive = on_receive

            log_message("✅ 已成功連接！")
            return interface
        except Exception as e:
            log_message(f"❗ 連線失敗：{e}")
            log_message(f"🔁 {RETRY_DELAY} 秒後重試...")
            play_sound_error()
            time.sleep(RETRY_DELAY)

# ========= 主程式執行區 =========
if __name__ == "__main__":
    interface = connect()

    while True:
        try:
            send_message(interface)
            time.sleep(INTERVAL)
        except Exception as e:
            log_message(f"💥 執行錯誤：{e}")
            log_message("🔄 嘗試重新連接裝置...")
            play_sound_error()
            interface = connect()