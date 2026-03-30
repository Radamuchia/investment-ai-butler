"""
Deep Research Selector 偵測腳本

執行後會：
1. 開啟 Gemini
2. 截圖儲存目前畫面
3. 用 JavaScript 掃描所有可互動元素
4. 印出與 Deep Research 相關的 selector 資訊

執行方式：
    cd ~/Documents/investment-ai-butler-agent-b
    source venv/bin/activate
    python debug_selector.py
"""

import asyncio
import json
from playwright.async_api import async_playwright

PLAYWRIGHT_PROFILE_DIR = "~/.local/share/investment-ai-butler/chrome-profile"
import os
PLAYWRIGHT_PROFILE_DIR = os.path.expanduser(
    "~/Documents/investment-ai-butler-agent-b/.chrome-profile"
)


async def main():
    async with async_playwright() as p:
        print("[DEBUG] 啟動 Chrome...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PLAYWRIGHT_PROFILE_DIR,
            channel="chrome",
            headless=False,
            ignore_default_args=["--enable-automation", "--disable-infobars"],
            args=[
                "--no-first-run",
                "--disable-blink-features=AutomationControlled",
            ],
            viewport={"width": 1280, "height": 900},
        )

        page = await context.new_page()

        # ── Step 1：開啟 Gemini ──────────────────────────────────
        print("[DEBUG] 開啟 Gemini...")
        await page.goto("https://gemini.google.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        # ── Step 2：截圖（看目前畫面長什麼樣）────────────────────
        screenshot_path = "debug_gemini_home.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"[DEBUG] 截圖已儲存：{screenshot_path}")

        # ── Step 3：JavaScript 掃描所有含關鍵字的元素 ─────────────
        print("\n[DEBUG] 掃描 Deep Research 相關元素...\n")

        results = await page.evaluate("""
            () => {
                const keywords = [
                    'deep research', 'deep_research', 'deepresearch',
                    '深度研究', 'research', 'Research'
                ];
                const found = [];
                const allElements = document.querySelectorAll('*');

                for (const el of allElements) {
                    const text = (el.textContent || '').trim().toLowerCase();
                    const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                    const dataAttr = el.getAttributeNames()
                        .map(a => `${a}="${el.getAttribute(a)}"`)
                        .join(' ');

                    for (const kw of keywords) {
                        if (
                            (text === kw.toLowerCase() || ariaLabel.includes(kw.toLowerCase()))
                            && el.offsetParent !== null  // 只找可見元素
                        ) {
                            found.push({
                                tag: el.tagName,
                                text: el.textContent.trim().substring(0, 80),
                                ariaLabel: el.getAttribute('aria-label'),
                                role: el.getAttribute('role'),
                                className: el.className.substring(0, 100),
                                id: el.id,
                                dataAttrs: el.getAttributeNames()
                                    .filter(a => a.startsWith('data-') || a.startsWith('jsname'))
                                    .map(a => `${a}="${el.getAttribute(a)}"`)
                                    .join(', ')
                            });
                            break;
                        }
                    }
                }
                return found;
            }
        """)

        if results:
            print(f"[DEBUG] 找到 {len(results)} 個相關元素：\n")
            for i, el in enumerate(results):
                print(f"  [{i+1}] TAG: {el['tag']}")
                print(f"       text: {el['text']}")
                print(f"       aria-label: {el['ariaLabel']}")
                print(f"       role: {el['role']}")
                print(f"       class: {el['className']}")
                print(f"       id: {el['id']}")
                print(f"       data-attrs: {el['dataAttrs']}")
                print()
        else:
            print("[DEBUG] ⚠️  找不到 Deep Research 相關元素")
            print("[DEBUG] 可能需要先點擊某個按鈕才會出現，請查看截圖")

        # ── Step 4：掃描所有按鈕與可點擊元素 ──────────────────────
        print("\n[DEBUG] 掃描頁面所有可見按鈕與工具列...\n")

        buttons = await page.evaluate("""
            () => {
                const els = document.querySelectorAll(
                    'button, [role="button"], mat-chip, [role="option"], [jsname]'
                );
                const visible = [];
                for (const el of els) {
                    if (el.offsetParent !== null && el.textContent.trim()) {
                        visible.push({
                            tag: el.tagName,
                            text: el.textContent.trim().substring(0, 60),
                            ariaLabel: el.getAttribute('aria-label'),
                            jsname: el.getAttribute('jsname'),
                            dataTestId: el.getAttribute('data-test-id'),
                            className: el.className.substring(0, 80),
                        });
                    }
                }
                return visible.slice(0, 40);  // 最多顯示 40 個
            }
        """)

        print(f"[DEBUG] 頁面可見互動元素（前40個）：\n")
        for i, btn in enumerate(buttons):
            print(f"  [{i+1}] {btn['tag']} | text='{btn['text']}' | "
                  f"aria='{btn['ariaLabel']}' | jsname='{btn['jsname']}' | "
                  f"data-test-id='{btn['dataTestId']}'")

        print(f"\n[DEBUG] 截圖路徑：{os.path.abspath(screenshot_path)}")
        print("[DEBUG] 請將截圖與以上資訊貼給 Claude 分析 ✅")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
