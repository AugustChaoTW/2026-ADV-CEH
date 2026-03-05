# 進階駭客攻防 0220 notes（Week 02）

本日主題：用 NGINX 架設簡單檔案下載站，讓藍隊提供題目檔案；紅隊從網站取得檔案並在本機執行分析（picoCTF 練習題）。

---

## 1. [runme.py](https://play.picoctf.org/practice/challenge/250)

### 目標
- **藍方**：在自己的 VM/主機上架 NGINX，並把 `runme.py` 放到網站根目錄，提供可下載連結給紅方。
- **紅方**：用 `wget` 把 `runme.py` 下載下來並用 Python 執行。

---

### 藍方（Blue Team）

#### A. 安裝並啟動 NGINX

> 如果你已經在 root shell，就不需要 `sudo`。

1. 更新套件索引並安裝 nginx
```bash
sudo apt update
sudo apt install -y nginx
```

2. 啟動 nginx，並設定開機自動啟動（建議）
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

3. 確認 nginx 狀態
```bash
sudo systemctl status nginx --no-pager
```

4. 用瀏覽器測試
- 在藍方機器上打開瀏覽器，進入：
  - `http://localhost`
- 若看到 NGINX 預設頁面，代表服務成功。

---

#### B. 下載題目檔案 `runme.py` 並放到網站目錄

NGINX 預設網站根目錄通常在：
- `/var/www/html`

1. 進入網站根目錄
```bash
cd /var/www/html
```

2. 下載題目檔案
```bash
sudo wget -O runme.py https://artifacts.picoctf.net/c/34/runme.py
```

3. 設定檔案權限（讓 nginx 可讀）
```bash
sudo chmod 644 runme.py
```

4. 確認檔案存在
```bash
ls -la /var/www/html/runme.py
```

---

#### C. 建立下載連結（修改 index.html）

你可以用以下任一編輯器（選一個你習慣的）：
```bash
sudo mousepad /var/www/html/index.html
# or
sudo nano /var/www/html/index.html
# or
sudo vi /var/www/html/index.html
```

在 `index.html` 裡加入連結，例如：
```html
<a href="runme.py">runme.py</a>
```

也可以用更完整的範例（可選）：
```html
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Week02 Files</title></head>
  <body>
    <h1>Week02</h1>
    <ul>
      <li><a href="runme.py">runme.py</a></li>
    </ul>
  </body>
</html>
```

---

#### D. 驗證紅方可以下載

1. 在藍方本機用 curl 測試
```bash
curl -I http://localhost/runme.py
```

理想狀態應看到 `HTTP/1.1 200 OK`。

2. 若紅方在同一個區網/Host-only/橋接網路，紅方需要用你的藍方 IP 連線。先查藍方 IP：
```bash
ip a
```

找到像 `10.x.x.x` / `192.168.x.x` 的位址。

---

#### E. 提供給紅方的資訊（很重要）

把以下資訊提供給紅方：
- **檔案 URL**：`http://<藍方IP>/runme.py`

例如（你原本的例子）：
- `http://10.0.2.15/runme.py`

---

#### 常見問題排查
- 防火牆擋 80 port：
  - 確認 80 port 有在 listen：
    ```bash
    sudo ss -lntp | grep :80
    ```
- 檔案權限錯誤導致 403：
  - 確認 `runme.py` 權限至少可讀（644）

---

### 紅方（Red Team）

#### A. 下載檔案
把 `<藍方IP>` 換成藍方提供的位址：

```bash
wget http://<藍方IP>/runme.py
```

或想指定檔名：
```bash
wget -O runme.py http://<藍方IP>/runme.py
```

確認下載成功：
```bash
ls -la runme.py
```

---

#### B. 執行程式
```bash
python3 runme.py
```

如果題目需要互動或有輸入提示，依照輸出操作即可。

---

## 2. [patchme.py](https://play.picoctf.org/practice/challenge/287)

### 目標
- **藍方**：架好 nginx，提供 `patchme.flag.py` 與 `flag.txt.enc` 下載。
- **紅方**：把檔案下載下來，分析 `patchme.flag.py` 的邏輯，並搭配 `flag.txt.enc` 還原 flag（依題目設計而定）。

---

### 藍方（Blue Team）

#### A. 安裝與啟動 NGINX
若第 1 題已完成，這段可以略過。

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

#### B. 下載並放置檔案到 `/var/www/html`

進入網站根目錄：
```bash
cd /var/www/html
```

下載兩個檔案：

1) `patchme.flag.py`
```bash
sudo wget -O patchme.flag.py https://artifacts.picoctf.net/c/201/patchme.flag.py
```

2) `flag.txt.enc`
```bash
sudo wget -O flag.txt.enc https://artifacts.picoctf.net/c/201/flag.txt.enc
```

設定權限：
```bash
sudo chmod 644 patchme.flag.py flag.txt.enc
```

確認檔案存在：
```bash
ls -la /var/www/html/patchme.flag.py /var/www/html/flag.txt.enc
```

---

#### C. 更新 `index.html` 加上連結（建議）

在 `index.html` 加入：
```html
<ul>
  <li><a href="patchme.flag.py">patchme.flag.py</a></li>
  <li><a href="flag.txt.enc">flag.txt.enc</a></li>
</ul>
```

---

#### D. 提供給紅方的資訊

把以下 URL 給紅方：
- `http://<藍方IP>/patchme.flag.py`
- `http://<藍方IP>/flag.txt.enc`

---

### 紅方（Red Team）

> 課堂備註：本題先跳過，留待下次課或回家練習。

（若要做）
1. 下載兩個檔案
```bash
wget http://<藍方IP>/patchme.flag.py
wget http://<藍方IP>/flag.txt.enc
```

2. 閱讀程式邏輯
```bash
less patchme.flag.py
```

3. 依程式流程嘗試執行或修改（題目通常需要 patch 其中某段邏輯）
```bash
python3 patchme.flag.py
```

---

## 課堂小結
- NGINX 預設網站路徑常見為 `/var/www/html`
- 藍方重點：檔案放對位置、權限可讀、提供正確 URL（含 IP）
- 紅方重點：能用 `wget` 成功取得檔案並在本機測試/分析
