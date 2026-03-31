"""
Agent B — Gemini Deep Research 自動化核心
Selectors 來源：Playwright Codegen 錄製（2026-03-31）
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import Page
from .browser import BrowserManager
from .prompt_designer import design_research_prompt

GEMINI_URL = "https://gemini.google.com/app"
RESEARCH_TIMEOUT = int(os.getenv("RESEARCH_TIMEOUT", "5400"))  # 秒（預設 90 分鐘）
REPORT_MIN_CHARS = int(os.getenv("REPORT_MIN_CHARS", "3000"))   # 報告最少字數


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
            await self.browser_manager.start()
            page = await self.browser_manager.new_page()

            prompt = design_research_prompt(stock_data)
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
        """核心自動化流程（依 Codegen 錄製順序）"""

        # ── Step 1：開啟 Gemini ──────────────────────────────
        print("[B] Step 1：開啟 Gemini...")
        await page.goto(GEMINI_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # ── Step 2：確認使用 PRO 模式 ────────────────────────
        print("[B] Step 2：確認 PRO 模式...")
        await self._ensure_pro_mode(page)

        # ── Step 3：進入 Deep Research 模式 ─────────────────
        print("[B] Step 3：啟動 Deep Research...")
        await self._enter_deep_research_mode(page)

        # ── Step 4：輸入研究提示詞並傳送 ──────────────────────
        print("[B] Step 4：輸入研究提示詞...")
        await self._input_prompt(page, prompt)

        # ── Step 5：等待研究計畫並點擊「開始研究」────────────────
        print("[B] Step 5：確認開始研究...")
        await self._confirm_start_research(page)

        # ── Step 6：等待研究完成並擷取報告 ──────────────────────
        print("[B] Step 6：等待 Deep Research 完成（約 10~15 分鐘）...")
        report = await self._wait_for_report(page)

        return report

    async def _ensure_pro_mode(self, page: Page):
        """
        確認目前使用 PRO 模式
        Codegen 錄製：
          1. click [data-test-id="bard-mode-menu-button"]
          2. click [data-test-id="bard-mode-option-pro"]
        """
        # 讀取目前模式文字
        current_mode = await page.evaluate("""
            () => {
                const btn = document.querySelector('[data-test-id="bard-mode-menu-button"]');
                return btn ? btn.textContent.trim() : null;
            }
        """)
        print(f"[B] 目前模式：{current_mode}")

        # 已是 PRO 則跳過
        pro_keywords = ['pro', 'Pro', 'PRO', '2.5 Pro']
        if current_mode and any(kw in current_mode for kw in pro_keywords):
            print("[B] 已是 PRO 模式 ✅")
            return

        # 點擊模式選單按鈕
        print("[B] 切換至 PRO 模式...")
        await page.locator('[data-test-id="bard-mode-menu-button"]').click()
        await page.wait_for_timeout(1000)

        # 直接點擊 PRO 選項（Codegen 錄製到的精確 selector）
        await page.locator('[data-test-id="bard-mode-option-pro"]').click()
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
        Codegen 錄製：
          1. get_by_role("button", name="工具", exact=True).click()
          2. get_by_role("menuitemcheckbox", name="Deep Research").click()
        """
        # 點擊「工具」按鈕
        print("[B] 點擊「工具」按鈕...")
        await page.get_by_role("button", name="工具", exact=True).click()
        await page.wait_for_timeout(1500)

        # 點擊「Deep Research」選項
        print("[B] 選擇「Deep Research」...")
        await page.get_by_role("menuitemcheckbox", name="Deep Research").click()
        await page.wait_for_timeout(1500)

        print("[B] Deep Research 模式啟用 ✅")

    async def _input_prompt(self, page: Page, prompt: str):
        """
        在 Gemini 輸入框填入提示詞並傳送
        Codegen 錄製：
          1. locator(".ql-clipboard").fill(prompt)   ← Quill 編輯器
          2. get_by_role("button", name="傳送訊息").click()
        """
        print("[B] 填入提示詞...")

        # 方法 A：Codegen 錄製的 .ql-clipboard（Quill 編輯器）
        try:
            clipboard = page.locator(".ql-clipboard")
            if await clipboard.count() > 0:
                await clipboard.fill(prompt)
                await page.wait_for_timeout(800)
                print("[B] 提示詞填入完成（.ql-clipboard）✅")
            else:
                raise Exception("找不到 .ql-clipboard")
        except Exception:
            # 方法 B：fallback 到 .ql-editor
            print("[B] fallback 到 .ql-editor...")
            editor = page.locator(".ql-editor").first
            await editor.click()
            await editor.fill(prompt)
            await page.wait_for_timeout(800)
            print("[B] 提示詞填入完成（.ql-editor）✅")

        # 點擊「傳送訊息」按鈕（Codegen 錄製）
        print("[B] 點擊「傳送訊息」...")
        await page.get_by_role("button", name="傳送訊息").click()
        await page.wait_for_timeout(2000)
        print("[B] 訊息已傳送 ✅")

    async def _confirm_start_research(self, page: Page):
        """
        等待研究計畫出現，點擊「開始研究」確認按鈕
        Codegen 錄製：
          locator('[data-test-id="confirm-button"]').click()
        """
        print("[B] 等待研究計畫生成（約 8 秒）...")
        await page.wait_for_timeout(8000)

        # 等待 confirm-button 出現（最多 30 秒）
        try:
            confirm_btn = page.locator('[data-test-id="confirm-button"]')
            await confirm_btn.wait_for(state="visible", timeout=30000)
            await confirm_btn.click()
            print("[B] 「開始研究」已點擊 ✅")
        except Exception as e:
            # 截圖方便除錯
            await page.screenshot(
                path=f"debug_confirm_{datetime.now().strftime('%H%M%S')}.png"
            )
            print(f"[B] ⚠️ 找不到 confirm-button：{e}，嘗試 Tab × 6 備援...")

            # 備援：Tab × 6 + Enter（用戶確認的方式）
            await page.mouse.click(740, 360)
            await page.wait_for_timeout(500)
            for _ in range(6):
                await page.keyboard.press("Tab")
                await page.wait_for_timeout(300)
            await page.keyboard.press("Enter")
            print("[B] 備援 Tab × 6 + Enter 完成 ✅")

        await asyncio.sleep(3)

    async def _wait_for_report(self, page: Page) -> str:
        """
        等待 Deep Research 完成並擷取最終報告

        Deep Research 的生命週期：
          Phase 1（約 10 秒）：顯示研究計畫 → 已在 _confirm_start_research 處理
          Phase 2（約 10~15 分鐘）：實際研究進行中
          Phase 3：研究完成，顯示完整報告
        判斷完成：頁面出現完成通知 或 報告內容超過 2000 字
        """
        interval = 30   # 每 30 秒檢查一次
        elapsed = 0

        while elapsed < RESEARCH_TIMEOUT:
            await asyncio.sleep(interval)  # asyncio.sleep：不依賴 page，不受導航影響
            elapsed += interval
            minutes = elapsed // 60
            seconds = elapsed % 60

            try:
                status = await page.evaluate("""
                    () => {
                        const text = document.body.innerText || '';

                        // ── 進行中判斷：有 spinner 元素 或 進行中文字 ──
                        const hasSpinner = !![
                            '[class*="spinner"]',
                            '[class*="loading"]',
                            '[aria-label*="載入"]',
                            '[aria-label*="loading"]',
                            '[aria-busy="true"]',
                        ].find(sel => document.querySelector(sel));

                        const busyKw = [
                            '正在研究', 'Researching',
                            '搜尋中', 'Searching',
                            '研究網站',
                        ];
                        const hasBusyText = busyKw.some(kw => text.includes(kw));

                        // ── 完成判斷：Gemini 完成後固定顯示的句子 ──
                        // ⚠️ 不可用「已完成」（研究步驟進行中也會出現）
                        const doneKw = [
                            '我已經完成研究',     // Gemini 完成後的固定回覆（繁中）
                            'I\'ve finished',    // 英文版
                            'Research complete', // 英文備用
                        ];
                        const isDone = doneKw.some(kw => text.includes(kw));

                        return {
                            isBusy: hasSpinner || hasBusyText,
                            isDone,
                        };
                    }
                """)
            except Exception:
                print(f"[B] 研究中... {minutes}分{seconds}秒（頁面暫時無法讀取）")
                continue

            if status['isDone']:
                print(f"[B] ✅ 偵測到「研究完成」通知（{minutes}分{seconds}秒），等待渲染...")
                await asyncio.sleep(5)
                content = await self._extract_report(page)
                if content and len(content) > REPORT_MIN_CHARS:
                    return content
                # 報告還在渲染，繼續等
                print(f"[B] 報告渲染中（目前 {len(content) if content else 0} 字），繼續等待...")
                continue

            if status['isBusy']:
                print(f"[B] 研究進行中... {minutes}分{seconds}秒")
                continue

            # isBusy=False 且 isDone=False → 嘗試字數判斷（可能完成但沒有通知字樣）
            content = await self._extract_report(page)
            if content and len(content) > REPORT_MIN_CHARS:
                print(f"[B] ✅ 報告完成（字數判斷：{len(content)} 字，{minutes}分{seconds}秒）")
                return content

            print(f"[B] 等待中... {minutes}分{seconds}秒")

        # 擷取最終報告
        print("[B] 擷取最終報告...")
        content = await self._extract_report(page)
        if content:
            return content

        raise Exception(f"Deep Research 超過 {RESEARCH_TIMEOUT} 秒仍未完成")

    def _clean_report(self, text: str) -> str:
        """
        移除報告頂部的 UI 按鈕文字（目錄、分享及匯出、建立）
        研究過程的思考步驟（Researching websites...）保留，可作參考
        """
        import re
        # 移除頂部 UI 按鈕列：「標題\n目錄\n分享及匯出\n建立\n」
        ui_header = r'^[^\n]*\n目錄\n分享及匯出\n建立\n'
        text = re.sub(ui_header, '', text, count=1)
        return text.strip()

    async def _extract_report(self, page: Page) -> str:
        """
        擷取 Deep Research 完成後右側面板的報告文字
        Gemini 完成後報告顯示在右側獨立面板（非左側聊天區）
        """
        # ── 優先：針對右側報告面板的 selector ──────────────────
        report_selectors = [
            # ✅ 確認有效（Chrome 實測 2026-03-31）
            "deep-research-immersive-panel",
            # 備用
            "response-container",
            ".response-container",
            "[class*='deep-research']",
            "[class*='report-content']",
            "[class*='research-report']",
            # 一般 Gemini response selector
            ".response-content",
            "[data-message-author-role='model']",
            ".model-response",
            "model-response",
            "article",
            "[class*='markdown']",
        ]

        for selector in report_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    last = elements.nth(count - 1)
                    text = await last.inner_text()
                    if text and len(text) > REPORT_MIN_CHARS:
                        text = self._clean_report(text)
                        print(f"[B] 報告擷取成功（{selector}，{len(text)} 字）")
                        return text
            except Exception:
                continue

        # ── JS fallback：找頁面上最長的文字區塊（排除左側聊天） ──
        print("[B] 嘗試 JS fallback 擷取右側面板...")
        try:
            text = await page.evaluate("""
                () => {
                    // 取所有葉子層級的大型文字容器，通常報告在最大的一塊
                    const candidates = [...document.querySelectorAll(
                        'div, section, article, main'
                    )];
                    let best = { len: 0, text: '' };
                    for (const el of candidates) {
                        // 跳過有大量子元素的容器（是版面節點，不是內容節點）
                        if (el.children.length > 20) continue;
                        const t = (el.innerText || '').trim();
                        if (t.length > best.len && t.length < 500000) {
                            best = { len: t.length, text: t };
                        }
                    }
                    return best.text;
                }
            """)
            if text and len(text) > REPORT_MIN_CHARS:
                print(f"[B] JS fallback 擷取成功（{len(text)} 字）")
                return text
        except Exception as e:
            print(f"[B] JS fallback 失敗：{e}")

        # ── 最終 fallback：整頁文字（去除雜訊） ──────────────────
        print("[B] 嘗試擷取整頁文字...")
        try:
            text = await page.evaluate("() => document.body.innerText")
            if text and len(text) > REPORT_MIN_CHARS:
                print(f"[B] 整頁文字擷取（{len(text)} 字），儲存供人工確認")
                return text
        except Exception:
            pass

        # 截圖方便除錯
        await page.screenshot(
            path=f"debug_extract_{datetime.now().strftime('%H%M%S')}.png"
        )
        print("[B] ⚠️ 所有擷取方法失敗，已儲存截圖")
        return None
