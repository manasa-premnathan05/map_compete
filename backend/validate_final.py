import sys, ast, re
sys.stdout.reconfigure(encoding='utf-8')

# 1. Check analytics.js for stray closing brace (the critical bug)
with open('frontend/js/components/analytics.js', encoding='utf-8') as f:
    js = f.read()
lines = js.split('\n')
# Scan for the orphan } pattern (line 174 was the culprit)
print('=== analytics.js checks ===')
print(f'Total lines: {len(lines)}')
print(f'renderAICompetitiveIntelligence: {"OK" if "renderAICompetitiveIntelligence" in js else "MISSING"}')
print(f'runAIAnalysis: {"OK" if "runAIAnalysis" in js else "MISSING"}')
print(f'renderAnalyticsMarketGaps: {"OK" if "renderAnalyticsMarketGaps" in js else "MISSING"}')
# Check that initAnalytics closes properly (last line should be closing brace of the export function)
last_meaningful = [l for l in lines if l.strip()][-1]
print(f'Last non-empty line: {repr(last_meaningful)}')
# Count open/close braces to check balance
open_count = js.count('{') - js.count('${')
close_count = js.count('}')
print(f'Brace balance check: open={open_count}, close={close_count}, diff={open_count - close_count}')

# 2. Check ideas.js
with open('frontend/js/components/ideas.js', encoding='utf-8') as f:
    ijs = f.read()
print('\n=== ideas.js checks ===')
print(f'Total lines: {len(ijs.split(chr(10)))}')
print(f'renderAnalysisSummary: {"OK" if "renderAnalysisSummary" in ijs else "MISSING"}')
print(f'dedup logic: {"OK" if "existingIdeaTexts" in ijs else "MISSING"}')
print(f'copy-idea-btn: {"OK" if "copy-idea-btn" in ijs else "MISSING"}')
print(f'ideas-analysis-panel: {"OK" if "ideas-analysis-panel" in ijs else "MISSING"}')

# 3. Check ai_service.py models
with open('backend/ai_service.py') as f:
    aipy = f.read()
print('\n=== ai_service.py checks ===')
print(f'qwen model: {"OK" if "qwen/qwen3.8-27b" in aipy else "MISSING"}')
print(f'old llama decommissioned: {"OK (removed)" if "llama-3.1-8b-instant" not in aipy else "WARNING: still referenced"}')
print(f'openai/gpt-oss fallback: {"OK" if "openai/gpt-oss-20b" in aipy else "MISSING"}')

# 4. Check index.html new panels
with open('frontend/index.html', encoding='utf-8') as f:
    html = f.read()
print('\n=== index.html checks ===')
print(f'ideas-analysis-panel: {"OK" if "ideas-analysis-panel" in html else "MISSING"}')
print(f'ideas-results grid: {"OK" if "ideas-results" in html else "MISSING"}')
print(f'previous-ideas: {"OK" if "previous-ideas" in html else "MISSING"}')
print(f'module-gaps subnav: {"OK" if "module-gaps" in html else "MISSING"}')

print('\nAll checks complete.')
