"""
Agent B — 瀏覽器管理模組
使用你現有的 Chrome 登入狀態，不需要重新登入 Gemini
"""

import os
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Chrome 用戶資料路徑（macOS 預設）
CHROME_USER_DATA_DIR = os.getenv(
    "CHROME_USER_DATA_DIR",
    os.path.expanduser("~/Library/Application Support/Google/Chrome")
)
CHROME_PROFILE = os.getenv("CHROME_PROFILE", "Default")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


class BrowserManager:
    """管理 Playwright Chrome 瀏覽器實例"""

    def __init__(self):
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None

    async def start(self):
        """啟動瀏覽器，繼承現有 Chrome 登入狀態"""
        self._playwright = await async_playwright().start()

        print(f"[B] 啟動 Chrome（headless={HEADLESS}）")
        print(f"[B] 使用 Chrome 用戶資料：{CHROME_USER_DATA_DIR}")

        # 使用 launch_persistent_context 繼承 Chrome 登入 Cookie
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=CHROME_USER_DATA_DIR,
            channel="chrome",           # 使用系統安裝的 Chrome
            headless=HEADLESS,
            args=[
                f"--profile-directory={CHROME_PROFILE}",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
        )

        print("[B] 瀏覽器啟動成功 ✅")
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
