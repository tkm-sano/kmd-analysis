const $ = id => document.getElementById(id);
const esc = value => String(value ?? "—").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[char]));
const NS = "http://www.w3.org/2000/svg";
const EDGE_COLORS = {"produces":"#217a63","depends on":"#b45309","parameterizes":"#6d5bd0","validates":"#087aa3","compares with":"#b13f75","feeds into":"#536782","interprets":"#7b4b2a"};
const STATUSES = ["DONE","CURRENT","NEXT","PLANNED","FUTURE","UNRESOLVED","SUPERSEDED","HISTORICAL"];
const readableStatus = value => String(value ?? "—").replaceAll("_", " ");

function pathLink(path, label = path) {
  if (!path) return '<span class="muted">NOT AVAILABLE</span>';
  if (path.startsWith("./research")) return `<code>${esc(path)}</code>`;
  const clean = path.split("#")[0];
  return `<a href="/artifact/${encodeURI(clean)}" target="_blank" rel="noopener">${esc(label)}</a>`;
}

function svgElement(name, attrs = {}) {
  const element = document.createElementNS(NS, name);
  Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function renderGraph(target, graph, options = {}) {
  const width = options.width || 1200, height = options.height || 220;
  const svg = svgElement("svg", {viewBox:`0 0 ${width} ${height}`, role:"img", "aria-label":options.label || "Research graph"});
  svg.classList.add("map-svg");
  const defs = svgElement("defs");
  for (const [relation, color] of Object.entries(EDGE_COLORS)) {
    const id = `arrow-${relation.replaceAll(" ", "-")}`;
    const marker = svgElement("marker", {id, viewBox:"0 0 10 10", refX:"9", refY:"5", markerWidth:"6", markerHeight:"6", orient:"auto-start-reverse"});
    marker.append(svgElement("path", {d:"M 0 0 L 10 5 L 0 10 z", fill:color}));
    defs.append(marker);
  }
  svg.append(defs);
  (graph.groups || []).forEach(group => {
    const g = svgElement("g", {class:"map-group"});
    g.append(svgElement("rect", {x:group.x,y:group.y,width:group.width,height:group.height,rx:14}));
    const text = svgElement("text", {x:group.x+16,y:group.y+28});
    text.textContent = group.name;
    g.append(text);
    svg.append(g);
  });
  const byId = Object.fromEntries(graph.nodes.map(node => [node.id,node]));
  graph.edges.forEach(edge => {
    const from = byId[edge.from], to = byId[edge.to];
    if (!from || !to) return;
    const sx=from.x+85, sy=from.y+58, tx=to.x+85, ty=to.y;
    const horizontal = Math.abs(tx-sx) > Math.abs(ty-sy);
    const path = horizontal
      ? `M ${sx} ${sy-28} C ${(sx+tx)/2} ${sy-28}, ${(sx+tx)/2} ${ty+28}, ${tx} ${ty+28}`
      : `M ${sx} ${sy} C ${sx} ${(sy+ty)/2}, ${tx} ${(sy+ty)/2}, ${tx} ${ty}`;
    const line = svgElement("path", {d:path,class:"map-edge","data-relation":edge.relation,stroke:EDGE_COLORS[edge.relation] || "#697386","marker-end":`url(#arrow-${edge.relation.replaceAll(" ","-")})`});
    svg.append(line);
    const label = svgElement("text", {x:(sx+tx)/2,y:(sy+ty)/2-5,class:"edge-label"});
    label.textContent=edge.relation;
    svg.append(label);
  });
  graph.nodes.forEach(node => {
    const g = svgElement("g", {transform:`translate(${node.x},${node.y})`,class:`map-node status-${String(node.status || "future").toLowerCase()}`,tabindex:"0",role:"button","aria-label":`${node.name}, ${node.status || ""}`});
    g.append(svgElement("rect", {width:170,height:58,rx:10}));
    const name = svgElement("text", {x:85,y:24,"text-anchor":"middle",class:"node-name"});
    name.textContent=node.name; g.append(name);
    if (node.status) {
      const status=svgElement("text",{x:85,y:44,"text-anchor":"middle",class:"node-status"});status.textContent=node.detail?.detail_type === "evidence" ? readableStatus(node.status) : node.status;g.append(status);
    }
    if (node.detail) {
      const open=()=>showStage(node);
      g.addEventListener("click",open);
      g.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();open();}});
    }
    svg.append(g);
  });
  $(target).replaceChildren(svg);
}

function renderField(label, value, kind = "text") {
  let content;
  if (Array.isArray(value)) content = value.length ? `<ul>${value.map(item=>`<li>${kind==="path"?pathLink(item):esc(item)}</li>`).join("")}</ul>` : '<span class="muted">NONE RECORDED</span>';
  else content = kind === "path" ? pathLink(value) : esc(value);
  return `<div class="detail-field"><dt>${esc(label)}</dt><dd>${content}</dd></div>`;
}

function showStage(node) {
  const detail=node.detail || {};
  if (detail.detail_type === "evidence") {
    $("stage-detail").innerHTML=`
      <p class="section-number">EVIDENCE NODE DETAIL</p>
      <div class="dialog-title"><h2>${esc(node.name)}</h2><span class="badge status-${String(detail.evidence_status).toLowerCase()}">${esc(readableStatus(detail.evidence_status))}</span></div>
      <dl class="detail-grid">
        ${renderField("Meaning",detail.meaning)}
        ${renderField("Evidence status",readableStatus(detail.evidence_status))}
        ${renderField("Evidence type",detail.evidence_type)}
        ${renderField("Key supporting sources",detail.key_sources)}
        ${renderField("Conditions",detail.conditions)}
        ${renderField("Out-of-scope claims",detail.out_of_scope_claims)}
        ${renderField("Evidence artifact",detail.evidence_artifact,"path")}
      </dl>`;
    $("stage-dialog").showModal();
    return;
  }
  $("stage-detail").innerHTML=`
    <p class="section-number">STAGE DETAIL</p>
    <div class="dialog-title"><h2>${esc(node.name)}</h2><span class="badge status-${String(node.status).toLowerCase()}">${esc(node.status)}</span></div>
    <dl class="detail-grid">
      ${renderField("Purpose",detail.purpose)}
      ${renderField("Status",detail.status)}
      ${renderField("Primary input",detail.primary_input)}
      ${renderField("Primary output",detail.primary_output)}
      ${renderField("Decision",detail.decision,"path")}
      ${renderField("Specification",detail.specification,"path")}
      ${renderField("Registry / Schema",detail.registry_schema,"path")}
      ${renderField("Implementation",detail.implementation,"path")}
      ${renderField("Validator",detail.validator,"path")}
      ${renderField("Canonical artifact",detail.canonical_artifact,"path")}
      ${renderField("Result",detail.result)}
      ${renderField("Known limitations",detail.known_limitations)}
      ${renderField("Blocking dependency",detail.blocking_dependency)}
      ${renderField("Next action",detail.next_action)}
      ${renderField("Reproduce / inspect",detail.commands)}
    </dl>`;
  $("stage-dialog").showModal();
}

let stateCache;

function renderEvidence(interpretation) {
  const nodeById=Object.fromEntries(interpretation.pathway_nodes.map(node=>[node.id,node]));
  $("evidence-overview").innerHTML=`<div class="metric-grid">
    ${metric("Overall judgment",readableStatus(interpretation.overall_assessment),"Interpretation layer; not an adopted investment outcome")}
    ${metric("Direct analysis boundary",interpretation.direct_research_boundary,"Everything downstream is interpretation")}
    ${metric("Evidence sources",interpretation.source_counts.total,`${interpretation.source_counts.verified_research_input} verified research input · ${interpretation.source_counts.needs_source_verification} need source verification`)}
  </div><p class="evidence-wording">${esc(interpretation.wording.ja)}</p><p class="evidence-wording en">${esc(interpretation.wording.en)}</p>`;

  const downstream=interpretation.pathway_nodes.filter(node=>node.layer==="EVIDENCE_SUPPORTED_INTERPRETATION");
  $("evidence-pathway").innerHTML=`<div class="direct-zone"><strong>DIRECT ANALYSIS</strong><span>Technology / Optimization → Delivery Fulfillment</span></div><div class="boundary-line"><span>DIRECT ANALYSIS BOUNDARY</span></div><div class="interpretation-zone"><strong>EVIDENCE-SUPPORTED INTERPRETATION</strong><div>${downstream.map((node,index)=>`<button data-evidence-node="${esc(node.id)}"><span>${esc(node.label)}</span><small>${esc(readableStatus(node.evidence_status))}</small></button>${index<downstream.length-1?'<i>↓</i>':''}`).join("")}</div></div>`;
  document.querySelectorAll("[data-evidence-node]").forEach(button=>button.addEventListener("click",()=>{
    const graphNode=stateCache.maps.conceptual.nodes.find(node=>node.id===button.dataset.evidenceNode);
    if (graphNode) showStage(graphNode);
  }));

  $("evidence-link-table").innerHTML=`<table><thead><tr><th>Link</th><th>Evidence status</th><th>Strength</th><th>Type</th></tr></thead><tbody>${interpretation.pathway_links.map(link=>`<tr><td>${esc(nodeById[link.from]?.label||link.from)} → ${esc(nodeById[link.to]?.label||"Actual Corporate Investment Decision")}</td><td><span class="gate">${esc(readableStatus(link.evidence_status))}${link.claim_status?` / ${esc(readableStatus(link.claim_status))}`:""}</span></td><td>${esc(link.strength_label)}</td><td>${esc(link.evidence_type)}</td></tr>`).join("")}</tbody></table>`;
  $("evidence-boundary").innerHTML=`<div><h3>What evidence supports</h3><ul>${interpretation.supports.map(item=>`<li>${esc(item)}</li>`).join("")}</ul></div><div class="does-not"><h3>What this does not mean</h3><ul>${interpretation.does_not_support.map(item=>`<li>${esc(item)}</li>`).join("")}</ul><p><strong>Actual Investment Decision:</strong> NOT ESTABLISHED / OUT OF SCOPE</p></div>`;
  $("evidence-trace-chain").innerHTML=interpretation.traceability.map((item,index)=>`<div><span>${String(index+1).padStart(2,"0")}</span><strong>${esc(item.label)}</strong>${item.path?pathLink(item.path,"open"):`<small>${esc(item.value)}</small>`}</div>`).join("");
}

function metric(label,value,note="") {
  return `<article class="metric"><span>${esc(label)}</span><strong>${esc(value)}</strong>${note?`<small>${esc(note)}</small>`:""}</article>`;
}

function renderNetwork(network) {
  const validation=network.validation,mapping=network.mapping;
  const facts=[
    ["Decision ID",network.decision_id],["Accepted run",network.accepted_run],
    ["Network path",pathLink(network.network_path,"Open canonical network")],
    ["Network SHA",network.declared_sha256],["SUMO version",network.sumo_version],
    ["Build",validation.sumo_build],["Lane",validation.lane_validity],["Speed",validation.speed_validity],
    ["Permission",validation.permission_validity],["Connectivity",validation.connectivity],
    ["Stop mapping",`${mapping.mapped.toLocaleString()} / ${mapping.total_stops.toLocaleString()}`],
    ["Routeability acceptance",validation.delivery_routeability],
    ["FORMAL_NETWORK_ACCEPTED",String(network.accepted)]
  ];
  $("network-summary").innerHTML=`
    <div class="facts">${facts.map(([label,value])=>`<div><dt>${esc(label)}</dt><dd>${String(value).startsWith("<a")?value:esc(value)}</dd></div>`).join("")}</div>
    <aside class="limitations"><h3>Known limitations</h3><ul>${network.known_limitations.map(item=>`<li>${esc(item)}</li>`).join("")}</ul>
    <p class="integrity ${network.sha_matches?"pass":"fail"}">SHA integrity: ${network.sha_matches?"MATCH":"MISMATCH"}</p></aside>`;
}

function render(state) {
  stateCache=state;
  $("question").textContent=state.research_question;
  $("philosophy").textContent=state.portal_philosophy;
  $("interpretation-mode").textContent=state.interpretation_mode;
  $("current-milestone").textContent=`${state.current_position.current_milestone} — ${state.current_position.milestone_status}`;
  $("current-stage").textContent=state.current_position.current_stage;
  $("next-task").textContent=state.current_position.immediate_next_task;

  $("status-legend").innerHTML=STATUSES.map(status=>`<span class="badge status-${status.toLowerCase()}">${status}</span>`).join("");
  $("edge-legend").innerHTML=Object.entries(EDGE_COLORS).map(([label,color])=>`<span><i style="background:${color}"></i>${esc(label)}</span>`).join("");
  renderGraph("conceptual-map",state.maps.conceptual,{width:1170,height:210,label:"Conceptual Research Map"});
  renderEvidence(state.interpretation_evidence);
  renderGraph("implementation-map",state.maps.implementation,{width:1500,height:710,label:"Implementation and Analysis Map"});
  renderGraph("data-flow-map",state.maps.data_flow,{width:1160,height:290,label:"Research data flow"});

  $("milestone-grid").innerHTML=[
    metric("M1 Network Ready","DONE","Current milestone"),
    metric("Formal Network Acceptance","ACCEPTED",state.accepted_network.network_id),
    metric("Routing Baseline","NEXT","No production artifact"),
    metric("Common Delivery Instance","PLANNED","Depends on Routing"),
    metric("Optimization / Quantum","FUTURE","No results claimed")
  ].join("");
  renderNetwork(state.accepted_network);

  $("validation-table").innerHTML=`<table><thead><tr><th>Stage</th><th>Validation gate</th><th>Status</th></tr></thead><tbody>${state.validation_gates.map(row=>`<tr><td>${esc(row.stage)}</td><td>${esc(row.gate)}</td><td><span class="gate gate-${row.status.toLowerCase().replaceAll(" ","-")}">${esc(row.status)}</span></td></tr>`).join("")}</tbody></table>`;
  $("unresolved-grid").innerHTML=state.unresolved_decisions.map(item=>`<article><span class="badge status-unresolved">UNRESOLVED</span><h3>${esc(item.label)}</h3><p>blocks</p><div>${item.blocks.map(stage=>`<button data-stage="${esc(stage)}">${esc(stage)}</button>`).join("")}</div><small>Evidence: ${esc(item.evidence)}</small></article>`).join("");

  $("trace-chain").innerHTML=state.traceability.map((item,index)=>`<div class="${item.available?"":"unavailable"}"><span>${String(index+1).padStart(2,"0")}</span><strong>${esc(item.label)}</strong>${item.url?pathLink(item.path,"open"):`<small>${esc(item.status)}</small>`}</div>`).join("");
  const categories=[...new Set(state.artifacts.map(item=>item.category))];
  $("artifact-browser").innerHTML=categories.map(category=>`<section><h3>${esc(category)}</h3><ul>${state.artifacts.filter(item=>item.category===category).map(item=>`<li><span class="badge status-${item.lifecycle.toLowerCase()}">${esc(item.lifecycle)}</span><div><strong>${esc(item.label)}</strong><small>${esc(item.path)}</small></div>${item.exists&&item.url?pathLink(item.path,"open"):'<span class="muted">MISSING</span>'}</li>`).join("")}</ul></section>`).join("");

  const tiers=state.provenance.tiers;
  $("provenance-grid").innerHTML=`<div class="tier-chart">${tiers.map(item=>`<div><header><strong>${esc(item.tier)}</strong><span>${item.count.toLocaleString()} · ${item.percent.toFixed(2)}%</span></header><i><b style="width:${Math.max(item.percent,.4)}%"></b></i></div>`).join("")}</div><div class="confidence"><h3>Confidence</h3>${Object.entries(state.provenance.confidence).map(([key,value])=>metric(key,value.toLocaleString())).join("")}<p>Tier is provenance class; confidence is not direct observation.</p></div>`;
  const lifecycle=[["CURRENT",state.historical.current],["HISTORICAL",state.historical.historical],["SUPERSEDED",state.historical.superseded],["GENERATED / DIAGNOSTIC",state.historical.generated_diagnostic]];
  $("lifecycle-grid").innerHTML=lifecycle.map(([label,items])=>`<article><span class="badge status-${label.split(" ")[0].toLowerCase()}">${esc(label)}</span><ul>${items.map(item=>`<li>${esc(item)}</li>`).join("")}</ul></article>`).join("");
  $("timeline-list").innerHTML=state.timeline.map(item=>`<article><time>${esc(item.date)}</time><div><strong>${esc(item.event)}</strong><p>${esc(item.detail)}</p>${pathLink(item.source,"source")}</div></article>`).join("");
  $("command-list").innerHTML=state.commands.map(item=>`<article><button class="copy" data-copy="${esc(item.command)}" title="Copy command">COPY</button><code>${esc(item.command)}</code><p>${esc(item.purpose)}</p></article>`).join("");
  document.querySelectorAll("[data-copy]").forEach(button=>button.addEventListener("click",()=>navigator.clipboard?.writeText(button.dataset.copy)));
  const routing=state.maps.implementation.nodes.find(node=>node.id==="routing_baseline");
  $("routing-placeholder").innerHTML=`<div><h3>Available inputs</h3><ul><li>accepted network</li><li>accepted Stop mapping</li><li>Requests / Stops</li></ul></div><div><h3>Unresolved</h3><ul>${routing.detail.blocking_dependency.map(item=>`<li>${esc(item)}</li>`).join("")}</ul></div><div><h3>Expected outputs</h3><ul><li>travel-time cost</li><li>distance cost</li><li>routeability</li><li>routing provenance</li></ul></div><button id="routing-detail">Open stage detail</button>`;
  $("routing-detail").addEventListener("click",()=>showStage(routing));
  $("source-chain").innerHTML=Object.entries(state.source_of_truth).map(([key,value])=>`<span><strong>${esc(key)}</strong> ${pathLink(value,"open")}</span>`).join("");
}

fetch("/api/state")
  .then(response=>{if(!response.ok) throw new Error(`Portal state HTTP ${response.status}`);return response.json();})
  .then(render)
  .catch(error=>{const box=$("error");box.hidden=false;box.textContent=`Portal state could not be loaded: ${error.message}`;});
