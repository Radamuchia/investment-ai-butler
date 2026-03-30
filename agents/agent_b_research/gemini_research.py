"""
Agent B — Gemini Deep Research 自動化核心
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import Page
from .browser import BrowserManager

GEMINI_URL = "https://gemini.google.com"
RESEARCH_TIMEOUT = int(os.getenv("RESEARCH_TIMEOUT", "600")) * 1000  # 轉毫秒


def build_research_prompt(stock_data: dict) -> str:
    """
    組裝結構化研究提示詞

    stock_data 範例：
    {
        "stock_id": "2330",
        "company_name": "台積電",
        "industry": "半導體",
        "eps": 32.3,
        "roe": 26.5,
        "gross_margin": 53.2,
        "revenue_yoy": 15.3,
        "fcf": 800,
        "interest_rate": 4.5,
        "cpi": 2.8
    }
    """
    return f"""
請針對以下股票進行深度研究分析：

【股票資訊】
公司名稱：{stock_data.get('company_name', 'N/A')}（{stock_data.get('stock_id', 'N/A')}）
產業別：{stock_data.get('industry', 'N/A')}

【最新財務數據】
- EPS：{stock_data.get('eps', 'N/A')} 元
- ROE（股東權益報酬率）：{stock_data.get('roe', 'N/A')}%
- 毛利率：{stock_data.get('gross_margin', 'N/A')}%
- 營收年成長率（YoY）：{stock_data.get('revenue_yoy', 'N/A')}%
- 自由現金流：{stock_data.get('fcf', 'N/A')} 億元

【總體經濟環境】
- 當前基準利率：{stock_data.get('interest_rate', 'N/A')}%
- CPI 通膨率：{stock_data.get('cpi', 'N/A')}%

【請進行以下深度研究】
1. 公司核心競爭優勢與護城河分析（品牌、技術、規模、轉換成本）
2. 產業趨勢分析與主要競爭對手比較
3. 財務健康度全面評估（獲利能力、成長性、負債結構）
4. 主要風險因素識別（產業風險、公司風險、總經風險）
5. 長期投資價值評估（3~5 年展望）
6. 綜合投資建議

請以繁體中文回覆，並提供具體數據佐證。
""".strip()


class GeminiResearcher:
    """Gemini Deep Research 操作核心"""

    def __init__(self):
        self.browser_manager = BrowserManager()

    async def research(self, stock_data: dict) -> dict:
        """
        執行 Deep Research 並回傳研究報告

        回傳格式：
        {
            "stock_id": "2330",
            "report": "研究報告內容...",
            "generated_at": "2026-03-30T15:00:00",
            "status": "success" | "failed",
            "error": None | "錯誤訊息"
        }
        """
        stock_id = stock_data.get("stock_id", "unknown")
        result = {
            "stock_id": stock_id,
            "report": None,
            "generated_at": datetime.now().isoformat(),
            "status": "failed",
            "error": None,
        }

        try:
            context = await self.browser_manager.start()
            page = await self.browser_manager.new_page()

            prompt = build_research_prompt(stock_data)
            report = await self._run_deep_research(page, prompt, stock_id)

            result["report"] = report
            result["status"] = "success"
            print(f"[B] ✅ {stock_id} 研究報告生成完成")

        except Exception as e:
            result["error"] = str(e)
            print(f"[B] ❌ {stock_id} 研究失敗：{e}")

        finally:
            await self.browser_manager.close()

        return result

    async def _run_deep_research(self, page: Page, prompt: str, stock_id: str) -> str:
        """核心自動化流程"""

        # ── Step 1：開啟 Gemini ──────────────────────────────
        print(f"[B] Step 1：開啟 Gemini...")
        await page.goto(GEMINI_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # ── Step 2：嘗試點擊 Deep Research 模式 ─────────────
        print(f"[B] Step 2：尋找 Deep Research 入口...")
        await self._enter_deep_research_mode(page)

        # ── Step 3：輸入研究提示詞 ──────────────────────────
        print(f"[B] Step 3：輸入研究提示詞...")
        await self._input_prompt(page, prompt)

        # ── Step 4：等待報告生成 ─────────────────────────────
        print(f"[B] Step 4：等待 Deep Research 生成中（最長 {RESEARCH_TIMEOUT//1000} 秒）...")
        report = await self._wait_for_report(page)

        return report

    async def _enter_deep_research_mode(self, page: Page):
        """
        進入 Deep Research 模式
        正確流程（從截圖確認）：
          1. 點擊輸入框底部的「工具」按鈕
          2. 在彈出選單中點擊「Deep Research」
        """

        # ── 先確認是否已經在 Deep Research 模式 ────────────────
        # （畫面上顯示 "Deep Research ×" chip 代表已啟用）
        try:
            chip = page.locator("text=Deep Research").first
            if await chip.is_visible(timeout=2000):
                print("[B] Deep Research 已啟用 ✅（偵測到 chip）")
                return
        except Exception:
            pass

        # ── Step A：點擊「工具」按鈕 ────────────────────────────
        print("[B] 點擊「工具」按鈕...")
        tool_selectors = [
            "button:has-text('工具')",
            "[aria-label*='工具']",
            "text=工具",
        ]

        tool_clicked = False
        for selector in tool_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    tool_clicked = True
                    print(f"[B] 「工具」按鈕點擊成功 ✅")
                    break
            except Exception:
                continue

        if not tool_clicked:
            await page.screenshot(path=f"debug_no_tool_btn_{datetime.now().strftime('%H%M%S')}.png")
            print("[B] ⚠️ 找不到「工具」按鈕，截圖已儲存")
            return

        # ── Step B：在選單中點擊「Deep Research」───────────────
        print("[B] 在選單中點擊「Deep Research」...")
        dr_selectors = [
            "text=Deep Research",
            "[aria-label*='Deep Research']",
            "li:has-text('Deep Research')",
            "div[role='menuitem']:has-text('Deep Research')",
        ]

        for selector in dr_selectors:
            try:
                item = page.locator(selector).first
                if await item.is_visible(timeout=3000):
                    await item.click()
                    await page.wait_for_timeout(1500)
                    print("[B] Deep Research 模式啟用 ✅")
                    return
            except Exception:
                continue

        await page.screenshot(path=f"debug_no_dr_menu_{datetime.now().strftime('%H%M%S')}.png")
        print("[B] ⚠️ 找不到選單中的 Deep Research，截圖已儲存")

    async def _input_prompt(self, page: Page, prompt: str):
        """在 Gemini 輸入框填入提示詞"""
        # Deep Research 啟用後 placeholder 變成「你想研究什麼？」
        # 優先嘗試 rich text editor，再 fallback 到一般 textarea
        input_selectors = [
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
            "textarea",
            "[role='textbox']",
            "p[data-placeholder]",
        ]

        for selector in input_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=3000):
                    await element.click()
                    await element.fill(prompt)
                    await page.wait_for_timeout(1000)
                    await page.keyboard.press("Enter")
                    print(f"[B] 提示詞輸入完成 ✅")
                    return
            except Exception:
                continue

        raise Exception("找不到 Gemini 輸入框")

    async def _wait_for_report(self, page: Page) -> str:
        """等待報告生成並擷取內容"""

        # 等待「生成中」狀態消失（代表完成）
        loading_selectors = [
            "[aria-label*='loading']",
            "[data-test-id='loading']",
            "text=研究中",
            "text=Researching",
        ]

        # 先等待載入開始
        await page.wait_for_timeout(5000)

        # 持續檢查是否完成
        max_wait = RESEARCH_TIMEOUT
        interval = 10000  # 每 10 秒檢查一次
        elapsed = 0

        while elapsed < max_wait:
            await page.wait_for_timeout(interval)
            elapsed += interval

            minutes = elapsed // 60000
            seconds = (elapsed % 60000) // 1000
            print(f"[B] 等待中... {minutes}分{seconds}秒")

            # 嘗試擷取報告內容
            content = await self._extract_report(page)
            if content and len(content) > 200:
                return content

        # 超時仍嘗試擷取
        content = await self._extract_report(page)
        if content:
            return content

        raise Exception(f"Deep Research 超過 {RESEARCH_TIMEOUT//1000} 秒仍未完成")

    async def _extract_report(self, page: Page) -> str:
        """擷取頁面上的報告文字"""
        report_selectors = [
            ".response-content",
            "[data-message-author-role='model']",
            ".model-response",
            "article",
        ]

        for selector in report_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    # 取最後一個（最新的回應）
                    last = elements.nth(count - 1)
                    text = await last.inner_text()
                    if text and len(text) > 100:
                        return text
            except Exception:
                continue

        return None
