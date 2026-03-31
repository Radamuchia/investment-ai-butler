# 💼 投資 AI 管家

> 透過多個 AI Agent 協作，提供台股投資的全方位深度分析與買賣建議。

---

## 專案概覽

本系統由 7 個專門化 AI Agent 組成，各司其職，透過統一的數據管理層（Agent F）協作運作：

```
用戶 / UI
    │
    ▼
[E] 量化快篩員 ──→ [B] 研究報告推手（Gemini Deep Research）
    │                      │
    ▼                      ▼
[D] 證券經理人 ──→ [C] 價值分析（巴菲特/蒙格）
    │                      │
    └──────────┬────────────┘
               ▼
          [F] 數據管理師（Single Source of Truth）
               │
               ▼
          [A] 數據站（股價 / 財報 / 總經數據）
               │
               ▼
          [G] 使用者介面
```

---

## Agent 說明

| Agent | 名稱 | 職責 | 狀態 |
|-------|------|------|------|
| **A** | 數據站 | 自動抓取股價、財報、總經數據 | 🔲 開發中 |
| **B** | 研究報告推手 | Gemini Deep Research 自動化，生成深度研究報告 | ✅ 完成 |
| **C** | 價值分析巴菲特蒙格 | 內在價值計算、安全邊際分析 | 🔲 規劃中 |
| **D** | 證券經理人 | 即時買賣訊號生成 | 🔲 規劃中 |
| **E** | 量化效率快篩員 | 第一層股票篩選（財務指標過濾）| 🔲 規劃中 |
| **F** | 數據管理師 | 統一數據管理、計算引擎、Single Source of Truth | 🔲 開發中 |
| **G** | 使用者介面 | 儀表板、報告展示、操作介面 | 🔲 規劃中 |

---

## 核心設計原則

**Single Source of Truth（SSOT）**
所有數據統一由 Agent F 管理。其他 Agent 不直接存取資料庫，一律透過 Agent F 的 API 申請數據，確保數據一致性。

**非同步多 Agent 協作**
各 Agent 獨立運作，透過任務佇列（Redis）協調，避免單點阻塞。

**瀏覽器自動化彌補 API 缺口**
Gemini Deep Research 目前無公開 API，Agent B 使用 Playwright RPA 操控瀏覽器完成深度研究。

---

## Repo 結構

本專案分為兩個 Repo：

| Repo | 分支 | 內容 |
|------|------|------|
| [investment-ai-butler](https://github.com/Radamuncia/investment-ai-butler) | `main` | 主後端、文檔、Agent F |
| [investment-ai-butler](https://github.com/Radamuncia/investment-ai-butler) | `agent-b` | Agent B 獨立開發環境 |

Agent B 在獨立分支開發的原因：需要真實 Chrome 瀏覽器環境與 Google 登入 Session，資源需求與主後端不同。

---

## 快速開始

### Agent B（目前可用）

最快速的入口——自動生成股票深度研究報告：

```bash
git clone https://github.com/Radamuncia/investment-ai-butler.git -b agent-b investment-ai-butler-agent-b
cd investment-ai-butler-agent-b
bash setup.sh
```

詳細說明見 [Agent B README](https://github.com/Radamuncia/investment-ai-butler/blob/agent-b/README.md)。

---

## 技術棧

| 層次 | 技術 |
|------|------|
| 後端框架 | Python 3.11+、FastAPI |
| 瀏覽器自動化 | Playwright（Agent B）|
| 資料庫 | PostgreSQL（結構化數據）|
| 快取 / 佇列 | Redis |
| AI 模型 | Gemini Deep Research（B）、Claude（分析）|
| 容器化 | Docker Compose |

---

## 文檔

- [系統架構](docs/architecture.md)
- [Agent A — 數據站](docs/agents/agent-a.md)
- [Agent B — 研究報告推手](docs/agents/agent-b.md) ✅ 完整文檔
- [Agent C — 價值分析](docs/agents/agent-c.md)
- [Agent D — 證券經理人](docs/agents/agent-d.md)
- [Agent E — 量化快篩員](docs/agents/agent-e.md)
- [Agent F — 數據管理師](docs/agents/agent-f.md)

---

## License

MIT
