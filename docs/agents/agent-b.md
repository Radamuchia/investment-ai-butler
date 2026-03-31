# [B] 研究報告推手 — Agent 規格文件

> 版本：v0.3.0 | 更新日期：2026-03-31
> ⚠️ 本 Agent 在獨立 worktree `agent-b` 分支開發
> 📁 程式碼位置：`~/Documents/investment-ai-butler-agent-b/`

---

## 職責

自動操控 Gemini Deep Research，生成股票深度研究報告並回傳給 [F] 數據管理師。

---

## 為何不使用 API？

Gemini Deep Research 目前**無公開 API 接口**，採用 Playwright 瀏覽器自動化（RPA）前端操控。

---

## 核心檔案結構

```
investment-ai-butler-agent-b/
├── agents/agent_b_research/
│   ├── __init__.py
│   ├── browser.py          # Chrome 持久化 profile 管理
│   └── gemini_research.py  # Deep Research 自動化核心
├── test_agent_b.py         # 單股測試腳本
├── run_research.py         # CLI 多股票執行腳本
├── .chrome-profile/        # Chrome 專屬 profile（含登入 session）
│   ⚠️  已加入 .gitignore，不可 commit（含 Google cookie）
└── venv/                   # Python 虛擬環境
```

---

## 自動化流程（完整版）

```
Step 1  goto https://gemini.google.com/app
Step 2  確認 PRO 模式
          ↳ 讀取 [data-test-id="bard-mode-menu-button"] 的文字
          ↳ 若非 Pro → click menu → click [data-test-id="bard-mode-option-pro"]
Step 3  啟動 Deep Research
          ↳ click button[role="button"][name="工具"]（exact=True）
          ↳ click menuitemcheckbox[name="Deep Research"]
Step 4  輸入提示詞並傳送
          ↳ locator(".ql-clipboard").fill(prompt)
          ↳ 若失敗 fallback → .ql-editor（Quill 編輯器）
          ↳ click button[name="傳送訊息"]
Step 5  等待研究計畫並確認開始
          ↳ wait 8 秒（計畫生成）
          ↳ wait_for [data-test-id="confirm-button"] → click
          ↳ 備援：click(740, 360) → Tab × 6 → Enter
Step 6  等待研究完成（10 分鐘～數十分鐘）
          ↳ 每 30 秒輪詢 document.body.innerText
          ↳ 完成信號：「我已經完成研究」（固定出現）
          ↳ ⚠️  不可用「已完成」—— 研究步驟進行中每完成一項也會出現，造成誤判
Step 7  擷取報告
          ↳ selector: deep-research-immersive-panel（✅ 實測確認，2026-03-31）
          ↳ 含研究思考過程（Researching websites...），保留作參考
          ↳ 清除頂部 UI 按鈕文字（目錄 / 分享及匯出 / 建立）
```

---

## 關鍵 Selectors（Playwright Codegen 實測，2026-03-31）

| 操作 | Selector | 方法 |
|------|----------|------|
| 模式選單按鈕 | `[data-test-id="bard-mode-menu-button"]` | `.click()` |
| PRO 模式選項 | `[data-test-id="bard-mode-option-pro"]` | `.click()` |
| 工具按鈕 | `button`, role=button, name="工具", exact=True | `get_by_role()` |
| Deep Research | `menuitemcheckbox`, name="Deep Research" | `get_by_role()` |
| 提示詞輸入框 | `.ql-clipboard` → fallback `.ql-editor` | `.fill()` |
| 傳送按鈕 | `button`, name="傳送訊息" | `get_by_role()` |
| 開始研究確認 | `[data-test-id="confirm-button"]` | `.click()` |
| 完成偵測 | `document.body.innerText` contains `我已經完成研究` | JS evaluate |
| 報告容器 | `deep-research-immersive-panel` | `.inner_text()` |

> ⚠️ Gemini 為 SPA，selector 可能因版本更新失效，需定期以 Playwright Codegen 重新錄製驗證。

---

## 例外處理設計

### 1. 輸入框 fallback

```python
# 主要：Codegen 錄製
locator(".ql-clipboard").fill(prompt)

# fallback：Quill 可見編輯區
locator(".ql-editor").first.fill(prompt)
```

### 2. 開始研究確認 fallback

```python
# 主要：精確 selector
locator('[data-test-id="confirm-button"]').wait_for(timeout=30000)

# fallback：鍵盤操作（用戶實測確認）
page.mouse.click(740, 360)   # 重置 Tab 焦點
keyboard.press("Tab") × 6   # 移至開始研究按鈕
keyboard.press("Enter")
```

### 3. 超時設定

```bash
# 預設 90 分鐘，可用環境變數調整
RESEARCH_TIMEOUT=3600 python run_research.py --stock 2330
```

### 4. asyncio.sleep vs page.wait_for_timeout

```python
# ❌ 不可用：點擊「開始研究」後頁面導航，page 物件失效
await page.wait_for_timeout(30000)

# ✅ 正確：完全獨立於頁面狀態
await asyncio.sleep(30)
```

### 5. 報告擷取 fallback 順序

```
deep-research-immersive-panel   ← 主要（實測有效）
response-container              ← 備用
[class*='deep-research']        ← 廣泛比對
JS 最大文字區塊掃描              ← fallback
document.body.innerText         ← 最終 fallback
```

---

## 完成偵測踩坑紀錄

| 關鍵字 | 問題 | 結論 |
|--------|------|------|
| `已完成` | ❌ 研究進行中每完成一個子步驟也會出現 → 誤判提早結束 | 禁用 |
| `研究完成` | ⚠️ 未實測確認是否存在 | 保留備用 |
| `我已經完成研究` | ✅ Gemini 研究結束後固定顯示的完整句子 | 主要偵測 |

---

## 報告面板結構說明

```
deep-research-immersive-panel
├── [頂部 UI] 標題 / 目錄 / 分享及匯出 / 建立   ← _clean_report() 移除
├── [正文]   完整研究報告（通常 15,000~25,000 字）
└── [穿插]   Researching websites... + 來源網址  ← 保留，可作研究來源參考
```

---

## 輸入格式

```python
stock_data = {
    "stock_id": "2330",
    "company_name": "台積電",
    "industry": "半導體／晶圓代工",
    "eps": 32.3,
    "roe": 26.5,
    "gross_margin": 53.2,
    "revenue_yoy": 15.3,
    "fcf": 800,
    "interest_rate": 4.5,
    "cpi": 2.8,
}
```

## 輸出格式

```python
{
    "stock_id": "2330",
    "report": "完整研究報告文字...",
    "generated_at": "2026-03-31T18:47:36.014006",
    "status": "success",   # 或 "failed"
    "error": None          # 失敗時為錯誤訊息字串
}
```

---

## Chrome Profile 設定

```python
# browser.py 關鍵設定
launch_persistent_context(
    user_data_dir=".chrome-profile",      # 獨立 profile，保存登入 session
    channel="chrome",                      # 使用系統 Chrome（非 Chromium）
    ignore_default_args=["--enable-automation", "--disable-infobars"],
    args=[
        "--disable-blink-features=AutomationControlled",  # 繞過 bot 偵測
        "--no-first-run",
        "--no-default-browser-check",
    ],
    viewport={"width": 1280, "height": 900},
)
```

### 首次登入流程

```bash
# 首次執行會自動開啟 Google 登入頁，手動完成登入後 session 會保存
python -c "
import asyncio
from agents.agent_b_research.browser import BrowserManager
async def login():
    bm = BrowserManager()
    await bm.start()
    input('請完成 Google 登入後按 Enter...')
    await bm.close()
asyncio.run(login())
"
```

---

## 執行方式

```bash
cd ~/Documents/investment-ai-butler-agent-b
source venv/bin/activate

# 單股測試
python test_agent_b.py

# CLI 多股票
python run_research.py --stock 2330
python run_research.py --stock 2330 2454 2317

# 調整超時（分鐘）
RESEARCH_TIMEOUT=3600 python run_research.py --stock 2330
```

---

## 獨立開發原因

| 原因 | 說明 |
|------|------|
| 特殊環境依賴 | 需要真實 Chrome 瀏覽器環境與登入 session |
| 穩定性隔離 | Gemini 頁面改版不影響其他 Agent |
| 資源隔離 | 瀏覽器佔用大量記憶體，需獨立部署 |
| Selector 維護 | 使用 Playwright Codegen 重新錄製，需獨立迭代 |

---

## 任務流程

```
[E/用戶] 觸發研究請求
    │
    ▼
[B] 啟動 Playwright Chrome
    │
    ▼
Gemini Deep Research（10 分鐘～數十分鐘）
    │
    ▼
擷取 deep-research-immersive-panel 內容
    │
    ▼
輸出至 [F] 數據管理師
```

---

## Worktree 開發資訊

```bash
# 切換至 agent-b worktree
cd ~/Documents/investment-ai-butler-agent-b

# 完成後 merge 回 main
git checkout main
git merge agent-b
```
