建立 `/etc/systemd/system/usbguard.service`：
```
[Unit]
Description=USB Guard Proxy and Web Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/ggd
# 先執行 HID 設定，再跑 Python
ExecStartPre=/usr/bin/sudo /home/ggd/setup_hid.sh
# 同時啟動 Web 和 Proxy (假設你寫在同一個啟動腳本或用 nohup)
ExecStart=/home/ggd/venv/bin/python /home/ggd/main_launcher.py
Restart=always

[Install]
WantedBy=multi-user.target
```
### 3. 建立 `main_launcher.py` (整合啟動器)
為了不要開一堆視窗，我們用一個 Python 腳本同時把兩個服務拉起來：
```python
import subprocess
import time
import sys

# 啟動 Web Monitor (背景)
web_proc = subprocess.Popen(["/home/ggd/venv/bin/python", "web_monitor.py"])

# 啟動 Proxy 主程式 (前景)
try:
    proxy_proc = subprocess.run(["/home/ggd/venv/bin/python", "proxy.py"])
except KeyboardInterrupt:
    web_proc.terminate()
    sys.exit(0)
```