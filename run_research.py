"""
Agent B — CLI 多股票研究腳本

執行方式：
    cd ~/Documents/investment-ai-butler-agent-b
    source venv/bin/activate

    # 單股
    python run_research.py --stock 2330

    # 多股票（依序執行）
    python run_research.py --stock 2330 2454 2317

    # 自訂超時（秒）
    RESEARCH_TIMEOUT=3600 python run_research.py --stock 2330

    # 指定輸出目錄
    python run_research.py --stock 2330 --output ./reports
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from agents.agent_b_research import GeminiResearcher

# ── 股票基本資料庫（之後由 Agent F 提供，目前手動維護）──
STOCK_DATABASE = {
    "2330": {
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
    },
    "2454": {
        "stock_id": "2454",
        "company_name": "聯發科",
        "industry": "IC 設計",
        "eps": 78.2,
        "roe": 21.3,
        "gross_margin": 47.1,
        "revenue_yoy": 22.4,
        "fcf": 120,
        "interest_rate": 4.5,
        "cpi": 2.8,
    },
    "2317": {
        "stock_id": "2317",
        "company_name": "鴻海",
        "industry": "電子製造服務",
        "eps": 10.8,
        "roe": 11.2,
        "gross_margin": 6.3,
        "revenue_yoy": 8.7,
        "fcf": 320,
        "interest_rate": 4.5,
        "cpi": 2.8,
    },
}


def get_stock_data(stock_id: str) -> dict:
    """取得股票資料，若資料庫無資料則建立基本結構"""
    if stock_id in STOCK_DATABASE:
        return STOCK_DATABASE[stock_id]
    # 找不到時建立基本結構，讓 Gemini 自行研究
    print(f"  ⚠️  {stock_id} 不在資料庫，將以股票代碼進行研究")
    return {
        "stock_id": stock_id,
        "company_name": stock_id,
        "industry": "N/A",
        "eps": "N/A",
        "roe": "N/A",
        "gross_margin": "N/A",
        "revenue_yoy": "N/A",
        "fcf": "N/A",
        "interest_rate": 4.5,
        "cpi": 2.8,
    }


def save_report(result: dict, output_dir: str = "."):
    """儲存研究報告（txt + json）"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    date_str = result["generated_at"][:10]
    base_name = f"report_{result['stock_id']}_{date_str}"

    # 純文字報告
    txt_path = Path(output_dir) / f"{base_name}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"股票代碼：{result['stock_id']}\n")
        f.write(f"生成時間：{result['generated_at']}\n")
        f.write("=" * 60 + "\n\n")
        f.write(result["report"])
    print(f"  📄 報告儲存：{txt_path}")

    # JSON 結構（供 Agent F 使用）
    json_path = Path(output_dir) / f"{base_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  📋 JSON 儲存：{json_path}")

    return str(txt_path)


async def research_stock(stock_id: str, output_dir: str) -> dict:
    """對單一股票執行 Deep Research"""
    stock_data = get_stock_data(stock_id)
    researcher = GeminiResearcher()
    result = await researcher.research(stock_data)

    if result["status"] == "success":
        save_report(result, output_dir)
    return result


async def main():
    parser = argparse.ArgumentParser(
        description="Agent B — Gemini Deep Research 自動化"
    )
    parser.add_argument(
        "--stock",
        nargs="+",
        required=True,
        metavar="STOCK_ID",
        help="股票代碼，可輸入多個（例：2330 2454 2317）",
    )
    parser.add_argument(
        "--output",
        default="./reports",
        help="報告輸出目錄（預設：./reports）",
    )
    args = parser.parse_args()

    stocks = args.stock
    output_dir = args.output

    print("\n" + "=" * 60)
    print("  Agent B — Gemini Deep Research 自動化")
    print("=" * 60)
    print(f"  股票清單：{', '.join(stocks)}")
    print(f"  輸出目錄：{output_dir}")
    print(f"  超時設定：{os.getenv('RESEARCH_TIMEOUT', '5400')} 秒")
    print("=" * 60 + "\n")

    results = []
    for i, stock_id in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] 開始研究 {stock_id}...")
        result = await research_stock(stock_id, output_dir)
        results.append(result)

        if result["status"] == "success":
            chars = len(result["report"]) if result["report"] else 0
            print(f"  ✅ {stock_id} 完成（報告 {chars} 字）")
        else:
            print(f"  ❌ {stock_id} 失敗：{result['error']}")

        # 多股票間等待，避免連續操作被偵測
        if i < len(stocks):
            print(f"\n  ⏳ 等待 10 秒後繼續下一支...")
            await asyncio.sleep(10)

    # 總結
    print("\n" + "=" * 60)
    print("  執行總結")
    print("=" * 60)
    success = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - success
    print(f"  成功：{success} 支 ｜ 失敗：{failed} 支")
    for r in results:
        icon = "✅" if r["status"] == "success" else "❌"
        print(f"  {icon} {r['stock_id']} — {r['status']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
