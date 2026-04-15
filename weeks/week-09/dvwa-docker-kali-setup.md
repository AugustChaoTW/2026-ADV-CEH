# 實驗：在 Kali Linux 中使用 Docker 建立 DVWA 靶機

**課程：** 進階駭客攻防技術 Week 09  
**難度：** ⭐⭐☆☆☆  
**預估時間：** 30–45 分鐘  
**環境：** Kali Linux（VirtualBox VM）

> ⚠️ **免責聲明：** DVWA 是充滿已知漏洞的練習平台，**僅限在隔離的虛擬機內使用**，請勿將其暴露於任何可公開存取的網路環境。

---

## 一、DVWA 是什麼？

**DVWA（Damn Vulnerable Web Application）** 是一個故意設計有漏洞的 PHP/MySQL Web 應用程式，廣泛用於資安教育與滲透測試練習。

### 涵蓋的漏洞模組

| 漏洞類型 | 說明 |
|---------|------|
| Brute Force | 帳號密碼暴力破解 |
| Command Injection | 命令注入 |
| CSRF | 跨站請求偽造 |
| File Inclusion | 本地/遠端檔案包含（LFI/RFI） |
| File Upload | 惡意檔案上傳 |
| Insecure CAPTCHA | 驗證碼繞過 |
| SQL Injection | SQL 注入 |
| SQL Injection (Blind) | 盲注 |
| Weak Session IDs | 弱 Session 識別碼 |
| XSS (DOM) | 基於 DOM 的跨站腳本 |
| XSS (Reflected) | 反射型 XSS |
| XSS (Stored) | 儲存型 XSS |
| CSP Bypass | 內容安全政策繞過 |
| JavaScript | JS 客戶端攻擊 |

### 難度等級

```
Low    → 無任何防護，直接練習攻擊技巧
Medium → 部分防護，需要繞過簡單過濾
High   → 強化防護，需要更進階的技術
```

---

## 二、環境需求

| 項目 | 需求 |
|------|------|
| 作業系統 | Kali Linux（VirtualBox VM） |
| 記憶體 | 建議 2 GB 以上 |
| 磁碟空間 | 至少 5 GB 可用空間 |
| 網路模式 | **NAT 或 Host-Only**（勿使用 Bridged） |
| Docker | 需先安裝（步驟見下方） |

---

## 三、安裝 Docker

### 步驟 1：更新套件列表

```bash
sudo apt update
```

### 步驟 2：安裝 Docker

```bash
sudo apt install -y docker.io
```

### 步驟 3：啟動 Docker 服務並設定開機自動啟動

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### 步驟 4：將目前使用者加入 docker 群組（避免每次都要 sudo）

```bash
sudo usermod -aG docker $USER
```

> ⚠️ 執行完畢後需**登出再重新登入**，群組變更才會生效。

### 步驟 5：驗證 Docker 安裝成功

```bash
docker --version
```

預期輸出（版本號可能不同）：
```
Docker version 27.x.x, build xxxxxxx
```

---

## 四、拉取並啟動 DVWA 容器

### 步驟 6：拉取 DVWA Docker 映像檔

```bash
docker pull vulnerables/web-dvwa
```

拉取過程會顯示各層下載進度，首次需要數分鐘。

### 步驟 7：啟動 DVWA 容器

```bash
docker run --rm -it -p 80:80 vulnerables/web-dvwa
```

**參數說明：**

| 參數 | 說明 |
|------|------|
| `--rm` | 容器停止後自動刪除（保持環境乾淨） |
| `-it` | 互動模式，顯示容器內部輸出 |
| `-p 80:80` | 將主機的 80 埠對應到容器的 80 埠 |
| `vulnerables/web-dvwa` | 使用的 Docker 映像檔 |

成功啟動後終端機會顯示類似：
```
[+] Starting MySQL...  [  OK  ]
[+] Starting Apache2... [  OK  ]
```

> 💡 **若 80 埠已被佔用**，可改用其他埠號：
> ```bash
> docker run --rm -it -p 8080:80 vulnerables/web-dvwa
> ```
> 之後請將以下所有 `http://localhost` 改為 `http://localhost:8080`

---

## 五、初始化 DVWA

### 步驟 8：開啟瀏覽器連線

在 Kali Linux 中開啟 Firefox，網址列輸入：

```
http://localhost/setup.php
```

### 步驟 9：建立資料庫

點擊頁面底部的 **「Create / Reset Database」** 按鈕。

DVWA 會自動建立所需的資料表並填入預設資料。

成功後頁面會顯示：
```
Setup successful!
```
並自動跳轉至登入頁面。

### 步驟 10：登入 DVWA

| 欄位 | 值 |
|------|-----|
| **Username** | `admin` |
| **Password** | `password` |

---

## 六、設定安全等級

登入後，在左側選單找到 **「DVWA Security」**：

```
DVWA Security → Security Level → 選擇 Low → Submit
```

**建議學習順序：**
1. `Low` → 直接理解漏洞原理
2. `Medium` → 嘗試繞過簡單過濾
3. `High` → 挑戰進階技術

---

## 七、網路架構確認

### VirtualBox 網路模式建議

```
┌─────────────────────────────────┐
│   VirtualBox VM（Kali Linux）    │
│                                  │
│  ┌─────────────────────────────┐ │
│  │  Docker Container (DVWA)    │ │
│  │  172.17.0.x : 80            │ │
│  └────────────┬────────────────┘ │
│               │ port mapping      │
│  localhost:80 ←→ container:80     │
└───────────────┼─────────────────┘
                │ NAT
         Host 電腦（不直接存取）
```

> 🔒 使用 **NAT 模式**：VM 只能對外存取網路，Host 無法直接連入 VM，最為安全。  
> 🔒 使用 **Host-Only 模式**：VM 與 Host 形成隔離內網，Host 可存取 VM，適合需要從 Host 操作的場景。  
> ❌ 避免使用 **Bridged 模式**：VM 會直接暴露在實體網路中。

---

## 八、常見問題排除

### Q1：80 埠衝突

**症狀：** `docker run` 出現 `bind: address already in use`

**解法：**
```bash
# 查看佔用 80 埠的程序
sudo lsof -i :80

# 或直接改用 8080 埠
docker run --rm -it -p 8080:80 vulnerables/web-dvwa
```

---

### Q2：Docker 指令需要 sudo

**症狀：** `permission denied while trying to connect to the Docker daemon socket`

**解法：**
```bash
# 確認已加入 docker 群組
groups $USER

# 若沒有 docker，重新執行
sudo usermod -aG docker $USER

# 重新登入後驗證
newgrp docker
```

---

### Q3：`Create / Reset Database` 失敗

**症狀：** 頁面顯示資料庫連線錯誤

**解法：**
```bash
# 停止容器（Ctrl+C），重新啟動
docker run --rm -it -p 80:80 vulnerables/web-dvwa

# 等待終端機顯示 MySQL 和 Apache 都啟動後再操作瀏覽器
```

---

### Q4：無法存取 http://localhost

**症狀：** 瀏覽器顯示無法連線

**確認清單：**
```bash
# 確認容器正在執行
docker ps

# 確認 80 埠正在監聽
ss -tlnp | grep :80

# 若使用 8080
ss -tlnp | grep :8080
```

---

## 九、後台管理：常用 Docker 指令

```bash
# 查看執行中的容器
docker ps

# 查看所有容器（含已停止）
docker ps -a

# 停止容器（CONTAINER_ID 從 docker ps 取得）
docker stop <CONTAINER_ID>

# 進入容器內部 shell（debug 用途）
docker exec -it <CONTAINER_ID> /bin/bash

# 查看容器 log
docker logs <CONTAINER_ID>

# 清除所有已停止的容器
docker container prune
```

---

## 十、練習任務

完成環境建置後，請嘗試以下練習：

### 任務 1：SQL Injection（基礎）

1. 進入 **SQL Injection** 模組（安全等級：Low）
2. 在 User ID 欄位輸入以下 Payload，觀察結果：
   ```sql
   1' OR '1'='1
   ```
3. 嘗試取得資料庫中所有使用者的資料

### 任務 2：Command Injection

1. 進入 **Command Injection** 模組（安全等級：Low）
2. 嘗試在 IP 欄位注入系統指令：
   ```bash
   127.0.0.1 && whoami
   127.0.0.1 && cat /etc/passwd
   ```

### 任務 3：XSS Reflected

1. 進入 **XSS (Reflected)** 模組（安全等級：Low）
2. 在輸入欄位注入以下 Payload：
   ```html
   <script>alert('XSS')</script>
   ```
3. 嘗試進階 Payload 繞過 Medium 等級的過濾

### 任務 4：Brute Force

1. 進入 **Brute Force** 模組
2. 使用 Burp Suite 或 Hydra 嘗試破解登入表單
3. 目標：找出 `gordonb` 帳號的密碼

---

## 十一、DVWA 預設帳號清單

| 使用者名稱 | 密碼 |
|-----------|------|
| admin | password |
| gordonb | abc123 |
| 1337 | charley |
| pablo | letmein |
| smithy | password |

---

## 參考資料

- [Docker Hub: vulnerables/web-dvwa](https://hub.docker.com/r/vulnerables/web-dvwa)
- [DVWA 官方 GitHub (digininja/DVWA)](https://github.com/digininja/DVWA)
- [How to set up the DVWA on Kali with Docker — Cybr](https://cybr.com/cybersecurity-fundamentals-archives/how-to-set-up-the-dvwa-on-kali-with-docker/)
- [DVWA Lab Setup In Linux (Kali) — GeeksforGeeks](https://www.geeksforgeeks.org/ethical-hacking/dvwa-lab-setup-in-linux-kali/)
- [DVWA Installation Using Docker — Medium](https://medium.com/@abhinsubej/dvwa-installation-using-docker-step-by-step-guide-79d3b31e88b5)
- [Deploy a Local Hacker Lab Using DVWA and Kali Linux — Medium](https://aniveshmohan.medium.com/part-1-deploy-a-local-hacker-lab-using-dvwa-and-kali-linux-90289f30d645)
