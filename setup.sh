#!/bin/bash
# Agent B — 首次安裝設定腳本
# 執行方式：bash setup.sh

set -e

echo ""
echo "============================================"
echo "  Agent B — Gemini Deep Research 安裝設定"
echo "============================================"
echo ""

# ── 1. 檢查 Python ────────────────────────────────────
echo "▶ 檢查 Python 版本..."
python3 --version || { echo "❌ 請先安裝 Python 3.11+"; exit 1; }
echo ""

# ── 2. 建立虛擬環境 ───────────────────────────────────
if [ ! -d "venv" ]; then
    echo "▶ 建立虛擬環境..."
    python3 -m venv venv
else
    echo "✅ 虛擬環境已存在，跳過"
fi
echo ""

# ── 3. 安裝依賴套件 ───────────────────────────────────
echo "▶ 安裝 Python 套件..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ 套件安裝完成"
echo ""

# ── 4. 安裝 Playwright Chrome ─────────────────────────
echo "▶ 安裝 Playwright Chrome..."
playwright install chrome
echo "✅ Playwright Chrome 安裝完成"
echo ""

# ── 5. 建立 .env ──────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ 已建立 .env（可依需求調整設定）"
else
    echo "✅ .env 已存在，跳過"
fi
echo ""

# ── 6. 首次 Google 登入 ───────────────────────────────
echo "============================================"
echo "  最後步驟：Google 帳號登入"
echo "============================================"
echo ""
echo "  即將開啟 Chrome 瀏覽器，請："
echo "  1. 登入你的 Google 帳號（需有 Gemini Pro）"
echo "  2. 確認可以正常使用 Gemini"
echo "  3. 回到此視窗按下 Enter"
echo ""
read -p "  按下 Enter 開始登入流程..." -r
echo ""

python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from agents.agent_b_research.browser import BrowserManager

async def first_login():
    bm = BrowserManager()
    await bm.start()
    print('')
    print('  ✅ Chrome 已開啟，請完成 Google 登入')
    print('  完成後回到此視窗按下 Enter...')
    input()
    await bm.close()
    print('  ✅ 登入 session 已儲存')

asyncio.run(first_login())
"

echo ""
echo "============================================"
echo "  ✅ 安裝完成！"
echo "============================================"
echo ""
echo "  開始研究股票："
echo "  source venv/bin/activate"
echo "  python run_research.py --stock 2330"
echo ""
