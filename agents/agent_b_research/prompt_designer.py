"""
AlphaButler — Deep Research 題目設計器

職責：根據股票資料生成適合 Gemini Deep Research 的研究題目。
不直接做研究，不給買賣建議，只輸出研究任務題目。

價值投資框架順序（固定）：
  1. 護城河
  2. 價格與長期報酬
  3. 進場倉位證據基礎（追蹤倉 / 分批倉 / 核心倉）
"""

# ── 產業別研究重點映射 ─────────────────────────────────────────────────────────
# 不同產業有不同的護城河來源與估值邏輯，題目要依此調整焦點

INDUSTRY_LENS = {
    # 半導體設備
    "半導體設備": {
        "moat_sources": "技術壁壘、客戶綁定、認證週期",
        "valuation_focus": "訂單能見度與資本支出週期",
        "cycle_keyword": "晶圓廠資本支出週期與交期",
    },
    # 記憶體半導體
    "記憶體半導體": {
        "moat_sources": "製程技術領先度、規模經濟",
        "valuation_focus": "景氣循環位置與庫存水位",
        "cycle_keyword": "記憶體價格週期與庫存去化進度",
    },
    # 電子零組件
    "電子零組件": {
        "moat_sources": "客戶黏著度、認證壁壘、交叉銷售能力",
        "valuation_focus": "客戶集中度與新客戶滲透進度",
        "cycle_keyword": "客戶庫存調整與新產品導入進度",
    },
    # 醫療器材
    "醫療器材": {
        "moat_sources": "法規認證壁壘、臨床黏著度、耗材循環",
        "valuation_focus": "耗材佔比與新市場開拓速度",
        "cycle_keyword": "法規進度與新市場認證時程",
    },
    # 光通訊
    "光通訊": {
        "moat_sources": "技術規格認證、超大規模雲端客戶進駐",
        "valuation_focus": "AI 基礎設施需求爆發與產能開出節奏",
        "cycle_keyword": "雲端資本支出能見度與產能開出時程",
    },
    # 電信服務 / IDC
    "電信服務": {
        "moat_sources": "基礎設施地位、牌照壁壘、客戶轉換成本",
        "valuation_focus": "IDC 稼動率與資本支出回收期",
        "cycle_keyword": "IDC 客戶進駐率與機房開出進度",
    },
    # 企業軟體
    "企業軟體／創意工具": {
        "moat_sources": "訂閱黏著度、工作流程嵌入深度、品牌溢價",
        "valuation_focus": "AI 功能對 ARPU 提升與用戶增長",
        "cycle_keyword": "AI 功能商業化進度與競爭替代風險",
    },
    # 金融科技
    "金融科技／支付": {
        "moat_sources": "網路效應、法規牌照、切換成本",
        "valuation_focus": "支付量成長動能與費率壓力",
        "cycle_keyword": "支付競爭格局變化與 fintech 替代風險",
    },
    # 能源
    "液化天然氣": {
        "moat_sources": "長期合約鎖定、基礎設施稀缺性",
        "valuation_focus": "合約到期結構與現貨市場曝險",
        "cycle_keyword": "LNG 合約能見度與全球供需缺口",
    },
    "石油天然氣": {
        "moat_sources": "低成本儲量、資產品質",
        "valuation_focus": "盈虧平衡油價與資本配置效率",
        "cycle_keyword": "油價假設敏感度與現金回報政策",
    },
    "石油煉製": {
        "moat_sources": "煉製複雜度、化工整合程度",
        "valuation_focus": "裂解價差週期與中游資產穩定性",
        "cycle_keyword": "裂解價差趨勢與下游化工貢獻",
    },
    # 消費品
    "消費品／鞋類": {
        "moat_sources": "品牌力、產品差異化、授權延伸",
        "valuation_focus": "品牌熱度持續性與國際化滲透",
        "cycle_keyword": "潮流持續性風險與新品牌/平台競爭",
    },
    # IC 設計
    "IC 設計": {
        "moat_sources": "IP 積累、客戶設計導入深度",
        "valuation_focus": "產品線多元化與 AI 應用滲透",
        "cycle_keyword": "庫存去化與 AI 晶片需求成長動能",
    },
    # 電子製造服務
    "電子製造服務": {
        "moat_sources": "規模經濟、垂直整合深度",
        "valuation_focus": "毛利率改善空間與 EV/機器人新業務",
        "cycle_keyword": "AI 伺服器組裝份額與非消費電子多元化",
    },
}

DEFAULT_LENS = {
    "moat_sources": "競爭優勢來源、客戶黏著度、市場地位",
    "valuation_focus": "估值水位與長期報酬潛力",
    "cycle_keyword": "當前所處景氣或產品週期位置",
}


def _get_lens(industry: str) -> dict:
    """取得對應產業的研究鏡頭，找不到則用預設值"""
    for key, lens in INDUSTRY_LENS.items():
        if key in industry:
            return lens
    return DEFAULT_LENS


def _build_query_points(stock_data: dict, lens: dict) -> list[str]:
    """
    根據股票資料生成 3 個「請特別查明」的研究點。
    優先反映：建設期、轉機期、估值矛盾、護城河來源、景氣位置。
    """
    points = []
    category = stock_data.get("category", "")
    key_risks = stock_data.get("key_risks", "")
    hard_data = stock_data.get("hard_data_summary", "")
    backlog = stock_data.get("backlog_evidence", "")
    moat_level = stock_data.get("moat_level", "")

    # Point 1：護城河確認（依產業特性）
    moat_q = (
        f"{lens['moat_sources']}的實質強度"
        f"——現有護城河是否仍在強化或已開始侵蝕？"
    )
    if moat_level:
        moat_q += f"（目前初步判斷護城河強度：{moat_level}，請查明依據與反證）"
    points.append(moat_q)

    # Point 2：週期 / 特殊情境（依 category 調整）
    cycle_context = ""
    cycle_flags = {
        "建設期": "目前資本支出規模、完工時程與稼動率爬坡預期",
        "轉機期": "轉機觸發因子是否已落地，以及尚未確認的反證",
        "產能開出": "產能開出節奏、客戶認證進度與良率爬升曲線",
        "庫存調整": "庫存去化進度、下游需求回補時間點",
        "客戶進駐": "主力客戶進駐速度、未來訂單能見度",
        "景氣循環": f"{lens['cycle_keyword']}——現在位於景氣哪個階段？",
    }
    for flag, question in cycle_flags.items():
        if flag in category:
            cycle_context = question
            break

    if not cycle_context:
        cycle_context = f"{lens['cycle_keyword']}——當前所處位置對未來 2~3 年報酬的影響"

    if backlog:
        cycle_context += f"（已知線索：{backlog}，請查明最新進展）"
    points.append(cycle_context)

    # Point 3：估值錨點 + 風險 / 矛盾點
    valuation_q = f"{lens['valuation_focus']}——"
    if hard_data:
        valuation_q += f"以下數據中是否存在估值矛盾需要解釋：{hard_data}。"
    else:
        valuation_q += "請建立合理的估值區間，並說明主要假設與敏感度。"
    if key_risks:
        valuation_q += f"特別需確認的風險：{key_risks}。"
    points.append(valuation_q)

    return points


def design_research_prompt(stock_data: dict) -> str:
    """
    主函數：輸入股票資料，輸出 Gemini Deep Research 研究題目。

    stock_data 欄位（基本必填）：
        stock_id, company_name, market, industry

    stock_data 欄位（選填，有助於生成更精準題目）：
        category        — 所處情境（建設期、轉機期、景氣循環、庫存調整等）
        moat_level      — 護城河強度初步判斷（強/中/弱）
        hard_data_summary — 已知硬數據摘要（EPS、ROE、FCF 等）
        key_risks       — 主要風險提示
        backlog_evidence — 訂單/客戶進駐等前置指標線索
    """
    ticker = stock_data.get("stock_id", "")
    company = stock_data.get("company_name", ticker)
    market = stock_data.get("market", "TW")
    industry = stock_data.get("industry", "")

    lens = _get_lens(industry)
    points = _build_query_points(stock_data, lens)

    # 組裝研究題目（固定格式）
    header = (
        f"請對 {company}（{ticker}.{market}）做一份價值投資導向的 Deep Research。\n"
        f"研究重點請依序放在：先看護城河，再看價格與長期報酬，"
        f"最後整理若進場應較接近追蹤倉、分批倉還是核心倉的證據基礎。\n"
        f"重點範圍：{industry}領域——{lens['valuation_focus']}。\n"
        f"請特別查明："
    )

    body = "\n".join(f"{i+1}. {p}" for i, p in enumerate(points))

    footer = (
        "\n最後請用研究底稿形式輸出，不要直接給買賣建議，"
        "並保留來源、反證、矛盾點與資料不足之處。"
    )

    return f"{header}\n{body}{footer}"
