# UAF 練習實驗室

這是一個針對大學資安課程設計的 Use-After-Free 漏洞練習環境。

## 目錄

- [環境需求](#環境需求)
- [練習題目](#練習題目)
- [CTF 挑戰](#ctf-挑戰)
- [快速開始](#快速開始)
- [攻擊方式說明](#攻擊方式說明)
- [防禦方式](#防禦方式)

---

## 環境需求

- Kali Linux（或任何 Linux 發行版）
- GCC 編譯器
- AddressSanitizer (ASan)

```bash
# 驗證環境
gcc --version
```

---

## 練習題目

| 編號 | 名稱 | 難度 | 描述 |
|------|------|------|------|
| uaf_01 | 基本 UAF | ⭐ | 最簡單的 Use-After-Free |
| uaf_02 | Double Free | ⭐ | 多次釋放同一記憶體 |
| uaf_03 | Buffer Overflow | ⭐ | 越界寫入記憶體 |
| uaf_04 | 懸空指標 | ⭐⭐ | 指標超出作用域 |
| uaf_05 | 結構體 UAF | ⭐⭐ | 結構體的 UAF |
| uaf_06 | 正確範例 | - | 安全程式碼示範 |
| uaf_07 | Heap Spray | ⭐⭐⭐ | 記憶體佈局控制 |
| uaf_08 | CTF 挑戰 | ⭐⭐⭐⭐ | 綜合漏洞利用 |

---

## CTF 挑戰

### uaf_08 - 漏洞綜合利用挑戰

**目標**：取得 admin 權限，獲得 FLAG

**FLAG**：`FLAG{U4f_3xp10t_5ucc3ssful}`

### 挑戰功能

```
1. Register new account    - 註冊帳號
2. Login                  - 登入
3. View Profile           - 查看個人資料
4. Admin Panel            - 管理員面板（需要 admin 權限）
5. Delete Account         - 刪除帳號（觸發 UAF）
6. Secret Admin Upgrade   - 秘密管理員升級
7. Debug Info             - 除錯資訊
8. Exit                   - 離開
```

### 攻擊方式

#### 方法一：Buffer Overflow（簡單）

```
1. 選擇 1 (Register)
2. 輸入 username: 超過 32 個字元 (例如 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA)
3. 輸入 password: 任意
4. 選擇 4 (Admin Panel)
5. 取得 FLAG！
```

**原理**：
```
struct User {
    char username[32];   // 0-31
    char password[32];  // 32-63  
    int is_admin;       // 64-67 ← 超過 32 字元會覆蓋這裡
};
```

#### 方法二：Use-After-Free（較難）

```
1. 選擇 1 (Register)         → 註冊帳號
2. 選擇 6 (Admin Upgrade)  → 設定 is_admin = 1
3. 選擇 4 (Admin Panel)    → 確認可見 FLAG
4. 選擇 5 (Delete)          → free 記憶體
5. 選擇 1 (Register)        → 重新註冊
6. 選擇 4 (Admin Panel)    → 再次取得 FLAG！
```

---

## 快速開始

### 編譯所有練習

```bash
cd /home/augchao/uaf_lab
./build_all.sh
```

### 執行 ASan 練習

```bash
# 基本練習（使用 ASan 檢測）
./uaf_01
./uaf_02
# ...
```

### 執行 CTF 挑戰

```bash
# CTF 挑戰（無 ASan，讓漏洞存在）
./uaf_08
```

---

## 攻擊方式說明

### Use-After-Free (UAF)

**定義**：記憶體被 `free()` 釋放後，指標仍被使用

**範例**：
```c
char *ptr = malloc(100);
free(ptr);       // 記憶體已釋放
printf("%s", ptr);  // 錯誤：仍在使用已釋放的記憶體
```

**防禦**：
```c
free(ptr);
ptr = NULL;  // 永遠設為 NULL
```

### Buffer Overflow

**定義**：寫入資料超過緩衝區大小

**範例**：
```c
char buffer[32];
scanf("%s", buffer);  // 無邊界檢查！
```

**防禦**：
```c
scanf("%31s", buffer);  // 限制長度
fgets(buffer, sizeof(buffer), stdin);  // 使用安全函數
```

---

## 檔案結構

```
uaf_lab/
├── README.md                 # 本檔案
├── build_all.sh              # 編譯腳本
├── uaf_01_basic.c           # 練習 1-7 原始碼
├── uaf_02_double_free.c
├── uaf_03_buffer_overflow.c
├── uaf_04_dangling_pointer.c
├── uaf_05_struct.c
├── uaf_06_fixed.c
├── uaf_07_heap_spray.c
├── uaf_08_ctf.c              # CTF 挑戰原始碼
├── uaf_08_hint.md            # CTF 提示
└── solve_ctf.py              # 自動化解題腳本
```

---

## 參考資源

- [AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)
- [how2heap](https://github.com/shellphish/how2heap)
- [CVE-2026-2441](https://nvd.nist.gov/vuln/detail/CVE-2026-2441)
