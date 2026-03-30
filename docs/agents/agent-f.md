# [F] 數據管理師 — Agent 規格文件

> 版本：v0.1.0 | 更新日期：2026-03-30

---

## 職責

系統的數據核心。統一管理所有數據的輸入、輸出、計算與儲存，是所有 Agent 的唯一數據來源。

---

## 核心原則

- **Single Source of Truth**：全系統數據唯一出口
- **矩陣式儲存**：以股票代碼（列）× 指標（行）為基礎
- **申請制計算**：其他 Agent 透過標準 API 申請計算，不自行運算共用指標

---

## 對外 API 介面

```python
class DataManagerF:

    def get_metric(self, stock_id: str, metric: str, period: str = None):
        """取得單一指標"""

    def compute(self, stock_id: str, formula_id: str, params: dict = {}):
        """申請自訂公式計算"""

    def get_matrix(self, stock_list: list, metrics: list):
        """批量矩陣查詢（給 E 快篩員）"""

    def subscribe(self, stock_id: str, metric: str, callback):
        """訂閱數據更新推播（給 D 經理人）"""

    def write(self, stock_id: str, data: dict, source: str):
        """寫入數據（給 A 數據站）"""
```

---

## 資料庫設計

| 資料庫 | 技術 | 儲存內容 |
|--------|------|----------|
| 主資料庫 | PostgreSQL | 財報、指標、研究報告、買賣訊號 |
| 時序資料庫 | TimescaleDB（PostgreSQL 擴充）| 股價歷史時序數據 |
| 快取層 | Redis | 即時股價、高頻計算結果 |
| 任務佇列 | Redis Queue | [A][B] 非同步任務 |

---

## 數據矩陣結構

```
        股票代碼（列）
指標     2330   AAPL   NVDA
────────────────────────────
stock_price  ✓    ✓     ✓
eps          ✓    ✓     ✓
roe          ✓    ✓     ✓
pe           ✓    ✓     ✓
research     ✓    ✓     ✓
signal       ✓    ✓     ✓
updated_at   ✓    ✓     ✓
```

---

## 高可用設計

- PostgreSQL 主從備援
- Redis Sentinel 故障轉移
- 各 Agent 保留 TTL 短期本地快取
- 降級模式：[F] 故障時使用最後快取數據

---

## 請求優先權

| 優先權 | 來源 Agent | 說明 |
|--------|-----------|------|
| P1 | [D] 證券經理人 | 即時訊號，不可延遲 |
| P2 | [C] 價值分析 | 決策分析 |
| P3 | [E] 量化快篩員 | 批量查詢 |
| P4 | [B] 研究報告推手 | 非同步，可排隊 |

---

## 優先開發原因

[F] 是所有 Agent 的基礎依賴，**必須在其他 Agent 開始開發前完成介面定義**，確保其他 Agent 有穩定的數據合約可遵循。
