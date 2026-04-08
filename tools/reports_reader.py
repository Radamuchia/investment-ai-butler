#!/usr/bin/env python3
"""
AlphaButler 報告讀取工具
讓 Codex CLI 或任何 AI agent 快速存取 Deep Research 報告

用法：
  python tools/reports_reader.py                    # 列出所有報告
  python tools/reports_reader.py --stock 3661       # 顯示單一報告
  python tools/reports_reader.py --context          # 輸出所有報告（可 pipe 給 Codex）
  python tools/reports_reader.py --context 3661 6263 # 指定股票輸出 context
  python tools/reports_reader.py --prompt 3661 "分析護城河" # 直接生成 Codex 提示詞

與 Codex CLI 搭配使用：
  python tools/reports_reader.py --context | codex "根據以上報告，幫我比較五家公司的護城河強度"
  codex < <(python tools/reports_reader.py --prompt 3661 "這支股票現在適合買嗎")
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# ── 路徑設定 ─────────────────────────────────────────────
REPO_ROOT    = Path(__file__).parent.parent
REPORTS_DIR  = REPO_ROOT / "reports"
WATCHLIST    = REPO_ROOT / "watchlist.json"


# ── 載入 watchlist 取得公司名稱 ────────────────────────────
def _load_watchlist() -> dict:
    """回傳 {stock_id: {company_name, industry, ...}} 對照表"""
    if not WATCHLIST.exists():
        return {}
    try:
        data = json.loads(WATCHLIST.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {str(item.get("stock_id", "")): item for item in data}
        if isinstance(data, dict):
            result = {}
            for v in data.values():
                if isinstance(v, list):
                    for item in v:
                        result[str(item.get("stock_id", ""))] = item
            return result
    except Exception:
        pass
    return {}


# ── 核心函式 ──────────────────────────────────────────────
def list_reports() -> list[dict]:
    """列出 reports/ 下所有 .txt 報告，每支股票只保留最新一份"""
    latest: dict[str, dict] = {}
    wl = _load_watchlist()

    for f in sorted(REPORTS_DIR.glob("report_*.txt")):
        parts = f.stem.split("_")           # report_STOCKID_DATE
        if len(parts) < 3:
            continue
        stock_id = parts[1]
        date     = "_".join(parts[2:])
        info     = wl.get(stock_id, {})

        entry = {
            "stock_id":     stock_id,
            "company_name": info.get("company_name", stock_id),
            "industry":     info.get("industry", "—"),
            "date":         date,
            "path":         f,
            "size_kb":      round(f.stat().st_size / 1024, 1),
        }
        # 同一股票只保留日期最新的
        if stock_id not in latest or date > latest[stock_id]["date"]:
            latest[stock_id] = entry

    return sorted(latest.values(), key=lambda x: x["stock_id"])


def load_report(stock_id: str) -> str:
    """載入指定股票的最新報告全文"""
    matches = sorted(REPORTS_DIR.glob(f"report_{stock_id}_*.txt"), reverse=True)
    if not matches:
        return f"[ERROR] 找不到 {stock_id} 的報告，請先執行 run_research.py --stock {stock_id}"
    return matches[0].read_text(encoding="utf-8")


def build_context(stock_ids: list[str] | None = None) -> str:
    """
    將多份報告組合成 AI 可直接引用的 context 字串。
    stock_ids=None 表示載入所有報告。
    """
    reports = list_reports()
    if stock_ids:
        reports = [r for r in reports if r["stock_id"] in stock_ids]

    if not reports:
        return "[ERROR] 沒有找到符合條件的報告"

    lines = [
        "# AlphaButler — Deep Research 研究資料庫",
        f"資料更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"報告數量：{len(reports)} 份",
        "",
        "以下每份報告均由 Gemini Deep Research 依「護城河 → 估值 → 倉位」",
        "價值投資框架生成，可直接引用作為投資分析依據。",
        "",
        "=" * 60,
    ]

    for r in reports:
        lines += [
            "",
            f"## [{r['stock_id']}] {r['company_name']}  ({r['industry']})  研究日期：{r['date']}",
            "",
            load_report(r["stock_id"]),
            "",
            "=" * 60,
        ]

    return "\n".join(lines)


def build_prompt(stock_id: str, question: str) -> str:
    """
    生成一個含報告 + 問題的完整 prompt，直接貼給任何 AI 使用。
    """
    report = load_report(stock_id)
    wl = _load_watchlist()
    info = wl.get(stock_id, {})
    company = info.get("company_name", stock_id)

    return f"""你是一位專業的價值投資分析師。
以下是 {company}（{stock_id}）的 Gemini Deep Research 研究底稿：

<research_report stock="{stock_id}" company="{company}" date="{datetime.now().strftime('%Y-%m-%d')}">
{report}
</research_report>

請根據上述研究底稿回答以下問題：
{question}

回答要求：
- 直接引用報告中的具體數據與段落
- 標注不確定或資料不足之處
- 用繁體中文回答
"""


# ── CLI 介面 ──────────────────────────────────────────────
def _print_list():
    reports = list_reports()
    if not reports:
        print("⚠️  reports/ 目錄下沒有報告，請先執行 run_research.py")
        return
    print(f"\n{'股票':>6}  {'公司':10}  {'產業':12}  {'日期':12}  {'大小':>8}")
    print("-" * 60)
    for r in reports:
        print(f"{r['stock_id']:>6}  {r['company_name']:10}  {r['industry']:12}  {r['date']:12}  {r['size_kb']:>6.1f} KB")
    print(f"\n共 {len(reports)} 份報告  •  路徑：{REPORTS_DIR}\n")


def main():
    args = sys.argv[1:]

    if not args:
        _print_list()
        return

    if args[0] == "--stock" and len(args) >= 2:
        print(load_report(args[1]))

    elif args[0] == "--context":
        stock_ids = args[1:] or None
        print(build_context(stock_ids))

    elif args[0] == "--prompt" and len(args) >= 3:
        stock_id = args[1]
        question = " ".join(args[2:])
        print(build_prompt(stock_id, question))

    elif args[0] == "--help":
        print(__doc__)

    else:
        print(f"[ERROR] 未知參數：{args}")
        print("執行 python tools/reports_reader.py --help 查看說明")


if __name__ == "__main__":
    main()
