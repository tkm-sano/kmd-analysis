/* Real Chromium/CDP checks of the file:// artifact; no routing or demand writes. */
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const {spawn,execFileSync} = require('child_process');
const {WebSocket} = require('undici');
const {pathToFileURL} = require('url');
const root = process.cwd();
const review = path.join(root,process.argv[2] || 'review_outputs/toc_demand_map_20261110');
fs.mkdirSync(review,{recursive:true});
const html = path.join(root,'output/toc_delivery/demand_map/v1/toc_demand_S1_S3_map.html');
const pause = ms => new Promise(resolve=>setTimeout(resolve,ms));
const hash = s => crypto.createHash('sha256').update(s).digest('hex');
const csv = JSON.parse(execFileSync('python',['-B','-c',`import csv,json
from pathlib import Path
p=Path('03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1')
data={}
for s in ['S1','S2','S3']:
 with (p/(s+'.csv')).open(newline='') as f:data[s]=list(csv.DictReader(f))
print(json.dumps(data))`],{encoding:'utf8',maxBuffer:8*1024*1024}));
const ids1 = new Set(csv.S1.map(r=>r.stop_id)), ids2 = new Set(csv.S2.map(r=>r.stop_id));
const groupOf = id=>ids1.has(id)?1:ids2.has(id)?2:3;
const labels = {1:'S1',2:'S2追加分',3:'S3追加分'};
const sortRows = (a,b)=>Buffer.compare(Buffer.from(a[0]),Buffer.from(b[0]));
const expectedRows = s=>csv[s].map(r=>[r.stop_id,r.building_id,r.chocho_code,r.latitude,r.longitude,r.parcel_count,String(groupOf(r.stop_id))]).sort(sortRows);
const expectedHashes = Object.fromEntries(['S1','S2','S3'].map(s=>[s,hash(JSON.stringify(expectedRows(s)))]));
const profile = fs.mkdtempSync(path.join(os.tmpdir(),'toc-demand-map-browser-'));
const chrome = spawn('google-chrome',[
  '--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
  ...(process.argv.includes('--http1')?['--disable-quic','--disable-http2']:[]),
  '--disable-background-networking','--disable-component-update','--no-first-run',
  '--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--remote-allow-origins=*',
  '--window-size=1440,1000','--user-data-dir='+profile,'about:blank'],{stdio:['ignore','ignore','pipe']});
let browserLog='';chrome.stderr.on('data',d=>browserLog+=d.toString());
let socket,sequence=0;const pending=new Map(),exceptions=[];
const report={status:'RUNNING',browser:'',url:pathToFileURL(html).href,scenario_checks:[],popup_checks:[],exceptions,network_failures:[],tile_requests:0,http1_diagnostic:process.argv.includes('--http1')};
function assert(condition,message){if(!condition)throw new Error(message);}
async function command(method,params={}){
  const id=++sequence;
  return new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout: '+method));},20000);
    pending.set(id,{resolve:v=>{clearTimeout(timeout);resolve(v)},reject:e=>{clearTimeout(timeout);reject(e)}});
    socket.send(JSON.stringify({id,method,params}));
  });
}
async function evaluate(expression){
  const result=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  if(result.exceptionDetails)throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function ready(previousTimeOrigin){
  for(let i=0;i<150;i++){
    try {if(await evaluate(`!!window.tocDemandMap && ${previousTimeOrigin===undefined?'true':'performance.timeOrigin !== '+previousTimeOrigin}`))return;}
    catch(e){}
    await pause(100);
  }
  throw new Error('Map did not initialize');
}
async function draw(){await evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');}
async function clickSelector(selector){
  const point=await evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  await clickPoint(point.x,point.y);
}
async function clickPoint(x,y){
  await command('Input.dispatchMouseEvent',{type:'mouseMoved',x,y});
  await command('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',buttons:1,clickCount:1});
  await command('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',buttons:0,clickCount:1});
  await draw();
}
async function scenarioCheck(level,offline){
  const start=Date.now();
  await clickSelector(`[data-scenario="${level}"]`);
  const actual=await evaluate(`(async()=>{
    const api=window.tocDemandMap,rows=[];let numericCoordinatesMatch=true;
    api.map.eachLayer(layer=>{if(layer instanceof L.CircleMarker){
      const r=layer.demandRecord,ll=layer.getLatLng();
      numericCoordinatesMatch=numericCoordinatesMatch&&ll.lat===Number(r.latitude)&&ll.lng===Number(r.longitude);
      rows.push([r.stop_id,r.building_id,r.chocho_code,r.latitude,r.longitude,r.parcel_count,String(r.minimum_series)]);
    }});
    rows.sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0);
    const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(rows)));
    return {scenario:'S'+api.active,count:rows.length,unique:new Set(rows.map(r=>r[0])).size,
      digest:Array.from(new Uint8Array(bytes)).map(b=>b.toString(16).padStart(2,'0')).join(''),
      numericCoordinatesMatch,label:document.getElementById('visible-count').textContent,
      legend:Array.from(document.querySelectorAll('[data-group]')).map(e=>e.dataset.visible),
      canvas:document.querySelectorAll('#map canvas').length};
  })()`);
  assert(actual.scenario==='S'+level,'Wrong active series');
  assert(actual.count===csv['S'+level].length&&actual.unique===actual.count,'Wrong/duplicate marker count');
  assert(actual.digest===expectedHashes['S'+level],'Rendered IDs/attributes differ from original CSV');
  assert(actual.numericCoordinatesMatch,'Marker coordinates do not match CSV numbers');
  assert(actual.canvas===1,'Expected one Canvas renderer');
  assert(actual.label.replace(/,/g,'')===String(actual.count),'Wrong visible count label');
  assert(actual.legend.every((v,i)=>v===String(i<level)),'Wrong legend visibility');
  report.scenario_checks.push({...actual,offline,interaction_check_ms:Date.now()-start});
}
async function screenshot(filename){
  await draw();const data=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  fs.writeFileSync(path.join(review,filename),Buffer.from(data.data,'base64'),{flag:'wx'});
}
async function popupCheck(group,offline){
  await evaluate('window.tocDemandMap.map.stop();window.tocDemandMap.map.closePopup();void 0');
  await draw();
  // Pick a non-overlapping actual point at zoom 18, then click the Canvas physically.
  const point=await evaluate(`(()=>{
    const api=window.tocDemandMap,all=api.visibleRecords().map(r=>({r,p:api.map.project([Number(r.latitude),Number(r.longitude)],18)}));
    const selected=all.find(a=>a.r.minimum_series===${group}&&all.every(b=>a===b||a.p.distanceTo(b.p)>13));
    if(!selected)throw Error('No isolated click target');
    api.map.setView([Number(selected.r.latitude),Number(selected.r.longitude)],18,{animate:false});
    return selected.r;
  })()`);
  await draw();
  const xy=await evaluate(`(()=>{const api=window.tocDemandMap,m=api.markerById.get(${JSON.stringify(point.stop_id)}),p=api.map.latLngToContainerPoint(m.getLatLng()),r=document.getElementById('map').getBoundingClientRect();return {x:r.x+p.x,y:r.y+p.y}})()`);
  await clickPoint(xy.x,xy.y);await pause(150);
  const popup=await evaluate(`(()=>{const p=document.querySelector('.leaflet-popup-content [data-stop-id]');return p?{stop_id:p.dataset.stopId,fields:Object.fromEntries(Array.from(p.querySelectorAll('[data-field]')).map(e=>[e.dataset.field,e.textContent]))}:null})()`);
  assert(popup&&popup.stop_id===point.stop_id,'Physical click opened wrong/no point: '+JSON.stringify({expected:point.stop_id,actual:popup,xy}));
  const original=csv.S3.find(r=>r.stop_id===point.stop_id);
  for(const field of ['stop_id','building_id','chocho_code','latitude','longitude','parcel_count'])assert(popup.fields[field]===original[field],'Wrong popup '+field);
  assert(popup.fields.minimum_series===labels[group],'Wrong minimum series in popup');
  report.popup_checks.push({minimum_group:group,stop_id:point.stop_id,offline,all_fields_match:true,physical_click:true});
}
async function main(){
  let port;
  for(let i=0;i<200;i++){
    const active=path.join(profile,'DevToolsActivePort');
    if(fs.existsSync(active)){port=Number(fs.readFileSync(active,'utf8').split('\n')[0]);break;}
    if(chrome.exitCode!==null)throw new Error('Chrome exited: '+browserLog);
    await pause(100);
  }
  assert(port,'Chrome debugging port unavailable');
  const targets=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const target=targets.find(t=>t.type==='page');
  socket=new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  socket.addEventListener('message',event=>{
    const data=JSON.parse(event.data);
    if(data.id){const callback=pending.get(data.id);if(callback){pending.delete(data.id);data.error?callback.reject(new Error(JSON.stringify(data.error))):callback.resolve(data.result);}}
    if(data.method==='Runtime.exceptionThrown')exceptions.push(data.params.exceptionDetails);
    if(data.method==='Network.loadingFailed')report.network_failures.push(data.params);
    if(data.method==='Network.requestWillBeSent'&&data.params.request.url.includes('cyberjapandata.gsi.go.jp/xyz/'))report.tile_requests++;
  });
  report.browser=(await command('Browser.getVersion')).product;
  await command('Page.enable');await command('Runtime.enable');await command('Network.enable');
  await command('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await command('Page.navigate',{url:report.url});await ready();
  for(let i=0;i<40;i++){if(await evaluate('window.tocDemandMap.tileStats.loaded>0'))break;await pause(250);}
  report.online_tile_stats=await evaluate('({...window.tocDemandMap.tileStats})');
  report.title=await evaluate('document.querySelector("h1").textContent');
  assert(report.title==='大田区ToC配送研究：固定需要地点分布','Wrong title');
  for(const level of [1,2,3]){await scenarioCheck(level,false);await screenshot(`map_S${level}.png`);}
  for(const level of [2,1,3])await scenarioCheck(level,false);
  for(const group of [1,2,3])await popupCheck(group,false);
  await screenshot('map_stop_popup.png');
  await evaluate('window.tocDemandMap.map.closePopup();void 0');
  const zoomBefore=await evaluate('window.tocDemandMap.map.getZoom()');
  await clickSelector('.leaflet-control-zoom-in');await pause(400);
  assert(await evaluate('window.tocDemandMap.map.getZoom()')===zoomBefore+1,'Zoom control failed');
  const center=await evaluate('window.tocDemandMap.map.getCenter()');
  const drag=await evaluate('(()=>{const r=document.getElementById("map").getBoundingClientRect();return {x:r.x+r.width*.6,y:r.y+r.height*.65}})()');
  await command('Input.dispatchMouseEvent',{type:'mouseMoved',x:drag.x,y:drag.y});
  await command('Input.dispatchMouseEvent',{type:'mousePressed',x:drag.x,y:drag.y,button:'left',buttons:1,clickCount:1});
  for(let i=1;i<=6;i++){await command('Input.dispatchMouseEvent',{type:'mouseMoved',x:drag.x+15*i,y:drag.y+5*i,buttons:1});await pause(35);}
  await command('Input.dispatchMouseEvent',{type:'mouseReleased',x:drag.x+90,y:drag.y+30,button:'left',buttons:0,clickCount:1});
  await pause(600);
  const moved=await evaluate('window.tocDemandMap.map.getCenter()');
  assert(center.lat!==moved.lat||center.lng!==moved.lng,'Map drag failed');
  report.zoom_control=true;report.physical_pan=true;
  const origin=await evaluate('performance.timeOrigin');
  await command('Network.emulateNetworkConditions',{offline:true,latency:0,downloadThroughput:0,uploadThroughput:0});
  await command('Network.setCacheDisabled',{cacheDisabled:true});
  await command('Page.reload',{ignoreCache:true});await ready(origin);
  for(const level of [1,2,3])await scenarioCheck(level,true);
  await popupCheck(3,true);
  await evaluate('window.tocDemandMap.map.closePopup();window.tocDemandMap.fitVisible()');
  await pause(300);await screenshot('map_offline.png');
  report.offline_file_reload=true;
  assert(exceptions.length===0,'Uncaught browser JavaScript exception');
  report.status='PASS';
}
main().catch(error=>{report.status='FAIL';report.error=error.stack;process.exitCode=1;}).finally(async()=>{
  fs.writeFileSync(path.join(review,'BROWSER_VALIDATION.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  fs.writeFileSync(path.join(review,'CHROME_LOG.txt'),browserLog,{flag:'wx'});
  console.log(JSON.stringify({status:report.status,browser:report.browser,scenarios:report.scenario_checks.length,popups:report.popup_checks.length,tiles:report.online_tile_stats,error:report.error}));
  if(socket)socket.close();chrome.kill('SIGTERM');await pause(300);
  try{fs.rmSync(profile,{recursive:true,force:true});}catch(e){}
});
