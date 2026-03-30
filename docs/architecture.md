# 投資AI管家 — 系統架構文檔

> 版本：v0.1.0 | 更新日期：2026-03-30

---

## 目錄
1. [專案概覽](#1-專案概覽)
2. [系統分層架構](#2-系統分層架構)
3. [Agent 總覽](#3-agent-總覽)
4. [資料流向](#4-資料流向)
5. [API 規格策略](#5-api-規格策略)
6. [數據管理原則](#6-數據管理原則)
7. [技術棧](#7-技術棧)
8. [專案目錄結構](#8-專案目錄結構)
9. [開發規劃](#9-開發規劃)
10. [Repo 結構](#10-repo-結構)

---

## 1. 專案概覽

**專案名稱**：投資的買賣建議全方面 AI 管家

**目標**：透過多個 AI Agent 協作，提供股票投資的全方位分析與即時買賣建議。

**核心理念**：
- 數據統一由 [F] 數據管理師處理（Single Source of Truth）
- 各 Agent 透過標準化 API 向 [F] 申請數據
- 達到數據範式標準化，消滅跨 Agent 數據矛盾

---

## 2. 系統分層架構

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4 │  展示層     │  [G] UI 介面                   │
├──────────┼─────────────┼────────────────────────────────┤
│  Layer 3 │  決策層     │  [C] 價值分析 / [D] 證券經理人  │
├──────────┼─────────────┼────────────────────────────────┤
│  Layer 2 │  研究層     │  [B] 研究報告推手 / [E] 快篩員  │
├──────────┼─────────────┼────────────────────────────────┤
│  Layer 1 │  數據層     │  [A] 數據站 / [F] 數據管理師    │
└──────────┴─────────────┴────────────────────────────────┘
```

**Orchestrator（主協調器）** 基於 Claude Agent SDK，負責協調所有 Agent 的執行順序與任務分派。

---

## 3. Agent 總覽

| Agent | 名稱 | 主要職責 | 主要 API/工具 |
|-------|------|----------|--------------|
| A | 數據站 | 股價與財報自動抓取 | Finmind, SEC EDGAR, FRED |
| B | 研究報告推手 | Gemini Deep Research 自動化 | Playwright（瀏覽器自動化）|
| C | 價值分析巴菲特蒙格 | 內在價值、護城河、安全邊際分析 | Claude Pro |
| D | 證券經理人 | 即時買賣訊號生成 | OpenAI / Claude |
| E | 量化效率快篩員 | 第一層量化指標篩選 | Finmind, SEC EDGAR |
| F | 數據管理師 | 統一數據管理、計算引擎、資料庫 | PostgreSQL, Redis |
| G | UI 設計師 | 使用者介面與數據視覺化 | Next.js, TradingView |

詳細各 Agent 規格請參閱 `docs/agents/` 目錄。

---

## 4. 資料流向

```
用戶口袋名單
      │
      ▼
[E] 量化快篩員 ─────────────────────────┐
      │                                  │
      ▼                                  │
[A] 數據站 ←── Finmind / SEC / FRED / TV │
      │                                  │
      ▼                                  │
[F] 數據管理師（矩陣資料庫）              │
  ├────────────► [B] 研究報告推手         │
  │                   │ Gemini Deep       │
  │                   ▼ Research          │
  ├────────────► [C] 價值分析             │
  │                   │ Claude Pro        │
  │                   ▼                  │
  └────────────► [D] 證券經理人 ◄─────────┘
                      │
                      ▼
               📊 買賣訊號
                      │
                      ▼
               [G] UI 介面
```

---

## 5. API 規格策略

採用**分場景混合策略**，根據各 Agent 需求選用最適合的通訊方式：

| 場景 | 規格 | 使用方 |
|------|------|--------|
| 同步查詢（即時需求） | REST API | [C][D][E][G] |
| 長時間非同步任務 | Message Queue (Redis Queue) | [A][B] |
| 即時推播（訂閱制） | WebSocket | [D][G] |
| 開發初期過渡 | Python 直接函式調用 | 全部（Prototype 階段）|

### 統一 API 介面（[F] 對外）

```python
class DataManagerF:
    # 取得單一指標
    def get_metric(self, stock_id, metric, period=None): ...

    # 申請自訂公式計算
    def compute(self, stock_id, formula_id, params={}): ...

    # 批量矩陣查詢（給 E 快篩員）
    def get_matrix(self, stock_list, metrics): ...

    # 訂閱數據更新（給 D 經理人）
    def subscribe(self, stock_id, metric, callback): ...
```

### 統一錯誤格式

```json
{
  "status": "error",
  "code": "DATA_NOT_FOUND",
  "stock": "2330",
  "metric": "ROE",
  "suggestion": "財報尚未更新，請等待 Q4 財報發布"
}
```

### 請求優先權

| 優先權 | Agent | 說明 |
|--------|-------|------|
| P1（最高）| [D] 證券經理人 | 即時買賣訊號不能延遲 |
| P2 | [C] 價值分析 | 決策層分析 |
| P3 | [E] 量化快篩員 | 批量查詢 |
| P4（最低）| [B] 研究報告推手 | 等待時間長，可排隊 |

---

## 6. 數據管理原則

### 核心原則：Single Source of Truth

所有數據與計算結果統一由 [F] 管理，其他 Agent 不自行計算共用指標。

### 分層策略

```
[F] 強制統一管理：
  ├─ 原始財報數據（EPS、營收、負債...）
  ├─ 基礎指標（PE、ROE、毛利率...）
  └─ 跨 Agent 共用的計算結果

Agent 本地允許：
  ├─ 該 Agent 專屬模型（僅 C 使用的 DCF 模型）
  ├─ 實驗性指標（未穩定前不納入 F）
  └─ 需要極低延遲的即時計算
```

### 數據矩陣結構

```
        股票代碼（列）
指標     2330   AAPL   NVDA   ...
──────────────────────────────────
股價      ✓      ✓      ✓
EPS       ✓      ✓      ✓
ROE       ✓      ✓      ✓
PE        ✓      ✓      ✓
研究報告  ✓      ✓      ✓
買賣訊號  ✓      ✓      ✓
更新時間  ✓      ✓      ✓
```

### 高可用設計

- **備援機制**：[F] 需高可用，避免單點故障
- **本地快取**：各 Agent 保留短期快取（Redis）
- **降級策略**：[F] 故障時的應急模式

---

## 7. 技術棧

| 層級 | 技術 | 用途 |
|------|------|------|
| 語言 | Python 3.11+ | 主要後端 |
| API 框架 | FastAPI | REST API 伺服器 |
| Agent 框架 | Claude Agent SDK | 多 Agent 協調 |
| 排程 | APScheduler | 定時任務（數據抓取）|
| 結構化資料庫 | PostgreSQL | 財報、指標持久化 |
| 快取 | Redis | 即時股價、計算結果快取 |
| 任務佇列 | Redis Queue | 非同步任務（[A][B]）|
| 瀏覽器自動化 | Playwright | [B] Gemini Deep Research |
| 前端 | Next.js 14 + TypeScript | [G] UI |
| 圖表 | TradingView Widget + Recharts | 股價圖表 |
| 容器化 | Docker Compose | 統一部署 |

### AI 模型分配

| Agent | 模型 | 原因 |
|-------|------|------|
| [B] 研究報告推手 | Gemini Pro（Deep Research）| 唯一支援 Deep Research |
| [C] 價值分析 | Claude Pro | 深度推理、長文本分析 |
| [D] 證券經理人 | Claude / OpenAI | 快速決策判斷 |
| Orchestrator | Claude Agent SDK | 多 Agent 協調 |

---

## 8. 專案目錄結構

```
investment-ai-butler/               ← 主後端 Repo
├── agents/
│   ├── agent_a_data/               # [A] 數據站
│   ├── agent_b_research/           # [B] 研究報告推手（worktree 獨立開發）
│   ├── agent_c_value/              # [C] 價值分析
│   ├── agent_d_signal/             # [D] 證券經理人
│   └── agent_e_screener/           # [E] 量化快篩員
├── agent_f/                        # [F] 數據管理師（核心）
│   ├── schemas/                    # 資料庫 Schema 定義
│   └── migrations/                 # 資料庫 Migration
├── orchestrator/                   # 主協調器
├── api/                            # FastAPI Gateway
├── database/                       # DB 設定
├── config/                         # 環境設定（API Keys 集中管理）
├── logs/                           # 日誌
├── tests/                          # 測試
└── docs/                           # 本文檔目錄
    ├── architecture.md             ← 本文件
    ├── agents/                     # 各 Agent 詳細規格
    ├── api/                        # API 規格文件
    └── database/                   # 資料庫 Schema 文件

investment-ai-butler-ui/            ← 前端獨立 Repo（Next.js）
```

---

## 9. 開發規劃

```
Phase 1（基礎）：  [F] worktree 先行 → 定義 API 介面與 Schema
Phase 2（數據）：  [A] 數據站 + [E] 量化快篩員
Phase 3（研究）：  [B] 研究報告推手（worktree 獨立）
Phase 4（決策）：  [C] 價值分析 → [D] 證券經理人
Phase 5（展示）：  [G] UI 介面（獨立 Repo）
Phase 6（整合）：  Orchestrator 協調所有 Agent
```

---

## 10. Repo 結構

| Repo | GitHub | 本地路徑 | 說明 |
|------|--------|----------|------|
| 主後端 | [investment-ai-butler](https://github.com/Radamuchia/investment-ai-butler) | `~/Documents/investment-ai-butler` | Python 後端主體 |
| 前端 UI | [investment-ai-butler-ui](https://github.com/Radamuchia/investment-ai-butler-ui) | `~/Documents/investment-ai-butler-ui` | Next.js 前端 |
| Agent B worktree | 同主後端 `agent-b` 分支 | `~/Documents/investment-ai-butler-agent-b` | Playwright 瀏覽器自動化 |
