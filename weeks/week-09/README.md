# 進階駭客攻防 Week 09 

**日期：** 2026/04/20 – 04/26  
**主題：** AI 驅動的漏洞研究新紀元：Claude Mythos Preview 與玻璃翼計畫

[TOC]

---

## 一、背景：AI 資安能力的臨界點

2026 年 4 月 8 日，Anthropic 正式發布 **Claude Mythos Preview**——一個在網路安全領域展現出史無前例能力的前沿 AI 模型。  
與此同時，Anthropic 宣布了限制存取計畫 **Project Glasswing（玻璃翼計畫）**，以確保此模型僅用於防禦目的。

這兩件事標誌著一個轉折點：**AI 已能自主發現並利用零日漏洞（Zero-Day Vulnerabilities）**，資安攻防格局從此改變。

---

## 二、Claude Mythos Preview

### 2.1 模型概覽

| 項目 | 內容 |
|------|------|
| **發布日期** | 2026 年 4 月 8 日 |
| **代號** | Capybara |
| **命名意義** | Mythos（希臘語）：將知識與思想深度連結的故事與神話脈絡 |
| **存取方式** | 限制存取（不公開，僅透過 Project Glasswing） |
| **Token 定價** | 輸入 $25 / 輸出 $125（每百萬 tokens，Preview 後） |

### 2.2 綜合性能指標

| 基準測試 | Mythos Preview | Claude Opus 4.6 |
|---------|---------------|-----------------|
| SWE-bench Verified | **93.9%** | — |
| SWE-bench Pro | **77.8%** | — |
| USAMO（數學奧林匹克） | **97.6%** | — |
| CyberGym 資安基準 | **83.1%** | 66.6% |

### 2.3 資安攻擊能力（紅隊評估）

#### CTF（Capture The Flag）表現

依據英國 AI 安全研究所（AISI）的評估：

```
難度等級：Technical Non-Expert → Expert
Expert 級任務成功率：73%（歷史上無模型能完成的等級）
```

- 在所有難度層級的 CTF 挑戰中均有顯著提升
- 首個能解決「Expert 級」CTF 的 AI 模型

#### 多步驟攻擊模擬：The Last Ones（TLO）

TLO 是模擬 32 步企業網路攻擊的完整情境（熟練人類專業人員需約 20 小時）：

| 模型 | 平均完成步驟 | 完整通關次數（10 次嘗試） |
|------|------------|----------------------|
| **Mythos Preview** | **22 / 32 步** | **3 次**（史上首次） |
| Claude Opus 4.6 | 16 / 32 步 | 0 次 |

> 🔴 **Mythos Preview 是史上第一個能從頭到尾完整完成 TLO 模擬的 AI 模型。**

### 2.4 漏洞發現能力

Mythos Preview 在自主模式（無人工引導）下已發現的具體漏洞：

| 漏洞 | 目標系統 | 潛伏年份 |
|------|---------|---------|
| TCP 有號整數溢位 | OpenBSD | **27 年** |
| H.264 解碼器記憶體錯誤 | FFmpeg | **16 年** |
| Guest-to-Host 記憶體損壞 | 生產環境 VMM | — |
| 多個 Linux 核心提權漏洞 | Linux Kernel | — |

**Firefox 漏洞發現對比：**
```
Mythos Preview：181 個成功利用
Claude Opus 4.6： 2 個成功利用
```

### 2.5 進階攻擊技術

Mythos Preview 能自主實作的攻擊技術包含：

- **ROP Chain（Return-Oriented Programming）**：遠端程式碼執行，在 FreeBSD NFS 上構建 20 個 Gadget 的 ROP 鏈
- **KASLR Bypass**：核心位址空間隨機化繞過
- **JIT Heap Spray + Sandbox Escape**：瀏覽器複合利用
- **Cross-Cache Memory Reclamation**：跨快取記憶體回收攻擊
- **Multi-Vulnerability Chaining**：多漏洞串接提權

### 2.6 已知限制

- 無法完成「Cooling Tower」工控系統（OT）攻擊情境
- 評估環境缺乏真實世界的主動防禦與告警機制
- 不代表真實有防禦佈署環境的成功率

---

## 三、Project Glasswing（玻璃翼計畫）

### 3.1 命名由來

> 玻璃翼蝴蝶（*Greta oto*）以透明的翅膀著稱——象徵 **透明、可見、揭露隱藏的威脅**。

### 3.2 計畫目標

在 AI 驅動的網路攻擊時代到來之前，**主動修補關鍵軟體中的漏洞**，給予防禦方持久優勢。

```
核心理念：先讓防禦者取得 AI 漏洞發現能力，
         在攻擊者獲得同等能力之前完成修補。
```

### 3.3 創始夥伴（12 家核心組織）

| 類別 | 組織 |
|------|------|
| 雲端平台 | Amazon Web Services、Google、Microsoft |
| 終端裝置 | Apple |
| 資安廠商 | CrowdStrike、Palo Alto Networks、Broadcom、Cisco |
| 金融機構 | JPMorgan Chase |
| AI 開發 | Anthropic、NVIDIA |
| 開源生態 | Linux Foundation |

> 另有 **40+ 家** 維護關鍵軟體的組織獲得存取權限。

### 3.4 財務承諾

| 項目 | 金額 |
|------|------|
| 模型使用配額（全計畫） | **$1 億美元** |
| Alpha-Omega + OpenSSF（透過 Linux Foundation） | **$250 萬美元** |
| Apache 軟體基金會 | **$150 萬美元** |

> 開源軟體維護者可**免費**使用 Mythos Preview 進行安全掃描。

### 3.5 負責任揭露流程

```
[發現漏洞]
    │
    ▼
[SHA-3 Hash 承諾]  ← 密碼學證明，不揭露細節
    │
    ▼
[人工分類驗證]  ← 專業資安研究員審查
    │
    ▼
[通知廠商]
    │
    ▼
[90 天修補期 + 45 天延長期]
    │
    ▼
[公開揭露]
```

---

## 四、資安產業衝擊分析

### 4.1 漏洞利用時間軸壓縮

```
2018：漏洞公開到被利用的中位數時間  →  771 天
2024：                              →  不到 4 小時
2026（預估）：                       →  不到 1 小時
```

### 4.2 攻守失衡的新現實

| 面向 | 舊現實 | 新現實（Mythos 時代） |
|------|-------|-------------------|
| 漏洞發現 | 需要稀缺的人類專家 | AI 自主、大規模、7×24 |
| 漏洞利用開發 | 數週到數月 | 分鐘到小時 |
| 攻擊準入門檻 | 高（需深度技術知識） | 民主化（工具可及） |
| 防禦端資源 | 有人力上限 | 面臨海量告警與修補壓力 |

### 4.3 Bishop Fox 的觀點

> "AI 加速了**發現**，但不能取代**決策**。  
> 真正的挑戰在於：在特定業務情境中，判斷哪些漏洞代表真實可行動的風險。"

---

## 五、紅隊 vs 藍隊：課程連結

### 5.1 紅隊（攻擊方）視角

Mythos Preview 等 AI 工具對攻擊者的意義：
- 自動化漏洞掃描與零日發現
- 自主建構 ROP Chain、bypass ASLR/KASLR
- 多漏洞串接提權（原本需要資深研究員）

**CTF 練習建議：** 嘗試在授權環境中使用 AI 輔助工具加速漏洞識別流程。

### 5.2 藍隊（防禦方）視角

Anthropic 與資安專家的建議行動：

1. **立即採用** 語言模型驅動的漏洞掃描工具
2. **加速** 軟體修補週期（Patching Cycle）
3. **強化** 存取控制與最小權限原則
4. **完善** 記錄與監控機制（Logging）
5. **建立** 自動化事件回應系統
6. **審視** 漏洞揭露政策是否符合新時代需求

---

## 六、倫理與政策討論

### 6.1 限制存取的兩難

**支持限制存取的理由：**
- 防止惡意行為者武器化此能力
- 給予防禦方修補的時間窗口
- 避免大規模網路攻擊的災難性後果

**反對意見：**
- 較小的模型配合適當工具可能達到類似效果
- 限制存取讓少數組織掌握不對稱的能力優勢
- 防禦方資源不足以快速處理所有發現的漏洞

### 6.2 AI 武器化的倫理界線

| 使用情境 | 合法性 | 說明 |
|---------|--------|------|
| 授權滲透測試 | ✅ 合法 | 有書面授權的測試 |
| 漏洞賞金計畫 | ✅ 合法 | 在範圍內的漏洞回報 |
| CTF 競賽 | ✅ 合法 | 教育/競賽用途 |
| 無授權掃描 | ❌ 違法 | 即使無惡意也違法 |
| 惡意攻擊部署 | ❌ 嚴重違法 | 刑事責任 |

---

## 七、今日實驗

📄 **[建立 DVWA 靶機（Docker on Kali）](./dvwa-docker-kali-setup.md)**

在 Kali Linux VirtualBox 中使用 Docker 建立 DVWA（Damn Vulnerable Web Application）練習環境，實際操作 Web 漏洞攻擊。

---

## 八、期中專題發表要點

本週為期中專題發表，各組請在報告中融入以下反思：

1. **你的專題攻擊手法** 是否已能被 AI 自動化？
2. **防禦機制** 如何因應 AI 輔助攻擊的速度提升？
3. **你學到的技術** 在 AI 驅動的資安時代還有哪些不可取代的價值？

---

## 參考資料

- [Project Glasswing — Anthropic](https://www.anthropic.com/glasswing)
- [Our evaluation of Claude Mythos Preview's cyber capabilities — AISI](https://www.aisi.gov.uk/blog/our-evaluation-of-claude-mythos-previews-cyber-capabilities)
- [Claude Mythos Preview Red Team Report — Anthropic](https://red.anthropic.com/2026/mythos-preview/)
- [Claude Mythos Preview: The AI Cybersecurity Inflection Point — Bishop Fox](https://bishopfox.com/blog/anthropics-claude-mythos-preview-the-ai-cybersecurity-inflection-point)
- [Claude Mythos #2: Cybersecurity and Project Glasswing — Zvi Mowshowitz](https://thezvi.substack.com/p/claude-mythos-2-cybersecurity-and)
- [Project Glasswing: Securing critical software for the AI era — Linux Foundation](https://www.linuxfoundation.org/blog/project-glasswing-gives-maintainers-advanced-ai-to-secure-open-source)
- [Anthropic Claude Mythos Preview — CrowdStrike](https://www.crowdstrike.com/en-us/blog/crowdstrike-founding-member-anthropic-mythos-frontier-model-to-secure-ai/)
- [Project Glasswing Marks a Turning Point for Cybersecurity — Arctic Wolf](https://arcticwolf.com/resources/blog/project-glasswing-marks-a-turning-point-for-cybersecurity/)
- [Claude Mythos test: attack capabilities and limits — Help Net Security](https://www.helpnetsecurity.com/2026/04/14/claude-mythos-test-attack-capabilities-limits/)
- [Anthropic Releases Claude Mythos Preview — InfoQ](https://www.infoq.com/news/2026/04/anthropic-claude-mythos/)
