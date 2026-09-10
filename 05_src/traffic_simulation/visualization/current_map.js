// Compact data and one canvas per layer keep the full network browsable.
(() => {
  const map = {{this._parent.get_name()}}, data = __PAYLOAD__;
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const CanvasLayer = L.Layer.extend({
    initialize(rows, points, color) { this.rows = rows; this.points = points; this.color = color; },
    onAdd(map) {
      this._map = map;
      this.canvas = L.DomUtil.create('canvas', 'leaflet-layer');
      this.canvas.style.pointerEvents = 'none';
      map.getPanes().overlayPane.appendChild(this.canvas);
      map.on('moveend resize zoomend', this.draw, this);
      this.draw();
    },
    onRemove(map) { map.off('moveend resize zoomend', this.draw, this); this.canvas.remove(); },
    draw() {
      const size = map.getSize(), canvas = this.canvas, ratio = window.devicePixelRatio || 1;
      canvas.width = size.x * ratio; canvas.height = size.y * ratio;
      canvas.style.width = size.x + 'px'; canvas.style.height = size.y + 'px';
      L.DomUtil.setPosition(canvas, map.containerPointToLayerPoint([0, 0]));
      const ctx = canvas.getContext('2d'); ctx.scale(ratio, ratio);
      ctx.strokeStyle = ctx.fillStyle = this.color; ctx.lineWidth = map.getZoom() >= 16 ? 2 : 1;
      const bounds = map.getBounds().pad(0.1);
      ctx.beginPath();
      for (const row of this.rows) {
        if (this.points) {
          if (!bounds.contains(row[1])) continue;
          const p = map.latLngToContainerPoint(row[1]);
          const radius = map.getZoom() >= 16 ? 3 : 1.5;
          ctx.moveTo(p.x + radius, p.y); ctx.arc(p.x, p.y, radius, 0, 2 * Math.PI);
        } else {
          if (!bounds.intersects(row.bounds)) continue;
          row[1].forEach((coord, i) => {
            const p = map.latLngToContainerPoint(coord);
            if (i) ctx.lineTo(p.x, p.y); else ctx.moveTo(p.x, p.y);
          });
        }
      }
      if (this.points) ctx.fill(); else ctx.stroke();
    }
  });
  data.roads.forEach(row => { row.bounds = L.latLngBounds(row[1]); });
  const permitted = new CanvasLayer(data.roads.filter(r => r[2]), false, '#2166ac').addTo(map);
  const other = new CanvasLayer(data.roads.filter(r => !r[2]), false, '#999').addTo(map);
  const stops = new CanvasLayer(data.stops, true, '#df7414');
  L.control.layers({}, {
    '受入済み道路 · delivery通行可': permitted,
    '受入済み道路 · その他': other,
    '配送地点 · 建物代表点': stops
  }, {collapsed: false}).addTo(map);
  const roadIndex = new Map(data.roads.map(row => [row[0], row]));
  const search = document.createElement('form');
  search.innerHTML = '<label for="road-id-search">エッジIDで道路を検索</label><br><input id="road-id-search" name="edge" required style="width:70%"><button type="submit">表示</button><p role="status"></p>';
  document.getElementById('research-panel').appendChild(search);
  search.onsubmit = event => {
    event.preventDefault();
    const id = search.elements.edge.value.trim();
    search.querySelector('[role="status"]').textContent = roadIndex.has(id) ? '' : '該当するエッジIDがありません。';
    if (roadIndex.has(id)) selectRoad(id, true);
  };
  const highlights = L.featureGroup().addTo(map);
  const detailPanel = document.createElement('aside');
  detailPanel.id = 'road-detail'; detailPanel.hidden = true;
  detailPanel.setAttribute('aria-label', '選択道路の詳細');
  document.body.appendChild(detailPanel);
  const style = document.createElement('style');
  style.textContent = `#road-detail{position:fixed;right:12px;top:110px;width:390px;max-height:calc(100vh - 145px);overflow:auto;z-index:1100;background:#fff;padding:18px;border-radius:12px;box-shadow:0 3px 18px #0003;font:14px/1.6 sans-serif;overflow-wrap:anywhere}
  #road-detail h2{font-size:18px;margin:0 0 10px} #road-detail h3{font-size:16px} #road-detail table{width:100%;border-collapse:collapse} #road-detail th,#road-detail td{padding:5px;text-align:left;vertical-align:top;border-bottom:1px solid #ddd} #road-detail th{width:35%} #road-detail button{cursor:pointer;margin:3px;padding:5px 9px;background:#eff5fa;border:1px solid #aab8c3;border-radius:4px} #road-detail details{margin-top:12px} .road-arrow{color:#b00065;font-size:25px;line-height:24px;text-shadow:0 0 3px white}
  @media(max-width:650px){#road-detail{top:auto;bottom:12px;left:12px;right:12px;width:auto;max-height:46vh} body.road-selected #research-panel{display:none}}`;
  document.head.appendChild(style);
  const caches = new Map();
  let queue = Promise.resolve(), selection = 0;
  function loadDetails(row) {
    const shard = row[5];
    if (!caches.has(shard)) {
      const pending = queue.then(() => new Promise((resolve, reject) => {
        const script = document.createElement('script');
        const timer = setTimeout(() => fail(), 20000);
        function fail() { clearTimeout(timer); script.remove(); reject(new Error('詳細ファイルを読み込めません。HTMLとcurrent_map_detailsフォルダーを同じ場所に配置してください。')); }
        script.onload = () => {
          clearTimeout(timer);
          const result = window.researchMapDetails;
          window.researchMapDetails = undefined;
          script.remove();
          if (!result || !result[row[0]]) reject(new Error('詳細データが地図と一致しません。地図を再生成してください。'));
          else resolve(result);
        };
        script.onerror = fail;
        script.src = data.detail_shards[shard];
        document.head.appendChild(script);
      }));
      caches.set(shard, pending);
      queue = pending.catch(() => { caches.delete(shard); });
    }
    return caches.get(shard).then(bucket => bucket[row[0]]);
  }
  const value = v => v === undefined || v === null || v === '' ? '未記載' : escape(v);
  const table = pairs => '<table>' + pairs.map(([k,v]) => `<tr><th>${escape(k)}</th><td>${value(v)}</td></tr>`).join('') + '</table>';
  const button = (id, text) => `<button type="button" data-road="${escape(id)}">${escape(text)}</button>`;
  function drawRoad(row, color, weight = 5) {
    if (row) L.polyline(row[1], {color, weight, opacity:0.9, interactive:false}).addTo(highlights);
  }
  function direction(row) {
    const i = Math.max(1, Math.floor(row[1].length / 2));
    const a = map.latLngToLayerPoint(row[1][i-1]), b = map.latLngToLayerPoint(row[1][i]);
    const angle = Math.atan2(b.y-a.y, b.x-a.x) * 180 / Math.PI;
    const middle = [(row[1][i-1][0]+row[1][i][0])/2, (row[1][i-1][1]+row[1][i][1])/2];
    L.marker(middle, {interactive:false, icon:L.divIcon({className:'road-arrow', html:`<div style="transform:rotate(${angle}deg)">➤</div>`, iconSize:[24,24], iconAnchor:[12,12]})}).addTo(highlights);
  }
  async function selectRoad(id, focus = false) {
    const row = roadIndex.get(id); if (!row) return;
    const token = ++selection;
    detailPanel.hidden = false; document.body.classList.add('road-selected');
    detailPanel.innerHTML = '<button type="button" data-close>閉じる</button><p>道路の詳細を読み込み中…</p>';
    detailPanel.querySelector('[data-close]').onclick = closeDetails;
    highlights.clearLayers(); drawRoad(row, '#b00065', 7); direction(row);
    if (focus) map.fitBounds(row.bounds.pad(0.6), {maxZoom:18, animate:false});
    try {
      const detail = await loadDetails(row);
      if (token !== selection) return;
      const a = detail.attributes;
      const incoming = [...new Set(detail.incoming.map(c=>c.from))];
      const outgoing = [...new Set(detail.outgoing.map(c=>c.to))];
      const allConnections = [...detail.incoming, ...detail.outgoing];
      const dirs = {s:'直進', l:'左折', r:'右折', t:'転回', L:'緩い左折', R:'緩い右折'};
      detailPanel.innerHTML = `<button type="button" data-close>閉じる</button><h2>${escape(a.name || a.id)}</h2>
        <p>紫: 選択道路と進行方向 / 緑: 流入 / 橙: 流出</p>
        <h3>基本情報（SUMO値）</h3>${table([['エッジID',a.id],['道路名',a.name],['道路種別',a.type],['優先度',a.priority],['接続元',a.from],['接続先',a.to],['代表レーン長さ (m)',detail.lanes[0].length],['レーン数',detail.lanes.length]])}
        <details open><summary>レーン別属性</summary>${detail.lanes.map((lane,i)=>`<h3>レーン ${value(lane.index ?? i)}</h3><button type="button" data-lane="${i}">このレーンを強調</button>${table([['ID',lane.id],['長さ (m)',lane.length],['幅 (m)',lane.width],['速度 (m/s)',lane.speed],['速度 (km/h)',lane.speed == null ? null : (Number(lane.speed)*3.6).toFixed(2)],['allow（通行許可）',lane.allow],['disallow（通行禁止）',lane.disallow],['原典ID param',lane.params?.origId]])}`).join('')}<p>未記載はXMLに値がないことを表します。allow/disallowが両方未記載なら車種制限なし。幅の未記載値は推測表示しません。</p></details>
        <details open><summary>接続道路・レーン間接続</summary><button type="button" data-neighbors>流入・流出をまとめて強調</button><p>流入: ${incoming.map(id=>button(id,id)).join('') || 'なし'}</p><p>流出: ${outgoing.map(id=>button(id,id)).join('') || 'なし'}</p>
        ${allConnections.map((c,i)=>`<div><button type="button" data-connection="${i}">${escape(c.from)} [${value(c.fromLane)}] → ${escape(c.to)} [${value(c.toLane)}] · ${value(dirs[c.dir] || c.dir)}</button><small>via: ${value(c.via)} / 信号ID: ${value(c.tl)} / linkIndex: ${value(c.linkIndex)} / state（接続属性）: ${value(c.state)}</small></div>`).join('')}
        <p>接続選択では流入・流出レーンを強調します。交差点内のviaレーン形状は表示対象外です。</p></details>
        <details><summary>ジャンクション・信号設定</summary>${Object.entries(detail.junctions).map(([key,j])=>`<h3>${key === 'from' ? '接続元' : '接続先'}</h3>${table([['ID',j?.id],['種別',j?.type]])}`).join('')}
        ${Object.entries(detail.signals).map(([id,programs])=>`<h3>信号 ${escape(id)}</h3>${programs.length ? programs.map(p=>table(Object.entries(p.attributes)) + '<pre>'+escape(JSON.stringify(p.phases,null,2))+'</pre>').join('') : '<p>信号プログラムは未記載</p>'}`).join('') || '<p>接続に信号IDの記載なし</p>'}<p>静的な信号設定です。現在の現示・運転状態ではありません。</p></details>
        <details><summary>出典・補完根拠</summary><p>受入済みnet.xmlの値を表示しています。OSM原典と属性別のDIRECT / INFERRED / FALLBACKは未照合です。エッジIDから原典IDを断定しません。</p>${table([['エッジparam',Object.keys(detail.params).length ? JSON.stringify(detail.params) : null]])}</details>`;
      detailPanel.querySelector('[data-close]').onclick = closeDetails;
      detailPanel.querySelectorAll('[data-road]').forEach(b=>b.onclick=()=>selectRoad(b.dataset.road,true));
      detailPanel.querySelector('[data-neighbors]').onclick = () => {
        ++selection;
        highlights.clearLayers();
        incoming.forEach(id=>drawRoad(roadIndex.get(id),'#168357'));
        outgoing.forEach(id=>drawRoad(roadIndex.get(id),'#dc7914'));
        drawRoad(row,'#b00065',7); direction(row);
        map.fitBounds(highlights.getBounds().pad(0.2),{maxZoom:18,animate:false});
      };
      detailPanel.querySelectorAll('[data-lane]').forEach(b=>b.onclick=()=>{
        ++selection;
        highlights.clearLayers();
        L.polyline(detail.lanes[Number(b.dataset.lane)].coordinates,{color:'#b00065',weight:7,interactive:false}).addTo(highlights);
        direction(row);
      });
      detailPanel.querySelectorAll('[data-connection]').forEach(b=>b.onclick=async()=>{
        const connectionToken = ++selection;
        const c=allConnections[Number(b.dataset.connection)];
        try {
          const source = await loadDetails(roadIndex.get(c.from)), target = await loadDetails(roadIndex.get(c.to));
          if (connectionToken !== selection) return;
          highlights.clearLayers();
          for (const [d,index,color] of [[source,c.fromLane,'#168357'],[target,c.toLane,'#dc7914']]) {
            const lane=d.lanes.find(l=>l.index === index);
            if (lane) L.polyline(lane.coordinates,{color,weight:7,interactive:false}).addTo(highlights);
          }
          map.fitBounds(highlights.getBounds().pad(0.2),{maxZoom:19,animate:false});
        } catch (error) { if(connectionToken === selection) { const message=document.createElement('p'); message.textContent=error.message; b.after(message); } }
      });
    } catch (error) { if (token === selection) { const message=document.createElement('p'); message.textContent=error.message; detailPanel.replaceChildren(message); const close=document.createElement('button'); close.textContent='閉じる'; close.onclick=closeDetails; detailPanel.append(close); } }
  }
  function closeDetails() { ++selection; highlights.clearLayers(); detailPanel.hidden=true; document.body.classList.remove('road-selected'); }
  document.addEventListener('keydown',event=>{if(event.key === 'Escape') closeDetails();});
  map.on('click', event => {
    let distance = 10, selected = null, isStop = false;
    const click = event.containerPoint;
    for (const layer of [permitted, other, stops]) {
      if (!map.hasLayer(layer)) continue;
      for (const row of layer.rows) {
        let d;
        if (layer.points) d = click.distanceTo(map.latLngToContainerPoint(row[1]));
        else {
          if (!row.bounds.pad(0.1).contains(event.latlng) && !row.bounds.intersects(L.latLngBounds(map.containerPointToLatLng(click.subtract([10,10])), map.containerPointToLatLng(click.add([10,10]))))) continue;
          d = Infinity;
          for (let i = 1; i < row[1].length; i++) {
            d = Math.min(d, L.LineUtil.pointToSegmentDistance(click, map.latLngToContainerPoint(row[1][i-1]), map.latLngToContainerPoint(row[1][i])));
          }
        }
        if (d <= distance) { distance = d; selected = row; isStop = layer.points; }
      }
    }
    if (!selected) return;
    if (!isStop) { map.closePopup(); selectRoad(selected[0]); return; }
    closeDetails();
    const body = isStop
      ? `配送地点: ${escape(selected[0])}<br>Requests: ${selected[2]} / 荷物換算: ${selected[3]}<br>需要評価日: ${escape(selected[4])}`
      : `有向エッジ: ${escape(selected[0])}<br>delivery: ${selected[2] ? '通行可' : '通行不可'}<br>レーン数: ${selected[3]} / 代表レーン速度: ${selected[4]} km/h`;
    L.popup().setLatLng(event.latlng).setContent(body).openOn(map);
  });
})();
