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

使用我們創建的代理腳本：

```bash
# 啟動代理（監聽 8081 端口）
python3 /tmp/opencode-proxy.py &
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

            # 2. 轉換 messages 格式
            parts = []
            for msg in messages:
                content = msg.get("content", "")
                if isinstance(content, str):
                    parts.append({"type": "text", "text": content})

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

            # 6. 提取回應文字
            all_text = []
            for part in result.get("parts", []):
                part_type = part.get("type", "")
                if part_type == "text":
                    text = part.get("text", "")
                    if text:
                        all_text.append(text)
                elif part_type == "reasoning":
                    text = part.get("text", "")
                    if text:
                        all_text.append(f"[Reasoning] {text}")
                elif part_type == "tool-result":
                    text = part.get("result", {}).get("text", "")
                    if text:
                        all_text.append(text)

            response_text = "\n".join(all_text)

            # 確保有內容
            if not response_text or not response_text.strip():
                response_text = result.get("info", {}).get("summary", {}).get("text", "Done")

            if not response_text:
                response_text = "Completed"

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
| `messages[].content` | `parts[].text` | 訊息內容格式 |
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

## 相關文件

- 代理腳本：`/tmp/opencode-proxy.py`
- OpenCode 位置：`/home/fychao/.opencode/`
- 認證方式：HTTP Basic Auth（用戶名：opencode）
