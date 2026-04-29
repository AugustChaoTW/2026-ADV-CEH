# Week 10 — CTF：Operation 竹流入侵

**日期**：2026/05/04–05/10  
**時長**：1 小時  
**延續**：W08 AI 漏洞研究 → W09 Prompt Injection → 本週回到系統層，模擬真實事件的指令注入攻擊

## 一、學習目標

- 理解 Command Injection 的成因與危害（對應 CVE-2026-39808）
- 實際攻擊自製靶機，體驗從「確認 RCE」到「資料洩漏」的完整攻擊鏈
- 理解 Allowlist 防禦策略，並現場驗證其效果

## 二、背景情境

> 2026 年 4 月，新竹物流遭駭客透過 HTTP 請求觸發未授權指令執行（CVE-2026-39808），  
> 系統癱瘓 2 天，物流全面停擺。  
>
> 本週任務：藍隊還原一個「物流查詢系統」，紅隊扮演攻擊者滲透並竊取機敏資料。

## 三、環境（課前先裝好，**不佔課堂時間**）

```bash
pip install flask
```

驗證：

```bash
python3 -c "import flask; print(flask.__version__)"
```

## 四、角色分工

| 角色 | 任務 |
|------|------|
| 藍隊 | 執行 `server.py` 建起靶機，將 IP 告知紅隊 |
| 紅隊 | 透過指令注入找出 4 個 Flag |

## 五、課堂流程（60 分鐘）

| 時間 | 活動 |
|------|------|
| 0:00–0:10 | 老師說明新竹物流事件 + Command Injection 原理 |
| 0:10–0:15 | 藍隊啟動靶機，紅隊讀關卡說明 |
| 0:15–0:45 | **CTF 攻擊時間**：紅隊依序攻 4 個關卡 |
| 0:45–0:55 | **藍隊現場修補**：加上 Allowlist，紅隊嘗試繞過 |
| 0:55–1:00 | 計分 + 複盤：哪個關卡最難？修補後有被繞過嗎？ |

## 六、藍隊：啟動靶機

```bash
python3 server.py
```

靶機跑起來後不得修改程式碼，直到攻擊時間（0:45）結束。

## 七、紅隊：4 個關卡

**攻擊入口**：

```
http://<藍隊IP>:5000/track?id=<payload>
```

| # | 難度 | 目標 | Flag 位置 |
|---|------|------|-----------|
| 🟢 Flag 1 | Easy | 確認 RCE 存在 | 執行 `id`，將完整輸出貼給老師即得分 |
| 🟡 Flag 2 | Medium | 讀取隱藏檔案 | `/tmp/secret.txt` |
| 🟠 Flag 3 | Hard | 洩漏環境變數 | 環境變數 `API_KEY` |
| 🔴 Flag 4 | Expert | 列舉系統使用者 | `/etc/passwd` 第一行完整內容 |

### 提示（真的卡住再看）

<details>
<summary>Flag 1 提示</summary>

`; id` 或 `&& id` 接在單號後面，看看回應有沒有變化。

</details>

<details>
<summary>Flag 2 提示</summary>

能執行 `id`，就能執行 `cat`，想想怎麼把路徑帶進去。

</details>

<details>
<summary>Flag 3 提示</summary>

`printenv` 或 `env` 可以列出所有環境變數。

</details>

<details>
<summary>Flag 4 提示</summary>

`head -1 /etc/passwd` 只讀第一行。

</details>

## 八、第二回合：藍隊現場修補

攻擊時間結束後，藍隊將 `server.py` 中的漏洞函式替換為以下 Allowlist 版本，重啟服務：

```python
import re

@app.route("/track")
def track():
    order_id = request.args.get("id", "")
    if not re.fullmatch(r"\d{1,10}", order_id):
        return "無效單號格式", 400
    result = subprocess.check_output(
        f"echo 查詢單號: {order_id}", shell=True, text=True
    )
    return f"<pre>{result}</pre>"
```

修補完重啟後，紅隊還有 **5 分鐘**嘗試繞過。能繞過者額外加 15 分。

## 九、計分規則

| 項目 | 分數 |
|------|------|
| 🟢 Flag 1 | 25 分 |
| 🟡 Flag 2 | 25 分 |
| 🟠 Flag 3 | 25 分 |
| 🔴 Flag 4 | 25 分 |
| 藍隊修補後成功擋住（每個 Flag）| +10 分 |
| 紅隊找到未預期的 bypass | +15 分 |
