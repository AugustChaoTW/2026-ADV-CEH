#!/usr/bin/env python3
"""
Week 10 CTF — Operation 竹流入侵
藍隊靶機：刻意保留 Command Injection 漏洞
攻擊時間結束後，依 README 說明換成 Allowlist 版本
"""
import os
import subprocess
from flask import Flask, request

app = Flask(__name__)

# 隱藏旗標（藍隊啟動時自動建立，不可手動修改）
os.environ["API_KEY"] = "FLAG{env_api_key_leaked}"

with open("/tmp/secret.txt", "w") as f:
    f.write("FLAG{filter_bypass_win}\n")


@app.route("/")
def index():
    return """
    <h2>竹流物流查詢系統</h2>
    <form action="/track">
        <label>輸入貨單號碼：</label>
        <input name="id" placeholder="例：1234567890">
        <button type="submit">查詢</button>
    </form>
    """


@app.route("/track")
def track():
    order_id = request.args.get("id", "")
    # 漏洞在這裡：直接將使用者輸入拼接進 shell 指令
    result = subprocess.check_output(
        f"echo 查詢單號: {order_id}", shell=True, text=True
    )
    return f"<pre>{result}</pre>"


if __name__ == "__main__":
    print("[*] 竹流靶機已啟動：http://0.0.0.0:5000")
    print("[*] Flag 2 已寫入 /tmp/secret.txt")
    print("[*] Flag 3 已設定至環境變數 API_KEY")
    app.run(host="0.0.0.0", port=5000, debug=False)
