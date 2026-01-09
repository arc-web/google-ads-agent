#!/bin/bash
# Quick script to run the campaign planning tool

echo "🚀 Running MyExpertResume Campaign Plan..."
echo "========================================"

cd "$(dirname "$0")"
python3 campaign_plan.py

echo ""
echo "✅ Campaign CSVs generated in ../campaigns/"
echo "📁 Files created:"
echo "   - myexpertresume_test_campaign_executive.csv (test campaign)"
echo "   - myexpertresume_campaign_export.csv (full campaign)"
echo ""
echo "💡 Next: Import CSV into Google Ads Editor"
