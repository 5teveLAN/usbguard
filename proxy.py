import sys
import os
import evdev
from evdev import ecodes
import time
import struct
from evdev.util import list_devices
import signal
from datetime import datetime
# 1. 建立鍵碼轉換表 (部分常用鍵)
# evdev scancode -> HID Usage ID
KEY_MAP = {
    ecodes.KEY_A: 0x04, ecodes.KEY_B: 0x05, ecodes.KEY_C: 0x06, ecodes.KEY_D: 0x07,
    ecodes.KEY_E: 0x08, ecodes.KEY_F: 0x09, ecodes.KEY_G: 0x0a, ecodes.KEY_H: 0x0b,
    ecodes.KEY_I: 0x0c, ecodes.KEY_J: 0x0d, ecodes.KEY_K: 0x0e, ecodes.KEY_L: 0x0f,
    ecodes.KEY_M: 0x10, ecodes.KEY_N: 0x11, ecodes.KEY_O: 0x12, ecodes.KEY_P: 0x13,
    ecodes.KEY_Q: 0x14, ecodes.KEY_R: 0x15, ecodes.KEY_S: 0x16, ecodes.KEY_T: 0x17,
    ecodes.KEY_U: 0x18, ecodes.KEY_V: 0x19, ecodes.KEY_W: 0x1a, ecodes.KEY_X: 0x1b,
    ecodes.KEY_Y: 0x1c, ecodes.KEY_Z: 0x1d, ecodes.KEY_1: 0x1e, ecodes.KEY_2: 0x1f,
    ecodes.KEY_3: 0x20, ecodes.KEY_4: 0x21, ecodes.KEY_5: 0x22, ecodes.KEY_6: 0x23,
    ecodes.KEY_7: 0x24, ecodes.KEY_8: 0x25, ecodes.KEY_9: 0x26, ecodes.KEY_0: 0x27,
    ecodes.KEY_ENTER: 0x28, ecodes.KEY_ESC: 0x29, ecodes.KEY_BACKSPACE: 0x2a,
    ecodes.KEY_TAB: 0x2b, ecodes.KEY_SPACE: 0x2c, ecodes.KEY_MINUS: 0x2d,
    ecodes.KEY_EQUAL: 0x2e, ecodes.KEY_LEFTBRACE: 0x2f, ecodes.KEY_RIGHTBRACE: 0x30,
    ecodes.KEY_BACKSLASH: 0x31, ecodes.KEY_SEMICOLON: 0x33, ecodes.KEY_APOSTROPHE: 0x34,
    ecodes.KEY_GRAVE: 0x35, ecodes.KEY_COMMA: 0x36, ecodes.KEY_DOT: 0x37, ecodes.KEY_SLASH: 0x38,
    ecodes.KEY_CAPSLOCK: 0x39,
}

# 修飾鍵 (Modifier keys)
MODIFIER_MAP = {
    ecodes.KEY_LEFTCTRL: 0x01, ecodes.KEY_LEFTSHIFT: 0x02,
    ecodes.KEY_LEFTALT: 0x04, ecodes.KEY_LEFTMETA: 0x08,
    ecodes.KEY_RIGHTCTRL: 0x10, ecodes.KEY_RIGHTSHIFT: 0x20,
    ecodes.KEY_RIGHTALT: 0x40, ecodes.KEY_RIGHTMETA: 0x80,
}
# Linux Scancode 轉人類文字的簡化對照表 (evdev scancode)
# 這是 evdev 的 Scancode (Linux 核心標準)
SC_TO_TEXT = {
    1: "ESC", 2: "1", 3: "2", 4: "3", 5: "4", 6: "5", 7: "6", 8: "7", 9: "8", 10: "9", 11: "0",
    12: "-", 13: "=", 14: "BACKSPACE", 15: "TAB",
    16: "Q", 17: "W", 18: "E", 19: "R", 20: "T", 21: "Y", 22: "U", 23: "I", 24: "O", 25: "P",
    26: "[", 27: "]", 28: "ENTER", 29: "L-CTRL",
    30: "A", 31: "S", 32: "D", 33: "F", 34: "G", 35: "H", 36: "J", 37: "K", 38: "L", 39: ";",
    40: "'", 41: "`", 42: "L-SHIFT", 43: "\\",
    44: "Z", 45: "X", 46: "C", 47: "V", 48: "B", 49: "N", 50: "M", 51: ",", 52: ".", 53: "/",
    54: "R-SHIFT", 56: "L-ALT", 57: "SPACE", 125: "L-GUI(Win)"
}
def log_blocked_event(data):
    if data.keystate == 1:  # Key Press
        sc = data.scancode
        key_name = SC_TO_TEXT.get(sc, f"<{sc}>")
        
        with open("intercepted.txt", "a", encoding="utf-8") as f:
            if len(key_name) == 1:
                # 字母或數字直接印
                f.write(key_name)
            else:
                # 功能鍵加括號，方便肉眼過濾
                f.write(f"[{key_name}]")
HID_G_PATH = '/dev/hidg0'

def write_hid_report(modifier, keys):
    """ 寫入 8 byte 的 HID Report """
    # 格式: [modifier, reserved, key1, key2, key3, key4, key5, key6]
    report = bytearray(8)
    report[0] = modifier
    for i, key in enumerate(keys[:6]):
        report[i+2] = key
    
    with open(HID_G_PATH, 'wb') as fd:
        fd.write(report)
import threading
import time
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas

# --- 1. 全域狀態管理 ---
system_status = {
    "state": "SAFE",   # SAFE, ATTACK, SCANNING
    "msg": "READY",
    "last_update": 0
}

# --- 2. OLED 專屬背景線程 ---
def oled_thread_worker():
    serial = i2c(port=1, address=0x3c)
    device = sh1106(serial)
    
    while True:
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            
            if system_status["state"] == "ATTACK":
                draw.text((10, 10), "🚨 !! ATTACK !!", fill="white")
                draw.text((10, 35), f"SPD: {system_status['msg']}s", fill="white")
                draw.text((10, 50), "BLOCKING...", fill="white")
            elif system_status["state"] == "SCANNING":
                draw.text((10, 25), "🔍 SCANNING USB...", fill="white")
            else:
                draw.text((20, 20), "🛡️ SYSTEM SAFE", fill="white")
                draw.text((20, 45), "MONITORING...", fill="white")
        
        # 這裡的 sleep 很重要，不要讓它 100% 佔用 CPU，每秒更新 2 次就很流暢了
        time.sleep(0.5)

# --- 3. 啟動線程 ---
t = threading.Thread(target=oled_thread_worker, daemon=True)
t.start()

def run_proxy(device_path):
    dev = evdev.InputDevice(device_path)
    dev.grab() 

    last_time = 0
    active_keys = set()
    active_modifiers = 0
    
    is_blocked = False       # 是否處於攔截模式
    block_start_time = 0     # 開始攔截的時間
    system_status["state"] = "SAFE"
    
    print(f"🔥 防禦代理啟動！正在監聽: {dev.name}")
    print(f"🛡️ 攔截到的異常字元將存入: intercepted.txt")

    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            data = evdev.categorize(event)
            current_time = time.time()
            
            # --- 1. 速度監測邏輯 ---
            if data.keystate == 1: # 按下
                delta = current_time - last_time if last_time != 0 else 999
                
                if delta < 0.015 and not is_blocked:
                    system_status["state"] = "ATTACK" # 只要改這個，OLED 就會自動變色
                    system_status["msg"] = f"{delta:.4f}"
                    print(f"🚨 偵測到 BadUSB！啟動攔截...")
                    is_blocked = True
                    force_release_all() # 斷開 T490 的連接
                    
                    # 補救措施：把剛才漏掉的第一個字（M）補進 log 裡
                    if last_scancode is not None:
                        prev_key = SC_TO_TEXT.get(last_scancode, f"<{last_scancode}>")
                        now = datetime.now()
                        formatted_time = now.strftime("%m/%d %H:%M:%S")
                        with open("intercepted.txt", "a") as f:
                            f.write(f"\n[TIME:{formatted_time} ]: {prev_key}")
                    # 同時，當前這個觸發異常的字（I）也會在後面的 is_blocked 邏輯被記進去
                
                last_time = current_time
                last_scancode = data.scancode # 紀錄這一次的 code，留給下次如果異常時補記

            # --- 2. 攔截記錄邏輯 ---
            if is_blocked:
                # 即使被攔截，我們也要記錄它按了什麼
                if data.keystate == 1: # 僅記錄按下的瞬間
                    log_blocked_event(data)
                continue # 💡 重要：被鎖定時跳過後面的轉發邏輯

            # --- 3. 正常轉發邏輯 ---
            if data.scancode in MODIFIER_MAP:
                modifier_bit = MODIFIER_MAP[data.scancode]
                if data.keystate == 1:
                    active_modifiers |= modifier_bit
                elif data.keystate == 0:
                    active_modifiers &= ~modifier_bit
            elif data.scancode in KEY_MAP:
                hid_key = KEY_MAP[data.scancode]
                if data.keystate == 1:
                    active_keys.add(hid_key)
                elif data.keystate == 0:
                    if hid_key in active_keys:
                        active_keys.remove(hid_key)

            # 更新輸出到電腦
            write_hid_report(active_modifiers, list(active_keys))


from findKeyboard import get_keyboard_event_path

def force_release_all():
    """ 強制發送一個全 0 報告，釋放所有電腦上的按鍵 """
    print("\n🧹 正在清理 HID 狀態，釋放所有按鍵...")
    write_hid_report(0, [])

# --- 處理 Ctrl+C 退出程式的情況 ---
def signal_handler(sig, frame):
    force_release_all()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    # 請填入你一開始 ls 到的那個鍵盤裝置路徑
    while (True):    
        path=None
        while (path==None):
            print("Finding keyboard...")
            path=get_keyboard_event_path()
            time.sleep(1)
        print("Keyboard path:", path)

        try:
            run_proxy(path)
        except (OSError, FileNotFoundError):
            print("Keyboard disconnect:")





