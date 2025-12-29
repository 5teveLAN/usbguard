import os
import subprocess
import re

def get_keyboard_event_path():
    # 1. 找出所有 /dev/input/event* 檔案
    try:
        event_files = [f for f in os.listdir('/dev/input/') if f.startswith('event')]
    except FileNotFoundError:
        return None

    for event in event_files:
        dev_path = f"/dev/input/{event}"
        
        # 2. 使用 udevadm 查詢該裝置屬性
        try:
            # 執行指令並取得輸出
            output = subprocess.check_output(
                ["udevadm", "info", "--query=property", f"--name={dev_path}"],
                text=True
            )
            
            # 3. 檢查是否包含鍵盤標籤
            # 注意：有些裝置會標註 ID_INPUT_KEYBOARD=1，但同時也是 ID_INPUT_MOUSE
            # 我們優先尋找純鍵盤或主要功能為鍵盤的裝置
            if "ID_INPUT_KEYBOARD=1" in output:
                # 排除掉只有多媒體鍵的事件 (選做，增加精確度)
                # 如果該 event 同時有 ID_INPUT_KEYBOARD 和 ID_INPUT_MOUSE，
                # 有時它是 Keychron 的控制介面而非打字介面
                print(f"检测到潜在键盘装置: {dev_path}")
                return dev_path
                
        except subprocess.CalledProcessError:
            continue

    return None

if __name__ == "__main__":
    path = get_keyboard_event_path()
    if path:
        print(f"成功鎖定鍵盤路徑: {path}")
        # run_proxy(path)
    else:
        print("未偵測到任何 HID 鍵盤裝置。")
