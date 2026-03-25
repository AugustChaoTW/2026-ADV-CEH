# Big-Pickle for IronClaw

使用 OpenCode 的 big-pickle 模型作為 IronClaw 的 LLM 後端。

## 背景

### 問題

- OpenCode 的免費模型（如 big-pickle）需要通過 OpenCode CLI 調用，無法直接從外部服務（如 IronClaw）調用
- 直接調用 `https://opencode.ai/zen/v1/chat/completions` 會返回 rate limit 錯誤
- IronClaw 使用 OpenAI 相容的 API 格式，而非 OpenCode 的 session 格式

### 解決方案

創建一個代理伺服器，將 IronClaw 的 OpenAI 格式請求轉換為 OpenCode session API 格式。

## 架構

```
┌─────────────┐     OpenAI API      ┌─────────────┐    Session API     ┌─────────────┐
│   IronClaw  │ ──────────────────▶ │   代理伺服器  │ ──────────────────▶ │ OpenCode   │
│             │   /v1/chat/        │ (Python)     │   /session/:id/   │   Server   │
│             │   completions       │               │   message         │             │
│             │ ◀────────────────── │               │ ◀─────────────────│             │
└─────────────┘   OpenAI Response   └─────────────┘   OpenCode Response  └─────────────┘
```

## 安裝步驟

### 1. 啟動 OpenCode 伺服器

OpenCode 伺服器需要密碼認證：

```bash
# 設置密碼並啟動伺服器
OPENCODE_SERVER_PASSWORD=test /home/fychao/.opencode/bin/opencode serve --port=5175
```

預設帳號：`opencode`

### 2. 啟動代理伺服器

```bash
# 啟動代理（監聽 8081 端口）
python3 /home/fychao/opencode-proxy.py &
```

### 3. 配置 IronClaw

```bash
# 設置環境變數
export LLM_BACKEND=openai_compatible
export LLM_BASE_URL=http://localhost:8081/v1
export LLM_MODEL=big-pickle

# 或使用 IronClaw 配置命令
ironclaw config set llm_backend openai_compatible
ironclaw config set openai_compatible_base_url http://localhost:8081/v1
ironclaw config set selected_model big-pickle
```

### 4. 測試

```bash
ironclaw run --no-onboard -m "Say hello"
```

## 代理伺服器設計

### 核心邏輯

代理伺服器需要完成以下任務：

1. **接收 OpenAI 格式請求**
   - 端點：`POST /v1/chat/completions`
   - 格式：JSON，包含 `model` 和 `messages`

2. **轉換為 OpenCode Session 格式**
   - 創建新 session：`POST /session`
   - 發送訊息：`POST /session/:id/message`
   - 需要包含 `model.providerID` 和 `model.modelID`

3. **轉換回 OpenAI 格式**
   - 從 OpenCode 回應中提取文字
   - 格式化為 OpenAI chat completion 格式

### 完整代碼

```python
#!/usr/bin/env python3
"""
OpenAI-to-OpenCode Proxy for big-pickle model
將 OpenAI API 格式轉換為 OpenCode Session API 格式
"""
import json
import urllib.request
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# 配置
OPENCODE_HOST = "localhost"
OPENCODE_PORT = 5175       # OpenCode 伺服器端口
OPENCODE_USER = "opencode" # 認證用戶名
OPENCODE_PASS = "test"     # 認證密碼
PROXY_PORT = 8081         # 代理伺服器端口

class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/v1/chat/completions":
            self.handle_chat_completions()
        else:
            self.send_error(404, "Not found")

    def handle_chat_completions(self):
        """處理 OpenAI chat completions 請求"""
        try:
            # 1. 解析請求
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            messages = data.get("messages", [])
            model = data.get("model", "big-pickle")

            # 2. 轉換 messages 格式 - 支援字串和陣列兩種格式
            # IronClaw 發送陣列格式: [{"type": "text", "text": "..."}]
            parts = []
            for msg in messages:
                content = msg.get("content", "")
                if isinstance(content, str):
                    parts.append({"type": "text", "text": content})
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text = item.get("text", "")
                                if text:
                                    parts.append({"type": "text", "text": text})

            # 3. 設置認證
            auth_encoded = base64.b64encode(
                f"{OPENCODE_USER}:{OPENCODE_PASS}".encode()
            ).decode()

            # 4. 創建 OpenCode session
            req = urllib.request.Request(
                f"http://{OPENCODE_HOST}:{OPENCODE_PORT}/session",
                data=json.dumps({"title": "ironclaw-proxy"}).encode(),
                method="POST"
            )
            req.add_header("Content-Type", "application/json")
            req.add_header("Authorization", f"Basic {auth_encoded}")

            with urllib.request.urlopen(req) as resp:
                session = json.loads(resp.read())

            session_id = session.get("id")

            # 5. 發送訊息到 OpenCode
            msg_req = urllib.request.Request(
                f"http://{OPENCODE_HOST}:{OPENCODE_PORT}/session/{session_id}/message",
                data=json.dumps({
                    "parts": parts,
                    "model": {"providerID": "opencode", "modelID": model}
                }).encode(),
                method="POST"
            )
            msg_req.add_header("Content-Type", "application/json")
            msg_req.add_header("Authorization", f"Basic {auth_encoded}")

            with urllib.request.urlopen(msg_req) as resp:
                result = json.loads(resp.read())

            # 6. 提取回應文字 - 只取 text 類型的 part
            response_text = ""
            for part in result.get("parts", []):
                part_type = part.get("type", "")
                if part_type == "text":
                    text = part.get("text", "")
                    if text and text.strip():
                        response_text = text.strip()
                        break

            # 確保有內容
            if not response_text:
                response_text = "Done"

            # 7. 轉換為 OpenAI 格式
            output = {
                "id": f"chatcmpl-{result.get('info', {}).get('id', 'test')[:8]}",
                "object": "chat.completion",
                "created": result.get("info", {}).get("time", {}).get("created", 0),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text,
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": result.get("info", {}).get("tokens", {}).get("input", 0),
                    "completion_tokens": result.get("info", {}).get("tokens", {}).get("output", 0),
                    "total_tokens": result.get("info", {}).get("tokens", {}).get("total", 0)
                }
            }

            # 8. 返回響應
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(output).encode())

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PROXY_PORT), ProxyHandler)
    print(f"Proxy running on port {PROXY_PORT}")
    print(f"Configure IronClaw:")
    print(f"  LLM_BASE_URL=http://localhost:{PROXY_PORT}/v1")
    print(f"  LLM_MODEL=big-pickle")
    server.serve_forever()
```

### API 對應關係

| OpenAI API | OpenCode API | 說明 |
|------------|--------------|------|
| `POST /v1/chat/completions` | `POST /session` + `POST /session/:id/message` | 創建 session 並發送訊息 |
| `messages[].content` (string) | `parts[].text` | 訊息內容格式 |
| `messages[].content` (array) | `parts[].text` | IronClaw 使用陣列格式 |
| `model` | `model.providerID` + `model.modelID` | 模型指定 |

### OpenCode Session API 詳情

#### 創建 Session
```bash
POST http://localhost:5175/session
Authorization: Basic <base64(opencode:test)>
Content-Type: application/json

{"title": "ironclaw-session"}
```

#### 發送訊息
```bash
POST http://localhost:5175/session/{session_id}/message
Authorization: Basic <base64(opencode:test)>
Content-Type: application/json

{
  "parts": [{"type": "text", "text": "用戶訊息"}],
  "model": {"providerID": "opencode", "modelID": "big-pickle"}
}
```

#### 回應格式
```json
{
  "info": {
    "role": "assistant",
    "modelID": "big-pickle",
    "providerID": "opencode",
    "tokens": {"input": 100, "output": 50, "total": 150}
  },
  "parts": [
    {"type": "reasoning", "text": "思考過程"},
    {"type": "text", "text": "回應內容"}
  ]
}
```

## 代理健康監控

### 問題

在測試過程中，我們發現代理伺服器經常停止響應。可能的原因包括：

1. **Python 進程被終止** - 可能被用戶或系統終止
2. **端口被佔用** - 其他程序佔用了相同端口
3. **OpenCode 伺服器連接失敗** - OpenCode 伺服器未運行或崩潰
4. **網絡問題** - 本地網絡延遲或中斷
5. **異常未被捕獲** - 未處理的異常導致進程崩潰

### 解決方案

#### 1. 使用 Systemd 服務（推薦）

創建系統服務以自動啟動和監控：

```ini
# /etc/systemd/system/opencode-proxy.service
[Unit]
Description=OpenCode to OpenAI Proxy for Big-Pickle
After=network.target

[Service]
Type=simple
User=fychao
WorkingDirectory=/home/fychao
ExecStart=/usr/bin/python3 /home/fychao/opencode-proxy.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 啟用服務
sudo systemctl daemon-reload
sudo systemctl enable opencode-proxy
sudo systemctl start opencode-proxy

# 查看狀態
sudo systemctl status opencode-proxy

# 查看日誌
sudo journalctl -u opencode-proxy -f
```

#### 2. 使用 Health Check 腳本

創建健康檢查腳本：

```bash
#!/bin/bash
# /home/fychao/check-proxy.sh

PROXY_URL="http://localhost:8081/v1/chat/completions"
OPENCODE_URL="http://localhost:5175/global/health"

# 檢查代理是否響應
check_proxy() {
    curl -s -X POST "$PROXY_URL" \
        -H "Content-Type: application/json" \
        -d '{"model": "test", "messages": []}' \
        --connect-timeout 2 \
        --max-time 5 > /dev/null 2>&1
    return $?
}

# 檢查 OpenCode 伺服器是否運行
check_opencode() {
    curl -s "$OPENCODE_URL" --connect-timeout 2 > /dev/null 2>&1
    return $?
}

# 主檢查邏輯
if ! check_proxy; then
    echo "[ERROR] Proxy not responding, restarting..."
    pkill -f opencode-proxy.py
    sleep 2
    cd /home/fychao
    nohup python3 /home/fychao/opencode-proxy.py > /tmp/proxy.log 2>&1 &
    sleep 3
    
    if check_proxy; then
        echo "[OK] Proxy restarted successfully"
    else
        echo "[ERROR] Failed to restart proxy"
    fi
fi

if ! check_opencode; then
    echo "[WARN] OpenCode server not responding"
fi
```

添加到 crontab 每分鐘檢查：

```bash
# crontab -e
* * * * * /home/fychao/check-proxy.sh
```

#### 3. 使用 Docker 容器（最佳方案）

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY opencode-proxy.py .

CMD ["python3", "opencode-proxy.py"]
```

```bash
# 構建和運行
docker build -t opencode-proxy .
docker run -d \
    --name opencode-proxy \
    -p 8081:8081 \
    --network host \
    -e OPENCODE_HOST=host.docker.internal \
    opencode-proxy
```

#### 4. 內建重試機制

在代理中添加自動重試邏輯：

```python
import time

def call_with_retry(func, max_retries=3, delay=1):
    """帶重試的函數調用"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Retry {attempt + 1}/{max_retries}: {e}")
                time.sleep(delay)
            else:
                raise

# 使用示例
def create_session():
    # ... 創建 session 的邏輯
    pass

session = call_with_retry(create_session)
```

### 監控腳本

創建 `/home/fychao/monitor-proxy.sh`：

```bash
#!/bin/bash
# 監控代理和 OpenCode 伺服器

LOG_FILE="/tmp/proxy-monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 檢查端口
check_port() {
    local port=$1
    ss -tlnp 2>/dev/null | grep -q ":$port " && return 0 || return 1
}

# 測試代理
test_proxy() {
    curl -s -X POST "http://localhost:8081/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{"model": "test", "messages": [{"role": "user", "content": "test"}]}' \
        --connect-timeout 3 --max-time 10 > /dev/null 2>&1
    return $?
}

# 測試 OpenCode
test_opencode() {
    curl -s "http://localhost:5175/global/health" \
        --connect-timeout 3 --max-time 5 > /dev/null 2>&1
    return $?
}

# 主邏輯
log "Starting proxy monitor..."

while true; do
    # 檢查 OpenCode
    if ! test_opencode; then
        log "[WARN] OpenCode server not responding"
    fi
    
    # 檢查代理
    if ! test_proxy; then
        log "[ERROR] Proxy not responding, attempting restart..."
        
        # 終止舊進程
        pkill -f "python3.*opencode-proxy" 2>/dev/null
        sleep 2
        
        # 重啟代理
        cd /home/fychao
        nohup python3 /home/fychao/opencode-proxy.py >> /tmp/proxy.log 2>&1 &
        PROXY_PID=$!
        
        sleep 3
        
        if test_proxy; then
            log "[OK] Proxy restarted (PID: $PROXY_PID)"
        else
            log "[ERROR] Failed to restart proxy"
        fi
    fi
    
    sleep 30  # 每 30 秒檢查一次
done
```

### 快速重啟腳本

創建 `/home/fychao/restart-proxy.sh`：

```bash
#!/bin/bash
# 快速重啟代理

echo "Stopping existing proxy..."
pkill -f "python3.*opencode-proxy" 2>/dev/null
sleep 1

echo "Starting proxy..."
cd /home/fychao
nohup python3 /home/fychao/opencode-proxy.py > /tmp/proxy.log 2>&1 &
sleep 2

# 測試
if curl -s -X POST "http://localhost:8081/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "test", "messages": []}' \
    --connect-timeout 5 > /dev/null 2>&1; then
    echo "Proxy is running!"
else
    echo "Proxy failed to start. Check /tmp/proxy.log"
fi
```

## 已知問題

### 1. Session 上下文

每次請求創建一個新的 session，沒有保留上下文。這是簡化版本，完整實現應該：

- 維護 session 池
- 複用 session 進行多輪對話
- 處理 session 過期

### 2. 工具調用

當前版本不支持工具調用（tool calling）。OpenCode 使用 `tool-call` part type，但需要：

- 解析工具調用請求
- 執行工具
- 將結果傳回 OpenCode

### 3. Rate Limit

- OpenCode 的免費模型有 rate limit
- 直接調用 API 會被限制
- 通過 OpenCode CLI 內建的身份驗證可以避免

## 改進建議

### 1. 添加工具支持

```python
# 檢測工具調用
for part in result.get("parts", []):
    if part.get("type") == "tool-call":
        # 執行工具並發送結果
        tool_calls = part.get("tool_calls", [])
        # ... 處理工具調用
```

### 2. Session 池

```python
class SessionPool:
    def __init__(self, max_sessions=10):
        self.sessions = []
        self.max_sessions = max_sessions

    def get_session(self):
        # 返回可用的 session 或創建新的
        pass

    def release_session(self, session_id):
        # 回收 session
        pass
```

### 3. 流式響應

實現 Server-Sent Events (SSE) 進行流式輸出：

```python
def handle_streaming(self, result):
    for part in result.get("parts", []):
        # 逐步發送每個 part
        self.send_chunk(part)
```

## 測試

### 測試代理

```bash
# 直接測試代理
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "big-pickle",
    "messages": [{"role": "user", "content": "Say hi in 3 words"}]
  }'
```

### 測試 IronClaw

```bash
export LLM_BASE_URL=http://localhost:8081/v1
export LLM_MODEL=big-pickle
ironclaw run --no-onboard -m "Hello"
```

### 測試檔案創建

```bash
ironclaw run --no-onboard -m "Create a file called test.txt with content 'hello world'"
ls -la test.txt
```

## 故障排除

### 代理無法啟動

```bash
# 檢查端口是否被佔用
ss -tlnp | grep 8081

# 殺死佔用進程
fuser -k 8081/tcp

# 重新啟動代理
/home/fychao/restart-proxy.sh
```

### IronClaw 顯示 "Done"

這通常意味著代理沒有收到正確的請求。檢查：

1. 代理是否運行：`ps aux | grep opencode-proxy`
2. 端口是否監聽：`ss -tlnp | grep 8081`
3. 日誌是否有錯誤：`cat /tmp/proxy.log`

### Rate Limit 錯誤

如果看到 rate limit 錯誤：

1. 等待一段時間再試
2. 檢查 OpenCode 伺服器是否正常運行
3. 嘗試重啟 OpenCode 伺服器

## 相關文件

- 代理腳本：`/home/fychao/opencode-proxy.py`
- 監控腳本：`/home/fychao/monitor-proxy.sh`
- 重啟腳本：`/home/fychao/restart-proxy.sh`
- OpenCode 位置：`/home/fychao/.opencode/`
- 認證方式：HTTP Basic Auth（用戶名：opencode）
