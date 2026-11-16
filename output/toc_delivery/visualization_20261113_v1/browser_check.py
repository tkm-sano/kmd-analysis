"""Operate the actual local dashboard in Chrome, including lazy saved OD paths."""
import csv
import json
import time
import urllib.request
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
SOURCE=REPO/'output/toc_delivery/ad_pipeline_20261112_route_v2'
checks=[]


def check(name,ok):checks.append({'check':name,'passed':bool(ok)})


def main():
    samples=[]
    for case in ['S1','S2','S3']:
        n={'S1':1000,'S2':2000,'S3':4000}[case]
        d=np.load(SOURCE/'roads/inputs'/case/'od/distance_m.npy',mmap_mode='r');t=np.load(SOURCE/'roads/inputs'/case/'od/duration_s.npy',mmap_mode='r')
        for i,j in [(0,n),(n,0),(n//3,n//2),(n//2,n//3),(17,17)]:
            start=time.perf_counter()
            with urllib.request.urlopen(f'http://127.0.0.1:8765/api/route?case={case}&i={i}&j={j}',timeout=30) as response:r=json.load(response)
            ok=r['geometry_check']['passed'] and r['distance_m']==float(d[i,j]) and r['duration_s']==float(t[i,j])
            check(f'live saved OD API:{case}:{i}:{j}',ok)
            samples.append({'case':case,'i':i,'j':j,'distance_m':r['distance_m'],'duration_s':r['duration_s'],
                            'node_count':len(r['node_ids']),'geometry_delta_m':r['geometry_check']['delta_m'],'passed':ok,'elapsed_s':time.perf_counter()-start})
    with (ROOT/'OD_GEOMETRY_SAMPLE_VALIDATION.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(samples[0]));w.writeheader();w.writerows(samples)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,
                                 args=['--no-sandbox','--disable-dev-shm-usage','--enable-precise-memory-info'])
        page=browser.new_page(viewport={'width':1600,'height':1100},device_scale_factor=1)
        errors=[];external=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda req:external.append(req.url) if not req.url.startswith(('http://127.0.0.1:8765/','file:','data:')) else None)
        start=time.perf_counter();page.goto('http://127.0.0.1:8765/index.html',wait_until='networkidle',timeout=60000);page.wait_for_function('window.VIZ&&window.VIZ.ready')
        initial_s=time.perf_counter()-start;heap=page.evaluate('performance.memory.usedJSHeapSize')
        check('initial dashboard ready',page.evaluate('window.VIZ.ready'))
        for case,n in [('S1',1000),('S2',2000),('S3',4000)]:
            page.locator('#scenario').select_option(case)
            check('scenario point count:'+case,page.evaluate('VIZ.data.scenarios[VIZ.scenario].points.length')==n+1)
            check('OD KPI displayed:'+case,f'{n:,}' in page.locator('#od-kpis').inner_text())
        page.locator('#show-snaps').check();page.locator('#show-stops').uncheck();page.locator('#show-roads').uncheck()
        check('OD layer toggles operate',page.locator('#show-snaps').is_checked() and not page.locator('#show-stops').is_checked() and not page.locator('#show-roads').is_checked())
        page.locator('#show-stops').check();page.locator('#show-roads').check();page.locator('#od-plus').click()
        check('OD zoom operates',page.evaluate('VIZ.odMap.zoom')>1)
        page.locator('#od-fit').click();page.locator('#od-map').scroll_into_view_if_needed();rect=page.locator('#od-map').bounding_box()
        point=page.evaluate('VIZ.odMap.project([VIZ.data.scenarios.S3.points[0].lon,VIZ.data.scenarios.S3.points[0].lat])')
        page.mouse.click(rect['x']+point[0],rect['y']+point[1])
        check('point click shows real ID','KEIHIN_WEST_CENTRAL_ENTRANCE' in page.locator('#point-detail').inner_text())
        page.locator('#od-from').fill('123');page.locator('#od-to').fill('2750');page.locator('#load-od').click()
        page.wait_for_function("document.getElementById('od-result').textContent.includes('地点 123 → 2750')")
        check('arbitrary S3 OD loaded via UI','一致' in page.locator('#od-result').inner_text())
        page.screenshot(path=str(ROOT/'screenshots/01_OD_map_S3.png'),full_page=True)
        page.locator('[data-tab=quality]').click();page.locator('#quality-scenario').select_option('S3')
        check('full S3 OD total shown','16,008,001' in page.locator('#quality-kpis').inner_text())
        check('four diagnostic SVG plots',page.locator('#tab-quality .chart svg').count()==4)
        page.screenshot(path=str(ROOT/'screenshots/02_OD_diagnostics_S3.png'),full_page=True)
        page.locator('[data-tab=routes]').click()
        for m,D in [('B','444.1768'),('C','410.1098'),('D','444.1768')]:
            page.locator('#method').select_option(m)
            check('method saved D displayed:'+m,D in page.locator('#plan-kpis').inner_text())
        page.locator('#vehicle').select_option('v0');page.locator('#all-vehicles').uncheck();page.locator('#trip').select_option('1');page.locator('#visit-numbers').check()
        check('vehicle/trip filtering',page.evaluate("VIZ.shownTrips().every(t=>t.vehicle_id==='v0'&&t.trip_no===1)"))
        check('selected route has road vertices',page.evaluate('VIZ.shownTrips()[0].geometry.length')>2)
        page.locator('#trip').select_option('2')
        check('second trip/unused filter',page.evaluate('VIZ.shownTrips().every(t=>t.trip_no===2)'))
        page.locator('#trip').select_option('all');page.locator('#all-vehicles').check();page.locator('#visit-numbers').uncheck();page.locator('#match-labels').check()
        page.locator('#stage').select_option('seed')
        check('D saved seed stage selectable',page.evaluate('VIZ.shownTrips().length')==17)
        page.locator('#stage').select_option('final')
        check('BD matching result visible','不一致' in page.locator('#bd-summary').inner_text())
        check('pipeline missing records explicit','記録なし' in page.locator('#pipeline').inner_text())
        page.screenshot(path=str(ROOT/'screenshots/03_S1_D_routes_and_comparison.png'),full_page=True)
        page.locator('#method').select_option('C');page.locator('#all-vehicles').uncheck();page.locator('#vehicle').select_option('v3');page.locator('#visit-numbers').check()
        page.screenshot(path=str(ROOT/'screenshots/03b_S1_C_selected_vehicle.png'),full_page=True)
        page.locator('[data-tab=berths]').click()
        for m,W in [('B','285.75'),('C','342.00'),('D','285.75')]:
            page.locator('#gantt-method').select_option(m);check('gantt wait sum:'+m,W in page.locator('#berth-kpis').inner_text())
        page.locator('#gantt-method').select_option('C')
        check('all 17 trip event rows',page.locator('#event-table tbody tr').count()==17)
        check('gantt rectangles contain exact event tooltips',page.locator('#berth-gantt rect title').count()==17)
        page.screenshot(path=str(ROOT/'screenshots/04_S1_C_berth_gantt.png'),full_page=True)
        # Direct local-file opening: preloaded figures and default OD must work.
        page.goto((ROOT/'index.html').as_uri(),wait_until='load');page.wait_for_function('window.VIZ&&window.VIZ.ready')
        check('file URL basic dashboard works',page.evaluate('VIZ.ready'))
        page.locator('[data-tab=routes]').click();check('file URL comparison renders','444.1768' in page.locator('#plan-kpis').inner_text())
        page.set_viewport_size({'width':850,'height':1000});page.locator('[data-tab=od]').click();page.screenshot(path=str(ROOT/'screenshots/05_tablet_layout.png'),full_page=True)
        check('no browser JS errors',not errors);check('no external web requests',not external)
        browser_version=browser.version;browser.close()
    report={'checks':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],
            'details':checks,'javascript_errors':errors,'external_requests':external,'browser':browser_version,
            'initial_page_ready_wall_s':initial_s,'initial_used_JS_heap_bytes':heap,'OD_live_samples':len(samples),
            'screenshots':[p.name for p in (ROOT/'screenshots').glob('*.png')]}
    (ROOT/'BROWSER_VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='details'},ensure_ascii=False,indent=2))
    assert not report['failed']


if __name__=='__main__':main()
