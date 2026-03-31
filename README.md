# [B] 研究報告推手 — Gemini Deep Research 自動化

> 投資 AI 管家系統的子模組，自動操控 Gemini Deep Research 生成股票深度研究報告。

---

## 為什麼需要這個？

Gemini Deep Research 目前**沒有公開 API**，但它能在 10~30 分鐘內生成 15,000~25,000 字的深度研究報告，遠超一般搜尋能力。

本模組使用 **Playwright 瀏覽器自動化**（RPA）操控 Chrome，模擬真人操作完成整個研究流程。

---

## 系統需求

- macOS（已在 macOS 14+ 測試）
- Python 3.11+
- Google Chrome（系統已安裝）
- **Google 帳號（需有 Gemini Pro 訂閱）**

---

## 快速開始

### 1. 安裝（首次只需執行一次）

```bash
git clone https://github.com/Radamuchia/investment-ai-butler.git -b agent-b investment-ai-butler-agent-b
cd investment-ai-butler-agent-b
bash setup.sh
```

`setup.sh` 會自動完成：
- 建立 Python 虛擬環境
- 安裝所有依賴套件
- 安裝 Playwright Chrome
- 引導你完成 Google 登入（Session 儲存在本機，不上傳）

### 2. 開始研究

```bash
cd investment-ai-butler-agent-b
source venv/bin/activate

# 單一股票
python run_research.py --stock 2330

# 多支股票（依序執行）
python run_research.py --stock 2330 2454 2317

# 指定輸出目錄
python run_research.py --stock 2330 --output ./my-reports
```

### 3. 查看報告

研究完成後，報告儲存於 `reports/` 目錄：
```
reports/
├── report_2330_2026-03-31.txt    ← 純文字報告（完整內容）
└── report_2330_2026-03-31.json   ← JSON 格式（供其他程式使用）
```

---

## 自動化流程說明

```
開啟 Gemini → 確認 PRO 模式 → 點擊「工具」→ 選擇「Deep Research」
→ 輸入提示詞 → 點擊「傳送訊息」→ 等待研究計畫 → 點擊「開始研究」
→ 等待完成（偵測「我已經完成研究」）→ 擷取報告
```

研究時間視題目複雜度而定：
- 簡單題目（單一公司）：約 10 分鐘
- 複雜題目（跨產業比較、總經分析）：30~60 分鐘

---

## 設定說明

複製 `.env.example` 為 `.env` 並調整：

```bash
cp .env.example .env
```

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `RESEARCH_TIMEOUT` | `5400` | 研究超時秒數（90 分鐘） |
| `REPORT_MIN_CHARS` | `3000` | 報告最少字數 |
| `HEADLESS` | `false` | `true` 為背景執行（不顯示瀏覽器）|

---

## 目錄結構

```
investment-ai-butler-agent-b/
├── agents/
│   └── agent_b_research/
│       ├── __init__.py
│       ├── browser.py          # Chrome 持久化 profile 管理
│       └── gemini_research.py  # Deep Research 自動化核心
├── reports/                    # 研究報告輸出（.gitignore 排除）
├── run_research.py             # CLI 執行腳本（主要入口）
├── test_agent_b.py             # 開發用測試腳本
├── setup.sh                    # 首次安裝腳本
├── requirements.txt            # Python 依賴
├── .env.example                # 環境變數範本
└── .chrome-profile/            # Chrome 登入 session（.gitignore 排除）
```

---

## 常見問題

**Q：Chrome 開啟後沒有自動登入怎麼辦？**
登入 session 儲存在 `.chrome-profile/`，首次必須手動登入一次。執行 `bash setup.sh` 會引導你完成。

**Q：研究到一半中斷了？**
重新執行相同指令即可，每次研究都是獨立的新對話。

**Q：報告內容只有研究計畫，沒有完整報告？**
表示「開始研究」按鈕沒有成功點擊。可嘗試調整視窗解析度或重新執行。

**Q：如何設定更長的超時時間？**
```bash
RESEARCH_TIMEOUT=7200 python run_research.py --stock 2330
```

**Q：能在背景執行嗎？**
在 `.env` 設定 `HEADLESS=true`，Chrome 將在背景執行（不顯示視窗）。注意：部分 Google 安全機制可能在無頭模式下封鎖自動化，建議先以 `false` 確認穩定後再切換。

---

## 技術細節

Playwright Codegen 實測確認的關鍵 Selector（2026-03-31）：

| 操作 | Selector |
|------|----------|
| PRO 模式 | `[data-test-id="bard-mode-option-pro"]` |
| 工具按鈕 | `get_by_role("button", name="工具", exact=True)` |
| Deep Research | `get_by_role("menuitemcheckbox", name="Deep Research")` |
| 開始研究 | `[data-test-id="confirm-button"]` |
| 完成偵測 | 頁面出現「我已經完成研究」 |
| 報告容器 | `deep-research-immersive-panel` |

> ⚠️ Gemini 為 SPA，Selector 可能因版本更新失效。更新方式：重新執行 `playwright codegen --channel chrome --user-data-dir=.chrome-profile https://gemini.google.com` 錄製。

---

## 與主系統的關係

本模組是 [投資 AI 管家](https://github.com/Radamuchia/investment-ai-butler) 的 Agent B，在獨立 `agent-b` 分支開發。研究報告輸出將整合至 Agent F（數據管理師）統一處理。

---

## License

MIT
