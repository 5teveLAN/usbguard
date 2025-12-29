from flask import Flask, render_template_string
import os

app = Flask(__name__)

# 網頁模板：每 2 秒自動重新整理一次
HTML = """
<html>
    <head>
        <title>USB Guard Monitor</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body { background: #121212; color: #00ff00; font-family: monospace; padding: 20px; }
            pre { background: #1e1e1e; padding: 15px; border-radius: 5px; white-space: pre-wrap; }
            h2 { color: #ff0000; border-bottom: 1px solid #333; }
        </style>
    </head>
    <body>
        <h2>🚨 USB Guard Real-time Interception Log</h2>
        <pre>{{ log_content }}</pre>
    </body>
</html>
"""

@app.route('/')
def index():
    log_path = 'intercepted.txt'
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            # 讀取最後 30 行，避免網頁太長
            lines = f.readlines()
            content = "".join(lines[-30:])
    else:
        content = "Waiting for data..."
    return render_template_string(HTML, log_content=content)

if __name__ == '__main__':
    # 讓區網內的所有電腦都能連線 (Pi 的 IP:5000)
    app.run(host='0.0.0.0', port=5000)
