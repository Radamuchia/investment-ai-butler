"""
Agent B — 瀏覽器管理模組
使用 Playwright 專屬 Chrome 個人資料夾，第一次需手動登入 Gemini
"""

import os
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Playwright 專屬 Chrome 資料夾（不與系統 Chrome 衝突）
PLAYWRIGHT_PROFILE_DIR = os.getenv(
    "PLAYWRIGHT_PROFILE_DIR",
    os.path.expanduser("~/Documents/investment-ai-butler-agent-b/.chrome-profile")
)
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


class BrowserManager:
    """管理 Playwright Chrome 瀏覽器實例"""

    def __init__(self):
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None

    async def start(self):
        """
        啟動瀏覽器
        - 第一次執行：Chrome 開啟後請手動登入 Google / Gemini
        - 之後執行：自動讀取已儲存的登入狀態
        """
        self._playwright = await async_playwright().start()

        is_first_run = not os.path.exists(PLAYWRIGHT_PROFILE_DIR)

        print(f"[B] 啟動 Chrome（headless={HEADLESS}）")
        print(f"[B] 專屬資料夾：{PLAYWRIGHT_PROFILE_DIR}")

        if is_first_run:
            print("[B] ⚠️  首次執行！請在瀏覽器中登入 Google 帳號後，關閉瀏覽器再重新執行腳本")

        # 使用獨立的 Playwright 專屬資料夾（不衝突系統 Chrome）
        # ignore_default_args 移除 --enable-automation 旗標，避免被 Google 偵測為機器人
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=PLAYWRIGHT_PROFILE_DIR,
            channel="chrome",
            headless=HEADLESS,
            ignore_default_args=["--enable-automation", "--disable-infobars"],
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-blink-features=AutomationControlled",
            ],
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
        )

        print("[B] 瀏覽器啟動成功 ✅")

        if is_first_run:
            # 首次執行：開啟 Google 登入頁面讓用戶手動登入
            page = await self._context.new_page()
            await page.goto("https://accounts.google.com")
            print("[B] 請在瀏覽器中完成 Google 登入，完成後直接關閉瀏覽器視窗")
            # 等待瀏覽器被手動關閉
            await self._context.wait_for_event("close", timeout=0)
            print("[B] 登入完成，請重新執行腳本 ✅")
            exit(0)

        return self._context

    async def new_page(self) -> Page:
        """開啟新分頁"""
        return await self._context.new_page()

    async def close(self):
        """關閉瀏覽器"""
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        print("[B] 瀏覽器已關閉")
