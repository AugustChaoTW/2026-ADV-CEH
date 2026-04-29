#!/usr/bin/env python3
"""
Week 10 CTF — Operation 竹流入侵（完整版）
4 個漏洞對應 4 個 CVE，各藏 1 個 Flag
攻擊時間結束後，依 README 說明逐一修補
"""
import os
import subprocess
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Flag 3：藏在 Flask config，需 SSTI 才能讀到
app.config["SECRET_FLAG"] = "FLAG{ssti_cve_2022_22963}"

# Flag 1：藏在檔案，需 Command Injection 才能讀到
with open("/tmp/flag1.txt", "w") as f:
    f.write("FLAG{cmd_injection_cve_2026_39808}\n")

# Flag 2：藏在檔案系統，需 Path Traversal 才能讀到
PUBLIC_DIR = "/tmp/www_public"
os.makedirs(PUBLIC_DIR, exist_ok=True)
with open(f"{PUBLIC_DIR}/notice.txt", "w") as f:
    f.write("竹流物流公告：系統維護中\n")
with open("/tmp/logistics_db.txt", "w") as f:
    f.write("FLAG{path_traversal_cve_2021_41773}\n")


@app.route("/")
def index():
    return """
    <h2>竹流物流查詢系統</h2>
    <ul>
      <li><b>/track?id=</b>　　貨單查詢</li>
      <li><b>/download?file=</b>　公告下載</li>
      <li><b>/greet?name=</b>　　客戶歡迎頁</li>
      <li><b>/fetch?url=</b>　　物流狀態整合</li>
    </ul>
    """


# ── CVE-2026-39808：Command Injection ────────────────────────────────────────
@app.route("/track")
def track():
    order_id = request.args.get("id", "")
    result = subprocess.run(
        f"echo 查詢單號: {order_id}", shell=True, capture_output=True, text=True
    )
    return f"<pre>{result.stdout}{result.stderr}</pre>"


# ── CVE-2021-41773：Path Traversal ───────────────────────────────────────────
@app.route("/download")
def download():
    filename = request.args.get("file", "notice.txt")
    path = f"{PUBLIC_DIR}/{filename}"
    try:
        with open(path, "r") as f:
            return f"<pre>{f.read()}</pre>"
    except Exception as e:
        return f"<pre>錯誤：{e}</pre>", 400


# ── CVE-2022-22963：SSTI ─────────────────────────────────────────────────────
@app.route("/greet")
def greet():
    name = request.args.get("name", "訪客")
    template = f"<h2>您好，{name}！您的貨件正在處理中。</h2>"
    return render_template_string(template)


# ── CVE-2021-26855：SSRF（Flag 藏在僅限本機的 /admin）────────────────────────
@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")
    try:
        resp = requests.get(url, timeout=3)
        return f"<pre>{resp.text}</pre>"
    except Exception as e:
        return f"<pre>錯誤：{e}</pre>", 400


@app.route("/admin")
def admin():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return "403 Forbidden — 僅限內部存取", 403
    return "<pre>FLAG{ssrf_cve_2021_26855}</pre>"


if __name__ == "__main__":
    print("[*] 竹流靶機已啟動：http://0.0.0.0:5000")
    print("[*] Flag 1 已寫入 /tmp/flag1.txt")
    print("[*] Flag 2 已寫入 /tmp/logistics_db.txt")
    print("[*] Flag 3 已藏入 app.config（需 SSTI 才能讀）")
    print("[*] Flag 4 在 /admin（需 SSRF 才能存取）")
    app.run(host="0.0.0.0", port=5000, debug=False)
