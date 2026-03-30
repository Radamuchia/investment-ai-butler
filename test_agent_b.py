"""
Agent B 測試腳本
用真實股票數據測試 Gemini Deep Research 自動化

執行方式：
    cd ~/Documents/investment-ai-butler-agent-b
    source venv/bin/activate
    python test_agent_b.py
"""

import asyncio
from agents.agent_b_research import GeminiResearcher

# 測試用股票數據（模擬 [F] 提供的數據）
TEST_STOCK = {
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


async def main():
    print("=" * 50)
    print("  Agent B — Gemini Deep Research 測試")
    print("=" * 50)
    print(f"  股票：{TEST_STOCK['company_name']}（{TEST_STOCK['stock_id']}）")
    print(f"  模式：可見模式（headless=False）")
    print("=" * 50)
    print()

    researcher = GeminiResearcher()
    result = await researcher.research(TEST_STOCK)

    print()
    print("=" * 50)
    print(f"  狀態：{result['status']}")
    print(f"  時間：{result['generated_at']}")
    print("=" * 50)

    if result["status"] == "success":
        print("\n📄 研究報告（前 500 字）：\n")
        print(result["report"][:500])
        print("\n...")

        # 儲存完整報告
        filename = f"report_{result['stock_id']}_{result['generated_at'][:10]}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result["report"])
        print(f"\n✅ 完整報告已儲存：{filename}")

    else:
        print(f"\n❌ 錯誤：{result['error']}")


if __name__ == "__main__":
    asyncio.run(main())
