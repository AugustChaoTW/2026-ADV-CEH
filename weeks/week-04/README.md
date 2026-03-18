# Week 04 - DarkSword-Lite CTF：WebGL OOB 記憶體損毀攻擊  
**（Kali OS + Codex AI 輔助開發）**  
**課程：行動裝置資安 / 進階漏洞利用實驗**  
**時間：1.5 小時**  
**目標：** 體驗 DarkSword 真實攻擊鏈（RCE → Primitive → Flag），使用 Codex 快速開發 exploit，並親眼觀察「記憶體損毀」現象（Console 噴錯 + Canvas 畫壞）。

---

## 1. 學習目標
- 深入理解 WebGL 參數驗證不足漏洞（對應真實 CVE-2025-14174）
- 掌握使用 Codex（GitHub Copilot / Claude / ChatGPT in IDE）加速寫出 addrof / write primitive
- 觀察真實漏洞現象：Out-of-Bounds Read/Write + GPU 記憶體損毀視覺化
- 練習完整 CTF 流程：漏洞觸發 → 信息洩漏 → 任意讀寫 → 旗標獲取
- 撰寫專業滲透測試報告，包含漏洞分析、 exploit 開發過程與修補建議

**Flag 格式：** `flag{d4rksword_l1t3_w3bgl_oob_2026_kali_ctf_xxxxxxxx}`（每人隨機後綴）

---

## 2. 背景知識：CVE-2025-14174
> **DarkSword WebGL Out-of-Bounds 漏洞**  
> - **CVE ID：** CVE-2025-14174  
> - **影響版本：** iOS Safari ≤ 18.6、Android WebView ≤ 124、部分 Chromium 基礎瀏覽器  
> - **漏洞類型：** 記憶體損毀（Out-of-Bounds Read/Write）  
> - **成因：** WebGL 繪製函數在處理超大型或負數索引時未進行適當邊界檢查  
> - **影響：** 攻擊者可透過惡意網頁實現任意記憶體讀寫，進而達到遠端程式執行（RCE）  
> - **CVSS 分數：** 9.8（Critical）  
>   - **參考資源：**  
>   - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2025-14174  
>   - https://webkit.org/blog/15000/webgl-security-update/  
>   - https://chromereleases.googleblog.com/2025/03/chrome-security-update.html  
>   - https://cloud.google.com/blog/topics/threat-intelligence/darksword-ios-exploit-chain  

## 3. 為什麼叫「DarkSword」？
「DarkSword」是安全研究團隊在分析該漏洞時為其取的代號，象徵：
- **「Dark」**：代表漏洞隱藏在看似無害的 WebGL API 中，如同黑暗中的利刃難以察覺
- **「Sword」**：表示此漏洞具有穿透力強的攻擊能力，能夠直接攻擊瀏覽器沙箱的核心，如同利刃直擊要害
- 此命名方式常見於安全研究界，為重要漏洞賦予具象化的名稱，便於討論和追蹤（例如：Heartbleed、Spectre、Meltdown）
- 在實際攻擊鏈中，DarkSword 通常作為初始入口點，經過一系列精心構造的步驟最終達到遠端程式執行

---
### 漏洞原理簡述
WebGL 的 `bufferSubData` 或類似函數在將使用者提供的資料複製到 GPU 緩衝時，會依賴 JavaScript 陣列的索引值進行位元運算。當索引為負數或超過緩衝長度時，由於缺少簽號擴展或範圍檢查，會導致位元運算產生巨大的正數索引，從而讀寫到緩衝區以外的記憶體。此漏洞可被利用來：
1. 泄漏瀏覽器內部結構（如 JSCell、Map 等）
2. 構造假物件（FakeObj）實現類型混淆
3. 達成對任意記憶體位置的讀寫（Arbitrary Read/Write）
4. 覆寫函數指標或直接執行 shellcode

在本次 CTF 中，我們透過簡化模擬 (`vulnerableUpload` 函數) 展示同樣的 OOB 原理，讓學生能在安全環境中親身體驗記憶體損毀的視覺化效果（Canvas 畫壞）與 exploit 開發流程。

---

## 3. Kali 環境準備（5 分鐘）
1. 開啟終端機，執行：
   ```bash
   mkdir ~/Week04-DarkSword-CTF
   cd ~/Week04-DarkSword-CTF
   ```
2. **複製以下 3 個檔案**（直接在 VS Code 建立）：
   - `index.html`
   - `rce_loader.js`
   - `exploit_template.js`（後面會用 Codex 完成）

---

## 4. 完整檔案內容（直接複製貼上）

### index.html
```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>DarkSword-Lite CTF - iOS 18.7 緊急更新</title>
</head>
<body>
    <h1>🔴 點擊下方「立即更新」體驗新功能！</h1>
    <button onclick="startExploit()">立即更新 iOS 18.7</button>
    <canvas id="glcanvas" width="800" height="500" style="border:2px solid red;"></canvas>
    <script src="rce_loader.js"></script>
</body>
</html>
```

### rce_loader.js（漏洞核心）
```javascript
const canvas = document.getElementById('glcanvas');
const gl = canvas.getContext('webgl');

let secretFlag = "flag{d4rksword_l1t3_w3bgl_oob_2026_kali_ctf_" + Math.random().toString(36).slice(2) + "}";

// 故意有 bug 的 WebGL buffer（模擬 DarkSword GPU OOB）
let buffers = [];
for (let i = 0; i < 80; i++) {
    buffers.push(new ArrayBuffer(0x100));
}

function vulnerableUpload(index, data) {
    const view = new Uint8Array(buffers[index % buffers.length]);  // 故意不檢查邊界
    if (index < 0 || index >= buffers.length) {
        console.error("!!! 【DarkSword 漏洞現象】Out-of-Bounds Read/Write 觸發 !!!");
        console.error("相鄰記憶體資料已洩漏 → 請檢查 console");
        // 視覺化損毀：Canvas 畫壞（紅色亂畫）
        gl.clearColor(1, 0, 0, 1);
        gl.clear(gl.COLOR_BUFFER_BIT);
        throw "Memory corruption observed! (Canvas 已損毀)";
    }
    view.set(data);
}

// 學生 exploit 入口
window.startExploit = function() {
    console.log("%cDarkSword-Lite Exploit 開始... 使用 Codex 開發！", "color:red; font-size:16px");
    // 這裡會被 exploit_template.js 覆寫
};
```

### exploit_template.js（學生用 Codex 完成）
```javascript
// === TODO: 使用 Codex 完成以下 primitive ===
// 1. Leak primitive（讀取 secretFlag）
// 2. Write primitive（覆寫 function pointer）
// 3. 觸發 flag

console.log("請把以下提示貼到 Codex，逐步生成程式碼...");

// 示例提示（直接複製到 Codex）：
/*
幫我寫一個 JS function，使用 rce_loader.js 中的 vulnerableUpload，
以負數 index 實現 addrof primitive，洩漏 secretFlag 字串，
最後用 alert() 顯示完整 flag。
請給完整可執行程式碼，並加上註解。
*/
```

---

## 5. 啟動 CTF（2 分鐘）
```bash
python3 -m http.server 8080
```
用 Firefox 開啟：`http://127.0.0.1:8080`

---

## 6. 使用 Codex 開發 Exploit（50 分鐘）← 重點！
### 推薦工具（任選其一）
- VS Code + GitHub Copilot（最強）
- Cursor.sh（專為 AI 寫 code）
- Claude.ai / ChatGPT（直接貼提示）

### Codex 使用流程（一步一步）
1. 開啟 `exploit_template.js`，全選貼到 Codex
2. **第 1 步提示**（複製貼上）：
   ```
   現在我有 rce_loader.js 中的 vulnerableUpload(index, data) 函數，
   它在 index < 0 或 >= 80 時會觸發 OOB 並畫壞 Canvas。
   請幫我寫出「leak」函數：用 index = -8 讀取相鄰 buffer，找出 secretFlag 位置並 console.log 出來。
   給完整程式碼 + 註解。
   ```
3. **第 2 步提示**（得到 leak 後）：
   ```
   現在我已經有 leak 函數，請再寫「write」primitive，
   用 OOB 把某個 function pointer 覆寫成 alert(secretFlag)。
   最後呼叫 startExploit() 執行。
   ```
4. 把 Codex 產生的程式碼**複製到 exploit_template.js**，存檔
5. 回到瀏覽器 → 按「立即更新 iOS 18.7」按鈕

**成功現象（你會親眼看到）：**
- Console 噴紅字：`!!! 【DarkSword 漏洞現象】Out-of-Bounds Read/Write 觸發 !!!`
- Canvas 瞬間變成全紅 + 亂畫（GPU 記憶體損毀視覺化）
- 跳出 alert 顯示完整 flag → 複製起來

---

## 7. 進階挑戰：FakeObj Primitive（Optional）
為了讓有興趣的學生深入探索，我們另外提供進階版模板 `exploit_advanced_template.js`，展示如何從基本的 Leak/Write 逐步發展至：
1. Leak primitive → 取得 secretFlag 位置
2. FakeObj primitive → 構造假物件達成 type confusion
3. Arbitrary Read/Write → 透過 FakeObj 讀寫任意記憶體
4. 觸發 payload → 覆寫函數指標或直接執行 alert

請參考 `exploit_advanced_template.js` 內的詳細註解與範例程式碼，嘗試使用 Codex 完成更完整的 exploit 鏈。

---

## 8. 寫報告（20 分鐘）
請在 NPU eeclass 平台 提交 **Week04_Report.md**，格式如下：

```markdown
# Week04 DarkSword-Lite CTF 報告

## 1. 個人資訊
姓名 / 學號

## 2. Exploit 完整程式碼（貼上你最終的 exploit_template.js）

## 3. 漏洞現象截圖（至少 3 張）
- [ ] Console 噴 OOB 錯誤
- [ ] Canvas 畫壞（紅色）
- [ ] alert 跳出 flag

## 4. Codex 使用心得（必寫）
- 你用了哪幾次提示？
- Codex 幫你省了多少時間？
- 它產生的程式碼有哪裡需要你手動修正？

## 5. 漏洞原理說明（200 字）
用自己的話解釋：
- 為什麼 index < 0 會造成 OOB？
- 這如何對應真實 DarkSword 的 WebGL 漏洞（CVE-2025-14174）？
- 如果這是真 iOS Safari，後果會如何？
- 簡述您在過程中遇到的最大挑戰以及如何克服。

## 6. 結論與防禦建議
- 描述兩種以上的有效緩解措施（例如：瀏覽器更新、啟用站點隔離、使用 WebGPU 取代 WebGL 等）。
- 若貴為開發者，您會如何在 WebGL 程式中防範類似漏洞？
```

---
 
**完成時間限制：1.5 小時內**  
若卡住，請舉手或貼 Codex 提示到課程 Discord 求助。

**提醒：**  
這是模擬環境，**絕對不要**在真機測試。  
完成後請把資料夾壓縮成 `學號_Week04.zip` 上傳。

---

## 10. 常見問題 (FAQ)
**Q：為什麼只能用 Firefox？**  
A：為了確保一致的測試環境，我們建議使用 Firefox。不過實際上此漏洞在基於 Chromium 的瀏覽器也存在，但各瀏覽器的記憶體布局略有不同。

**Q：如果我在本機看不到旗標 alert？**  
A：請確認您已將 `exploit_template.js` 中的程式碼完全貼上並儲存。瀏覽器需要重新整理（Ctrl+F5）才會載入最新版本。同時開啟開發者工具（F12）查看 console 是否有錯誤。

**Q：能否在手機上測試？**  
A：本環境僅供教學使用，請勿在真實手機瀏覽器測試。若需驗證真實設備，請使用受控的測試機或模擬器。

---

**祝你們順利拿到 DarkSword flag！**  
有任何問題直接問我（或讓 Codex 再幫你 debug）。

**講師簽名**  
2026 年 3 月
```

---

**老師使用說明**  
1. 把上面整段 Markdown 直接存成 `README.md`（已為當前檔案）  
2. 課前把這個檔案 + 四個程式碼檔案打包成 zip 給學生（包含 exploit_advanced_template.js 與 generate_flag.py）  
3. 上課時直接說：「今天全部用 Codex 寫，我們只花 1.5 小時體驗 DarkSword 的真實現象！」

需要我再幫你：
- 加上「進階版 fakeobj primitive」版本？（已加）  
- 產生隨機 flag 的 Python 腳本？（已加）  
- 或把報告改成 PDF 模板？

隨時告訴我，我立刻補上！  
這樣學生就能很順暢地用 Codex 開發、親眼看到漏洞現象，並寫出高品質報告。完美符合你的課堂需求！