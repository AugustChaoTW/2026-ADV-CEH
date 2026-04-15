# 安裝手冊：OpenCode Shannon Plugin on Kali Linux

**課程：** 進階駭客攻防技術 Week 09  
**難度：** ⭐⭐⭐☆☆  
**預估時間：** 45–60 分鐘  
**環境：** Kali Linux（VirtualBox VM）

> ⚠️ **法律警告：** Shannon Plugin 是自動化滲透測試工具。請**僅在您擁有或獲得明確書面授權的系統上**進行測試。未授權的測試在多數地區屬於刑事犯罪。

---

## 一、Shannon Plugin 是什麼？

**OpenCode Shannon Plugin** 是一個整合於 [OpenCode](https://opencode.ai) 終端 AI 代理的自動化滲透測試外掛，以 AI 驅動超過 600 種 Kali Linux 工具，完整涵蓋 OWASP Top 10 測試流程。

### 核心能力

| 階段 | 功能 | 使用工具 |
|------|------|---------|
| 偵察（Recon） | 網路掃描、子域名探索、技術指紋識別 | nmap、subfinder、httpx、gowitness |
| 漏洞發現 | SQL 注入、XSS、目錄遍歷 | sqlmap、nikto、nuclei、gobuster、ffuf |
| 瀏覽器測試 | React / Angular / Vue SPA 分析 | Playwright、Chromium、BrowserBruter |
| 漏洞利用 | IDOR、檔案上傳、提權鏈 | 自動化 exploit 框架 |
| 報告產出 | CVE 參照、CVSS 評分、修補建議 | AI 生成 PDF 報告 |

### 支援的 AI 提供商

Anthropic、OpenAI、Google Gemini、GitHub Copilot、Azure OpenAI、Groq、DeepSeek、xAI

---

## 二、前置需求確認

安裝前請確認以下項目均已備妥：

| 需求 | 最低版本 | 確認指令 |
|------|---------|---------|
| Docker | 最新版 | `docker --version` |
| OpenCode | ≥ 1.0.150 | `opencode --version` |
| Bun | ≥ 1.3.9 | `bun --version` |
| Git | 任意版本 | `git --version` |
| Python | ≥ 3.x | `python3 --version` |

> 若尚未安裝 Docker，請先參照 [dvwa-docker-kali-setup.md](./dvwa-docker-kali-setup.md) 的第三章完成 Docker 安裝。

---

## 三、安裝 Bun

Bun 是高效能的 JavaScript 執行環境與套件管理器（比 Node.js/npm 快數倍）。

### 步驟 1：安裝 Bun

```bash
curl -fsSL https://bun.sh/install | bash
```

### 步驟 2：套用環境變數（使 bun 指令立即可用）

```bash
source ~/.bashrc
# 或 zsh 使用者：
source ~/.zshrc
```

### 步驟 3：驗證安裝

```bash
bun --version
```

預期輸出（版本號可能不同）：
```
1.x.x
```

---

## 四、安裝 OpenCode

### 步驟 4：使用官方安裝腳本

```bash
curl -fsSL https://opencode.ai/install | bash
```

### 步驟 5（替代方案）：使用 Bun 安裝

```bash
bun add -g opencode-ai
```

### 步驟 6：驗證 OpenCode 版本

```bash
opencode --version
```

確認版本號 **≥ 1.0.150**，若版本過舊請重新安裝：

```bash
bun add -g opencode-ai@latest
```

---

## 五、設定 OpenCode 的 AI 模型

Shannon Plugin 需要透過 OpenCode 連線至 AI 提供商。

### 步驟 7：啟動 OpenCode 並設定 API 金鑰

```bash
opencode
```

進入終端介面後，輸入：
```
/connect
```

依照提示選擇 AI 提供商並貼上 API 金鑰。

**推薦模型選擇（學術用途）：**

| 用途 | 推薦模型 |
|------|---------|
| 主要代理（Shannon） | `anthropic/claude-opus-4-5` 或 `openai/gpt-4.5-preview` |
| 偵察階段 | `google/gemini-2.0-flash`（速度快、成本低） |
| 漏洞利用 | `anthropic/claude-sonnet-4-5` |
| 報告產出 | `anthropic/claude-sonnet-4-5` |

> 💡 若無 API 金鑰，可使用 OpenCode Zen（內建免費配額）：至 [opencode.ai/auth](https://opencode.ai/auth) 取得認證憑證。

---

## 六、安裝 Shannon Plugin

### 步驟 8：Clone 專案儲存庫

```bash
git clone https://github.com/vichhka-git/opencode-shannon-plugin
cd opencode-shannon-plugin
```

### 步驟 9：安裝 Node.js 相依套件並編譯

```bash
bun install
bun run build
```

編譯完成後會在 `dist/` 目錄產生編譯後的外掛檔案。

### 步驟 10：建立 Docker 工具映像檔

此步驟將所有資安工具打包至 Docker 容器：

```bash
docker build -t shannon-tools .
```

> ⏳ 首次建置需要 10–20 分鐘，映像檔包含 600+ 種資安工具。

建置完成後確認映像檔存在：

```bash
docker images | grep shannon-tools
```

預期輸出：
```
shannon-tools   latest   xxxxxxxxxxxx   x minutes ago   x.xxGB
```

### 步驟 11：執行自動安裝腳本

```bash
./scripts/install-global.sh
```

此腳本會：
1. 自動備份現有的 OpenCode 設定
2. 將 Shannon Plugin 路徑寫入 `~/.config/opencode/opencode.json`
3. 建立預設設定檔

**若腳本為 Python 版本：**

```bash
python3 scripts/install_global.py
```

---

## 七、手動設定（替代方案）

若自動安裝腳本失敗，可手動完成以下步驟。

### 步驟 12：建立 OpenCode 設定目錄

```bash
mkdir -p ~/.config/opencode
```

### 步驟 13：編輯 OpenCode 主設定檔

```bash
nano ~/.config/opencode/opencode.json
```

加入 plugin 路徑（請替換 `<YOUR_PATH>` 為實際路徑）：

```json
{
  "plugin": [
    "/home/<YOUR_USERNAME>/opencode-shannon-plugin/dist/index.js"
  ]
}
```

確認實際路徑：

```bash
pwd
# 在 opencode-shannon-plugin 目錄中執行，取得絕對路徑
```

### 步驟 14：建立 Shannon Plugin 設定檔

```bash
nano ~/.config/opencode/shannon-plugin.json
```

貼入以下內容：

```json
{
  "shannon": {
    "require_authorization": true,
    "docker_image": "shannon-tools",
    "browser_testing": true,
    "idor_testing": true,
    "upload_testing": true
  }
}
```

**設定說明：**

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `require_authorization` | `true` | 測試前要求確認授權（建議保持開啟） |
| `docker_image` | `shannon-tools` | 使用的 Docker 工具映像檔名稱 |
| `browser_testing` | `true` | 啟用 SPA/JavaScript 應用測試 |
| `idor_testing` | `true` | 啟用 IDOR 漏洞自動偵測 |
| `upload_testing` | `true` | 啟用檔案上傳漏洞測試 |

---

## 八、進階設定：多模型配置

可針對不同測試階段指定不同 AI 模型，以平衡效能與成本。

### 高效能配置（適合比賽/深度測試）

```json
{
  "shannon": {
    "require_authorization": true,
    "docker_image": "shannon-tools",
    "agents": {
      "shannon": "anthropic/claude-opus-4-5",
      "recon":   "openai/gpt-4.5-preview",
      "exploit": "anthropic/claude-opus-4-5",
      "report":  "anthropic/claude-opus-4-5"
    }
  }
}
```

### 省成本配置（適合日常練習）

```json
{
  "shannon": {
    "require_authorization": true,
    "docker_image": "shannon-tools",
    "agents": {
      "shannon": "anthropic/claude-sonnet-4-5",
      "recon":   "google/gemini-2.0-flash",
      "exploit": "openai/gpt-4o",
      "report":  "anthropic/claude-sonnet-4-5"
    }
  }
}
```

---

## 九、驗證安裝

### 步驟 15：啟動 OpenCode 並測試外掛

```bash
opencode
```

進入互動介面後，輸入偵察指令：

```
/shannon-recon
```

若 Shannon Plugin 正常載入，系統會詢問目標位址並開始偵察。

### 完整安裝驗證清單

```bash
# 1. 確認 Bun 版本
bun --version

# 2. 確認 OpenCode 版本
opencode --version

# 3. 確認 Docker 映像檔存在
docker images | grep shannon-tools

# 4. 確認設定檔存在
ls -la ~/.config/opencode/
cat ~/.config/opencode/opencode.json
cat ~/.config/opencode/shannon-plugin.json
```

---

## 十、使用方式

### 10.1 基本指令

| 指令 | 說明 |
|------|------|
| `/shannon-scan` | 完整滲透測試（涵蓋全部 OWASP Top 10） |
| `/shannon-recon` | 僅執行偵察階段（安全，不主動攻擊） |
| `/shannon-report` | 產出測試報告（需先完成掃描） |

### 10.2 自然語言操作

在 OpenCode 中直接用文字描述目標：

```
> Scan http://localhost for SQL injection vulnerabilities
> Test http://localhost/dvwa for XSS and CSRF
> Generate a penetration test report for http://localhost
```

### 10.3 搭配 DVWA 練習

以本週建立的 DVWA 環境為目標：

```bash
# 先確認 DVWA 正在執行
docker ps | grep web-dvwa

# 啟動 OpenCode
opencode
```

在 OpenCode 中輸入：

```
> /shannon-recon
Target: http://localhost
```

或：

```
> Scan http://localhost/dvwa for vulnerabilities. I have authorization to test this system.
```

---

## 十一、常見問題排除

### Q1：`bun: command not found`

```bash
# 重新載入環境變數
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
echo 'export BUN_INSTALL="$HOME/.bun"' >> ~/.bashrc
echo 'export PATH="$BUN_INSTALL/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

### Q2：`opencode: command not found`

```bash
# 確認安裝位置
which opencode
ls ~/.local/bin/opencode

# 若在 ~/.local/bin，加入 PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

### Q3：`bun run build` 失敗

```bash
# 清除快取重新安裝
rm -rf node_modules
bun install --frozen-lockfile
bun run build
```

---

### Q4：Docker build 失敗（網路問題）

```bash
# 確認 Docker 服務運作中
sudo systemctl status docker

# 測試 Docker 網路連線
docker run --rm alpine ping -c 1 8.8.8.8

# 若 DNS 問題，設定 Docker DNS
echo '{"dns": ["8.8.8.8", "1.1.1.1"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

---

### Q5：Plugin 未被 OpenCode 載入

```bash
# 確認設定檔格式正確（JSON 語法檢查）
python3 -m json.tool ~/.config/opencode/opencode.json

# 確認外掛檔案存在
ls -la ~/opencode-shannon-plugin/dist/index.js

# 確認路徑在設定檔中正確
cat ~/.config/opencode/opencode.json
```

---

### Q6：`shannon-tools` Docker 映像檔不存在

```bash
# 回到專案目錄重新建置
cd ~/opencode-shannon-plugin
docker build -t shannon-tools .

# 確認建置成功
docker images shannon-tools
```

---

## 十二、目錄結構說明

安裝完成後的相關路徑：

```
~/.config/opencode/
├── opencode.json           ← OpenCode 主設定（含 plugin 路徑）
└── shannon-plugin.json     ← Shannon 功能設定

~/opencode-shannon-plugin/
├── src/                    ← 原始碼
├── dist/
│   └── index.js            ← 編譯後的外掛入口點
├── scripts/
│   ├── install-global.sh   ← 自動安裝腳本
│   └── install_global.py   ← Python 版安裝腳本
├── Dockerfile              ← 工具容器定義
└── docs/
    └── guide/
        └── installation.md ← 官方安裝文件
```

---

## 十三、與 DVWA 整合練習流程

```
[啟動 DVWA]
    docker run --rm -it -p 80:80 vulnerables/web-dvwa
         │
         ▼
[開啟另一個終端，啟動 OpenCode]
    opencode
         │
         ▼
[執行偵察]
    /shannon-recon → Target: http://localhost
         │
         ▼
[執行完整掃描]
    /shannon-scan → Target: http://localhost
         │
         ▼
[產出報告]
    /shannon-report
         │
         ▼
[比對 DVWA 手動攻擊結果]
    分析 AI 找到的漏洞 vs 手動發現的漏洞
```

---

## 參考資料

- [opencode-shannon-plugin — GitHub](https://github.com/vichhka-git/opencode-shannon-plugin)
- [OpenCode 官方文件](https://opencode.ai/docs/)
- [OpenCode 安裝教學 2026 — NxCode](https://www.nxcode.io/resources/news/opencode-install-guide-step-by-step-2026)
- [Bun 安裝文件](https://bun.sh/docs/installation)
- [OpenCode GitHub (anomalyco/opencode)](https://github.com/anomalyco/opencode)
