# [B] 研究報告推手 — Agent 規格文件

> 版本：v0.1.0 | 更新日期：2026-03-30
> ⚠️ 本 Agent 在獨立 worktree `agent-b` 分支開發

---

## 職責

自動操控 Gemini Deep Research，生成股票深度研究報告。

---

## 為何不使用 API？

Gemini Deep Research 目前**無公開 API 接口**，因此採用瀏覽器自動化（Browser Automation）方式前端操控，屬於 RPA（機器人流程自動化）技術。

---

## 技術方案：Playwright

```python
from playwright.async_api import async_playwright

async def run_deep_research(prompt: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 1. 導航至 Gemini
        await page.goto("https://gemini.google.com")

        # 2. 選擇 Deep Research 模式
        await page.click("[data-deep-research-btn]")

        # 3. 注入結構化研究提示詞
        await page.fill("textarea", prompt)
        await page.keyboard.press("Enter")

        # 4. 等待報告生成（最長 10 分鐘）
        await page.wait_for_selector(
            "[data-report-complete]",
            timeout=600000
        )

        # 5. 擷取報告內容
        report = await page.inner_text("[data-report-content]")
        return report
```

---

## 輸入

| 來源 | 內容 |
|------|------|
| [F] 數據管理師 | 股票代碼、基本財報數據、產業資訊 |
| 提示詞模板 | 結構化研究提示詞（見下方）|

---

## 提示詞模板結構

```
【股票研究請求】
公司名稱：{company_name}（{stock_id}）
產業：{industry}

【財務概況】
- 最新 EPS：{eps}
- ROE：{roe}%
- 毛利率：{gross_margin}%
- 營收 YoY：{revenue_yoy}%
- 自由現金流：{fcf}

【請進行以下研究】
1. 公司核心競爭優勢與護城河分析
2. 產業趨勢與競爭對手比較
3. 財務健康度評估
4. 潛在風險因素
5. 長期投資價值評估（3-5 年）

【總體環境】
- 當前利率：{interest_rate}%
- CPI：{cpi}%
```

---

## 輸出

研究報告輸出至 **[F] 數據管理師**，包含：
- 純文字報告內容
- 生成時間戳記
- 股票代碼對應
- 報告版本號

---

## 獨立開發原因

| 原因 | 說明 |
|------|------|
| 特殊環境依賴 | 需要真實 Chromium 瀏覽器環境 |
| 穩定性隔離 | Gemini 頁面改版不影響其他 Agent |
| 資源隔離 | 瀏覽器佔用大量記憶體，需獨立部署 |
| 可獨立部署 | 可部署在本機或有瀏覽器的獨立機器 |

---

## 任務流程（非同步 MQ）

```
[E/用戶] 觸發研究請求
    │
    ▼
Redis Queue（任務排隊）
    │
    ▼
[B] 取出任務 → 啟動 Playwright
    │
    ▼
Gemini Deep Research（等待 5~10 分鐘）
    │
    ▼
擷取報告 → 輸出至 [F]
    │
    ▼
通知請求方（task_id 完成）
```

---

## 注意事項

- 需預先儲存 Gemini 登入 Cookie / Session
- Gemini PRO 帳號必要（支援 Deep Research）
- 每次研究約需 5~10 分鐘，採非同步處理
- 頁面 Selector 需定期維護（Gemini 改版時）

---

## Worktree 開發資訊

```bash
# 切換至 agent-b worktree
cd ~/Documents/investment-ai-butler-agent-b

# 完成後 merge 回 main
git checkout main
git merge agent-b
```
