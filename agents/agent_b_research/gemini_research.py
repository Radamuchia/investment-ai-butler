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

        # ── Step 2：確認使用 PRO 模式（非快捷/複雜）────────────
        print(f"[B] Step 2：確認 PRO 模式...")
        await self._ensure_pro_mode(page)

        # ── Step 3：進入 Deep Research 模式 ─────────────────
        print(f"[B] Step 3：啟動 Deep Research...")
        await self._enter_deep_research_mode(page)

        # ── Step 4：輸入研究提示詞 ──────────────────────────
        print(f"[B] Step 4：輸入研究提示詞...")
        await self._input_prompt(page, prompt)

        # ── Step 5：等待研究計畫出現並確認，再等最終報告 ────────
        print(f"[B] Step 5：等待 Deep Research 完成（約 10~15 分鐘）...")
        report = await self._wait_for_report(page)

        return report

    async def _ensure_pro_mode(self, page: Page):
        """
        確認目前使用 PRO 模式
        模式順序（用戶確認）：快捷 > 思考型 > pro
        切換方式：點擊模式按鈕 → ArrowDown × 2 → Enter
        注意：此 dropdown 只能用 ArrowDown，不能用 Tab
        """
        # 取得目前模式文字
        current_mode = await page.evaluate("""
            () => {
                const btn = document.querySelector('[data-test-id="bard-mode-menu-button"]');
                return btn ? btn.textContent.trim() : null;
            }
        """)
        print(f"[B] 目前模式：{current_mode}")

        # 已是 PRO 則跳過
        pro_keywords = ['pro', 'Pro', 'PRO', '2.5']
        if current_mode and any(kw in current_mode for kw in pro_keywords):
            print("[B] 已是 PRO 模式 ✅")
            return

        # 點擊模式選擇器按鈕（用座標點擊確保精準）
        print("[B] 切換至 PRO 模式（快捷 → ↓ → 思考型 → ↓ → pro）...")
        mode_pos = await page.evaluate("""
            () => {
                const btn = document.querySelector('[data-test-id="bard-mode-menu-button"]');
                if (!btn) return null;
                const r = btn.getBoundingClientRect();
                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
            }
        """)

        if not mode_pos:
            print("[B] ⚠️ 找不到模式選擇器，略過")
            return

        await page.mouse.click(mode_pos['x'], mode_pos['y'])
        await page.wait_for_timeout(1500)

        # 方法 A：ArrowDown × 2 → Enter（快捷 → 思考型 → pro）
        for _ in range(2):
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(400)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1500)

        # 確認切換成功
        new_mode = await page.evaluate("""
            () => {
                const btn = document.querySelector('[data-test-id="bard-mode-menu-button"]');
                return btn ? btn.textContent.trim() : null;
            }
        """)
        print(f"[B] 切換後模式：{new_mode} ✅")

    async def _enter_deep_research_mode(self, page: Page):
        """
        進入 Deep Research 模式
        流程：
          1. 用滑鼠座標精準點擊「工具」按鈕
          2. 等待下拉選單出現（2秒）
          3. 方法 A：用 getBoundingClientRect 找 Deep Research 座標後點擊
          4. 方法 B（備援）：重試最多 3 次，每次增加等待時間
        """

        # ── 確認是否已在 Deep Research 模式 ─────────────────────
        dr_rect = await page.evaluate("""
            () => {
                for (const el of document.querySelectorAll('*')) {
                    const rect = el.getBoundingClientRect();
                    if (
                        el.textContent.trim() === 'Deep Research' &&
                        rect.width > 0 && rect.height > 0 &&
                        el.closest('[class*="chip"], [class*="token"], [class*="badge"]')
                    ) {
                        return true;
                    }
                }
                return false;
            }
        """)
        if dr_rect:
            print("[B] Deep Research 已啟用 ✅")
            return

        # ── 取得「工具」按鈕的螢幕座標 ──────────────────────────
        print("[B] 取得「工具」按鈕位置...")
        tool_pos = await page.evaluate("""
            () => {
                const btns = [...document.querySelectorAll('button')];
                const btn = btns.find(b => b.textContent.trim() === '工具');
                if (!btn) return null;
                const r = btn.getBoundingClientRect();
                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
            }
        """)

        if not tool_pos:
            await page.screenshot(path=f"debug_no_tool_{datetime.now().strftime('%H%M%S')}.png")
            print("[B] ⚠️ 找不到「工具」按鈕")
            return

        # ── 點擊「工具」按鈕 ────────────────────────────────────
        print("[B] 點擊「工具」按鈕...")
        await page.mouse.click(tool_pos['x'], tool_pos['y'])
        await page.wait_for_timeout(2000)  # 等選單動畫完成

        # ── 方法 A：座標點擊 Deep Research ──────────────────────
        print("[B] 方法 A：尋找 Deep Research 座標...")
        dr_pos = await page.evaluate("""
            () => {
                for (const el of document.querySelectorAll('*')) {
                    const rect = el.getBoundingClientRect();
                    if (
                        el.textContent.trim() === 'Deep Research' &&
                        rect.width > 0 && rect.height > 0
                    ) {
                        return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
                    }
                }
                return null;
            }
        """)

        if dr_pos:
            await page.mouse.click(dr_pos['x'], dr_pos['y'])
            await page.wait_for_timeout(1500)
            print("[B] Deep Research 點擊成功（方法 A）✅")
            return

        # ── 方法 B：Tab × 3 + Enter（工具選單第3項）────────────
        # 用戶確認：點擊「工具」後，按 Tab 3 下可移至 Deep Research
        print("[B] 方法 B：Tab × 3 + Enter...")
        await page.screenshot(path=f"debug_before_tab_{datetime.now().strftime('%H%M%S')}.png")

        for _ in range(3):
            await page.keyboard.press("Tab")
            await page.wait_for_timeout(400)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1500)

        print("[B] Tab × 3 + Enter 完成 ✅")
        await page.screenshot(path=f"debug_after_tab_{datetime.now().strftime('%H%M%S')}.png")

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
        """
        等待 Deep Research 完成並擷取最終報告

        Deep Research 的生命週期：
          Phase 1（約 10 秒）：顯示「研究計畫」（研究網站清單）→ 不是最終報告
          Phase 2（約 5~10 分鐘）：實際研究進行中（頁面有 loading 動畫）
          Phase 3：研究完成，顯示完整報告 → 這才是我們要的

        判斷完成的依據：
          - 頁面上不再有「正在研究」、「研究網站」等進行中文字
          - 回應內容超過 2000 字（計畫只有幾百字，報告通常數千字）
        """

        # ── Phase 1：等待研究計畫出現，並自動點擊「確認」─────────
        print("[B] 等待 Deep Research 研究計畫出現...")
        await page.wait_for_timeout(8000)

        # ── 點擊空白處重置 Tab 焦點，再 Tab × 7 → Enter 選到「開始研究」──
        # 用戶確認：點空白處後按 Tab 7 次可選到「開始研究」
        print("[B] 點擊空白處重置焦點...")
        await page.mouse.click(100, 300)   # 左側空白區域
        await page.wait_for_timeout(500)

        print("[B] Tab × 7 → Enter 選取「開始研究」...")
        for i in range(7):
            await page.keyboard.press("Tab")
            await page.wait_for_timeout(300)
        await page.keyboard.press("Enter")

        confirmed = "開始研究"

        if confirmed:
            print(f"[B] 已點擊確認按鈕：「{confirmed}」✅，開始真正研究...")
            await page.wait_for_timeout(3000)
        else:
            print("[B] 未找到確認按鈕（可能不需要確認），繼續等待...")

        # ── Phase 2：等待完成通知，每 30 秒檢查一次 ─────────────
        # Deep Research 需要 10~15 分鐘，完成後會有通知
        max_wait = RESEARCH_TIMEOUT
        interval = 30000   # 每 30 秒檢查一次
        elapsed = 0

        while elapsed < max_wait:
            await page.wait_for_timeout(interval)
            elapsed += interval
            minutes = elapsed // 60000
            seconds = (elapsed % 60000) // 1000

            # 偵測完成通知 或 loading 消失
            status = await page.evaluate("""
                () => {
                    const text = document.body.innerText || '';

                    // 仍在研究中的關鍵字
                    const busyKw = ['研究網站', 'Researching', '正在研究', '搜尋中', 'Searching'];
                    const isBusy = busyKw.some(kw => text.includes(kw));

                    // 完成通知的關鍵字
                    const doneKw = ['研究完成', '已完成', 'Research complete', '查看報告'];
                    const isDone = doneKw.some(kw => text.includes(kw));

                    // 檢查 loading 動畫是否還在
                    const hasLoader = document.querySelector(
                        '[aria-label*="loading"], [class*="loading"], [class*="spinner"]'
                    );

                    return { isBusy, isDone, hasLoader: !!hasLoader };
                }
            """)

            if status['isDone']:
                print(f"[B] ✅ 偵測到完成通知！（{minutes}分{seconds}秒）")
                await page.wait_for_timeout(2000)
                break

            if status['isBusy'] or status['hasLoader']:
                print(f"[B] 研究進行中... {minutes}分{seconds}秒（預計 10~15 分鐘）")
                continue

            # 無 loading 也無完成通知 → 嘗試擷取看字數
            content = await self._extract_report(page)
            if content and len(content) > 2000:
                print(f"[B] ✅ 報告完成（{len(content)} 字，{minutes}分{seconds}秒）")
                return content

            print(f"[B] 等待中... {minutes}分{seconds}秒")

        # 擷取最終報告
        print("[B] 擷取最終報告...")
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
