#!/bin/bash
# 今晚台股研究一鍵啟動
# 執行方式：bash run_tonight.sh

cd ~/Documents/investment-ai-butler-agent-b
source venv/bin/activate

echo ""
echo "============================================"
echo "  AlphaButler — 台股夜間研究啟動"
echo "============================================"
echo "  股票：3023 4104 4107 6263 6561"
echo "  模式：背景執行（Chrome 不顯示視窗）"
echo "  Mac：研究期間防止睡眠"
echo "============================================"
echo ""

# 防止 Mac 睡眠（研究完成後自動解除）
caffeinate -i python run_research.py \
    --stock 3023 4104 4107 6263 6561 \
    --output ./reports

echo ""
echo "✅ 台股研究全部完成，報告在 ./reports/"
