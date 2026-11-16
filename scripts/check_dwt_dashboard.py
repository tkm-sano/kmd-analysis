"""Actual Chrome operation against the completed DWT dashboard, no solver calls."""
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'output/toc_delivery/dwt_balance_20261113_v1/revision_1_3_1')
url = sys.argv[2] if len(sys.argv) > 2 else 'http://127.0.0.1:8767/'
raw = json.loads((root / 'ALL_TRIALS.json').read_text())
rows = [r for r in raw if r['phase'] in ('limited', 'baseline', 'control')]
valid = [r for r in rows if r['status'] == 'COMPLETE']
front = json.loads((root / 'THREE_OBJECTIVE_EVALUATION.json').read_text())['front_trial_ids']
checks = []
screenshots = root / 'screenshots'
screenshots.mkdir(exist_ok=True)


def check(name, value):
    checks.append({'check': name, 'passed': bool(value)})


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
                                 args=['--no-sandbox', '--disable-dev-shm-usage'])
    page = browser.new_page(viewport={'width': 1500, 'height': 1100})
    errors, external = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: external.append(r.url) if not r.url.startswith((url, 'data:')) else None)
    page.goto(url, wait_until='networkidle', timeout=60000)
    check('all registered final/failed rows displayed', page.locator('#results tr').count() == len(rows) + 1)
    check('front membership identical', page.locator('#results tr.front').count() == len(front))
    check('only actually complete plans selectable', page.locator('#trial option').count() == len(valid))
    check('A human time boundary visible', '人手T' in page.locator('main').inner_text())
    for m in ['A', 'B', 'C', 'D', 'D_CLASSICAL_CONTROL']:
        candidate = next((r for r in valid if r['method'] == m), None)
        if candidate is None:
            check('no fabricated selectable plan:' + m, not any(m == r['method'] for r in valid))
            continue
        page.locator('#trial').select_option(candidate['trial_id'])
        page.wait_for_function('(trialId)=>document.querySelector("#details").textContent.startsWith(trialId)', arg=candidate['trial_id'])
        expected = json.loads(Path(candidate['trial_directory'], 'plan.json').read_text())
        check(m + ':actual GeoJSON/Gantt trip count', page.locator('#gantt svg rect').count() == len(expected['trips']))
        check(m + ':nonempty real road drawing', page.evaluate('Array.from(document.querySelector("#map").getContext("2d").getImageData(0,0,1300,480).data).some(x=>x!==0)'))
        vehicle = expected['trips'][0]['vehicle_id']
        page.locator('#vehicle').select_option(vehicle)
        check(m + ':vehicle filtering', page.locator('#gantt svg rect').count() == sum(t['vehicle_id'] == vehicle for t in expected['trips']))
        page.locator('#trip').select_option('1')
        check(m + ':trip filtering', page.locator('#gantt svg rect').count() == sum(t['vehicle_id'] == vehicle and t['trip_no'] == 1 for t in expected['trips']))
        page.locator('#vehicle').select_option('all')
        page.locator('#trip').select_option('all')
    check('three figures load', page.locator('.figs img').evaluate_all('(imgs)=>imgs.length===3&&imgs.every(x=>x.complete&&x.naturalWidth>0)'))
    page.screenshot(path=str(screenshots / '01_DWT_dashboard.png'), full_page=True)
    check('no JS errors', not errors)
    check('no external services', not external)
    result = {'checks': len(checks), 'passed': sum(x['passed'] for x in checks),
              'failed': [x for x in checks if not x['passed']], 'details': checks,
              'javascript_errors': errors, 'external_requests': external, 'browser': browser.version}
    browser.close()
(root / 'BROWSER_VALIDATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(result['passed'], result['checks'])
if result['failed']:
    raise SystemExit(1)
