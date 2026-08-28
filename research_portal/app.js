const state = { registry: null, view: "overview", category: "all", query: "", zoom: 1, propagationMode: false, propagationOrigin: null, propagationFilter: "all" };
const $ = (id) => document.getElementById(id);
const arr = (value) => Array.isArray(value) ? value : [];
const esc = (value) => String(value ?? "—").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[char]));
const byId = (items, id) => arr(items).find((item) => item.id === id);
const registryNode = (id) => byId(state.registry?.nodes, id);
const statusJa = { implemented:"実装済み",in_progress:"進行中",planned:"計画",blocked:"阻害",unknown:"不明",accepted:"受理済み",provisional:"暫定",not_accepted:"未受理",not_evaluated:"未評価",known:"確認済み",known_proxy:"確認済みproxy",unresolved:"未算出" };
const reasonJa = { data_missing:"データ不足",parameter_not_set:"パラメータ未設定",assumption_not_adopted:"仮定未採用",model_not_formalized:"モデル未定式化",not_calculated:"未計算",evidence_not_accepted:"エビデンス未受理",external_model_not_selected:"外部モデル未選定" };
const urgencyJa = { critical:"最優先",high:"高",medium:"中",low:"低",none:"なし" };
const roleJa = { fixed_condition:"固定条件",scenario_variable:"シナリオ変数",derived:"導出値",output:"出力",input_data:"入力データ",specification:"仕様",configuration:"設定",process:"処理",artifact:"生成物",validation:"検証",acceptance:"研究上の受理",unconfirmed:"役割未確認" };
const originJa = { open_data:"オープンデータ",research_setting:"研究設定",model_derived:"モデル導出",simulation_output:"シミュレーション出力",unknown:"未確定" };
const categoryMeta = {
  open_data:{label:"オープンデータ",icon:"▣",className:"cat-open"},
  model_parameter:{label:"モデル引数",icon:"◉",className:"cat-parameter"},
  derived_value:{label:"導出値",icon:"◆",className:"cat-derived"},
  problem_size:{label:"問題サイズ",icon:"▦",className:"cat-size"},
};
const propagationMeta = {
  condition_propagation:{label:"条件",className:"prop-condition"},
  demand_propagation:{label:"需要",className:"prop-demand"},
  problem_size_propagation:{label:"問題サイズ",className:"prop-size"},
  simulation_outcome_propagation:{label:"配送成果",className:"prop-outcome"},
};
const semanticsJa = { direct:"直接",derived:"導出",conditional:"条件付き",unresolved:"未確定" };
const text = (map, value) => map[value] || value || "未設定";
const badge = (label, cls = "") => `<span class="badge ${esc(cls)}">${esc(label)}</span>`;
const displayLabel = (node) => ({"issue.route_generation_not_frozen":"Common Delivery Instance生成設定未確定","stage.current_review_required":"要レビュー","model.general_traffic_routing":"道路・交通経路設定"}[node?.id] || node?.label_ja || "未設定");
const displayText = (value) => String(value ?? "").replace(/route[- ]generation/gi, "配送経路生成");

function simulationMap() { return state.registry.simulation_map; }
function mapItems() { const map=simulationMap(); return [...map.open_data,...map.model_parameters,...map.derived_values,...map.problem_sizes,...map.process_nodes,map.final_evaluation]; }
function mapItem(id) { return byId(mapItems(), id); }
function propagationRelations() { return arr(simulationMap().propagation_relations); }
function outgoingRelations(id) { return propagationRelations().filter((relation)=>relation.source===id); }
function propagationReach(origin=state.propagationOrigin) {
  if(!origin)return {nodes:new Set(),relations:new Set(),steps:new Map()};
  const nodes=new Set([origin]),relations=new Set(),steps=new Map([[origin,0]]),queue=[origin];
  while(queue.length){const source=queue.shift();outgoingRelations(source).forEach((relation)=>{relations.add(relation.id);if(!nodes.has(relation.target)){nodes.add(relation.target);steps.set(relation.target,(steps.get(source)||0)+1);queue.push(relation.target);}});}
  return {nodes,relations,steps};
}
function shortestPropagationPath(source,target){
  if(!source||!target)return null;const queue=[{id:source,relations:[]}],seen=new Set([source]);
  while(queue.length){const current=queue.shift();if(current.id===target)return current.relations;for(const relation of outgoingRelations(current.id)){if(!seen.has(relation.target)){seen.add(relation.target);queue.push({id:relation.target,relations:[...current.relations,relation]});}}}return null;
}
function outcomePropagationPath(source){
  const delivered="map.derived.delivered_parcel_equivalent";const finalId=simulationMap().final_evaluation.id;
  const operational=shortestPropagationPath(source,delivered);const terminal=relationBetween(delivered,finalId);
  return operational&&terminal?[...operational,terminal]:shortestPropagationPath(source,finalId);
}
function relationBetween(source,target){return propagationRelations().find((relation)=>relation.source===source&&relation.target===target);}
function matchesQuery(item) { return !state.query || JSON.stringify(item).toLowerCase().includes(state.query); }
function categoryClass(item) { return categoryMeta[item.information_category]?.className || "cat-process"; }
function isDimmed(item) { const outside=state.propagationMode&&state.propagationOrigin&&!propagationReach().nodes.has(item.id);return outside||(state.category!=="all"&&item.information_category&&item.information_category!==state.category)||!matchesQuery(item); }
function valueText(item) { if(item.value_status==="unresolved" || item.value==null) return "未算出"; return `${Array.isArray(item.value)?item.value.join(" / "):item.value}${item.unit?` ${item.unit}`:""}`; }
function downstreamLabels(item) { return arr(item.used_by).map((id)=>mapItem(id)?.label_ja||id).join("、"); }
function propagationLabels(id){return outgoingRelations(id).map((relation)=>`<span class="mini-effect ${propagationMeta[relation.propagation_type].className} ${relation.effect_semantics==="unresolved"?"unresolved":""}">${esc(relation.effect_label_ja)}</span>`).join("");}
function nodePropagationClasses(id){if(!state.propagationMode||!state.propagationOrigin)return "";const reach=propagationReach();const endpoint=[simulationMap().final_evaluation.id,"map.size.required_qubits"].includes(id)&&reach.nodes.has(id);return `${id===state.propagationOrigin?"propagation-origin":""} ${endpoint?"propagation-endpoint":""}`;}
function propagationEdge(source,target,fallback="→"){
  const relation=relationBetween(source,target);if(!state.propagationMode||!relation)return `<span class="chain-arrow">${esc(fallback)}</span>`;
  const reach=propagationReach();const active=reach.relations.has(relation.id);const filtered=state.propagationFilter!=="all"&&relation.propagation_type!==state.propagationFilter;
  return `<span class="propagation-edge ${propagationMeta[relation.propagation_type].className} ${relation.effect_semantics==="unresolved"?"unresolved":""} ${relation.propagation_scope==="fixed_input"?"fixed-input":""} ${!active||filtered?"dimmed":""}"><span>${esc(relation.effect_label_ja)}</span>${badge(semanticsJa[relation.effect_semantics],relation.effect_semantics)}<b>→</b></span>`;
}

function mapCard(item, options={}) {
  const meta=categoryMeta[item.information_category];
  const category=meta?`<span class="node-category"><b>${meta.icon}</b>${meta.label}</span>`:`<span class="node-category process">処理</span>`;
  const value=item.value_status?`<strong class="node-value ${item.value_status}">${esc(valueText(item))}</strong>`:"";
  const use=options.showUse&&item.used_by?.length?`<span class="used-by">→ ${esc(downstreamLabels(item))}</span>`:"";
  const status=item.value_status?badge(text(statusJa,item.value_status),item.value_status):"";
  const effects=state.propagationMode?`<span class="node-effects">${propagationLabels(item.id)}</span>`:"";
  return `<button class="semantic-node ${categoryClass(item)} ${isDimmed(item)?"dimmed":""} ${nodePropagationClasses(item.id)} ${options.className||""}" data-map-node="${esc(item.id)}"><span class="node-head">${category}${status}</span><span class="node-label">${esc(item.label_ja)}</span><code>${esc(item.id)}</code>${value}${use}${effects}</button>`;
}
function processCard(id,className="") { const item=mapItem(id); return `<button class="semantic-node cat-process ${isDimmed(item)?"dimmed":""} ${nodePropagationClasses(id)} ${className}" data-map-node="${esc(id)}"><span class="node-category process">処理</span><span class="node-label">${esc(item.label_ja)}</span><code>${esc(id)}</code>${state.propagationMode?`<span class="node-effects">${propagationLabels(id)}</span>`:""}</button>`; }

function renderTabs() {
  const tabs=[["overview","研究全体"],["current","EV都市配送モデル"],["battery","技術変化"],["social","社会変化"],["quantum_scale","量子問題スケール"]];
  $("views").innerHTML=tabs.map(([id,label])=>`<button data-view="${id}" class="${state.view===id?"active":""}">${label}</button>`).join("");
  document.querySelectorAll("[data-view]").forEach((button)=>{button.onclick=()=>{state.view=button.dataset.view;state.zoom=1;renderAll();};});
}
function renderCategoryFilter() {
  const controls=[["all","すべて"],...Object.entries(categoryMeta).map(([id,meta])=>[id,meta.label])];
  $("category-filter").innerHTML=controls.map(([id,label])=>`<button data-category="${id}" class="${state.category===id?"active":""}">${label}</button>`).join("");
  document.querySelectorAll("[data-category]").forEach((button)=>{button.onclick=()=>{state.category=button.dataset.category;renderAll();};});
}
function renderContext() {
  const stage=registryNode(state.registry.current_stage_ref);
  $("title").textContent="量子技術と移動技術が都市を変えるまで";
  $("scope").textContent="量子技術の発展が、移動技術を通じて都市社会・都市経済にどのような変化をもたらしうるかを検討する。";
  $("stage").textContent=stage?.status==="unknown"?"要レビュー":displayLabel(stage);
  const counts=state.registry.nodes.reduce((result,node)=>({...result,[node.status]:(result[node.status]||0)+1}),{});
  $("counts").innerHTML=Object.entries(counts).map(([key,value])=>badge(`${text(statusJa,key)} ${value}`)).join("");
}
function renderSummary() {
  const overview=state.registry.metadata.research_overview_ja||state.registry.metadata.scope_note_ja;
  $("overview").innerHTML=`<p class="eyebrow">研究概要</p><h2>量子技術と都市物流の接点を読み解く</h2><details><summary>研究概要を読む</summary><p class="overview-copy">${esc(overview)}</p></details>`;
  const stage=registryNode(state.registry.current_stage_ref);
  $("stage-card").innerHTML=`<p class="eyebrow">現在の研究段階</p><h3>${stage?.status==="unknown"?"要レビュー":esc(displayLabel(stage))}</h3><p>正式stageが未レビューの場合は推測しません。</p>`;
  $("method-card").innerHTML=`<p class="eyebrow">現在比較する解法</p><h3>Baseline / Classical / Qiskit Aer QAOA</h3><p>Qiskit Aerは古典計算機上の量子回路シミュレータです。</p>`;
  $("metric-card").innerHTML=`<p class="eyebrow">現在の最終評価</p><h3>配送需要充足率</h3><p class="metric-formula">delivered_parcel_equivalent / total_parcel_equivalent</p><small>計算時間は解法比較指標として分離します。</small>`;
}

function renderOverview() {
  const concept=(className,eyebrow,title,body,extra="")=>`<article class="map-node ${className}"><span class="map-eyebrow">${eyebrow}</span><h3>${title}</h3><p>${body}</p>${extra}</article>`;
  $("graph").innerHTML=`<div class="research-map-head"><div><p class="eyebrow">研究全体マップ</p><h2>量子技術から、移動技術を媒介として都市社会・都市経済へ</h2><p>EV都市配送は、この大きな問いを具体化する現在の分析対象です。</p></div><div class="current-location"><span>現在地</span><strong>EV都市配送</strong><small>現在の具体的分析対象</small></div></div><div class="research-map">${concept("quantum-root","上流の問い","量子技術","物理現象の扱い方と情報処理の方法に変化をもたらしうる技術領域")}<div class="map-branch branch-info">${concept("info-path","A｜情報処理側","情報処理の変化","最適化・大規模計算の方法の変化")}</div><div class="map-branch branch-physics">${concept("physics-path","B｜物理現象側","物理現象の扱い方の変化","材料・電子状態の解析可能性",badge("将来検討・未確定"))}</div>${concept("mobility-node","媒介","移動技術","電動化・自動化・交通情報・エネルギー管理・最適化")}${concept("movement-node","波及対象","人・物の移動の変化","移動計画、実行、物流サービスの変化")}<button class="map-node ev-focus" data-view="current"><span class="map-eyebrow">現在の分析対象</span><h3>EV都市配送</h3><p>観測・設定・導出・問題サイズを追う</p><span class="map-action">モデルマップを開く →</span></button>${concept("urban-node","研究全体の下流","都市物流・モビリティ","配送成果や移動条件を介した都市活動への接続")}${concept("society-node","最終的な問い","都市社会・都市経済","定量接続モデルは将来検討",badge("仮説・未確定"))}</div>`;
}

function propagationChain(path,label){
  if(!path)return `<section><h4>${esc(label)}</h4><p class="no-path">現在formal relationなし</p></section>`;
  const ids=[path[0]?.source,...path.map((relation)=>relation.target)].filter(Boolean);
  return `<section><h4>${esc(label)}</h4><div class="propagation-chain">${ids.map((id,index)=>`<button data-chain-node="${esc(id)}"><b>${index+1}</b><span>${esc(mapItem(id)?.label_ja||id)}</span></button>${index<path.length?`<em class="${propagationMeta[path[index].propagation_type].className} ${path[index].effect_semantics==="unresolved"?"unresolved":""}">${esc(path[index].effect_label_ja)}・${esc(semanticsJa[path[index].effect_semantics])}</em>`:""}`).join("")}</div></section>`;
}
function renderPropagationSummary(){
  if(!state.propagationOrigin)return `<aside class="propagation-summary empty-origin"><strong>波及を見る</strong><p>起点にしたいnodeを選択してください。関係のないnodeは位置を残したまま薄く表示します。</p></aside>`;
  const origin=mapItem(state.propagationOrigin);const outcome=outcomePropagationPath(origin.id);const scale=shortestPropagationPath(origin.id,"map.size.required_qubits");
  return `<aside class="propagation-summary"><header><div><span>選択した起点</span><strong>${esc(origin.label_ja)}</strong><code>${esc(origin.id)}</code></div><button data-clear-propagation>起点を選び直す</button></header><p>矢印は増減を断定せず、下流の再計算・変化可能性を示します。</p><div class="propagation-branches">${propagationChain(outcome,"配送成果への波及")}${propagationChain(scale,"計算規模への波及")}</div></aside>`;
}

function renderCurrentMap() {
  const map=simulationMap();
  const derived=Object.fromEntries(map.derived_values.map((item)=>[item.id,item]));
  const sizes=Object.fromEntries(map.problem_sizes.map((item)=>[item.id,item]));
  const evaluation=map.final_evaluation;
  const openData=map.open_data.map((item)=>mapCard(item,{showUse:true})).join("");
  const parameters=map.model_parameters.map((item)=>mapCard(item)).join("");
  const sizeChain=["map.size.stop_count","map.process.evrp_formulation","map.size.binary_variable_count","map.process.qubo_ising","map.size.required_qubits"];
  const sizeCards=sizeChain.map((id,index)=>`${mapItem(id)?.information_category?mapCard(mapItem(id)):processCard(id)}${index<sizeChain.length-1?propagationEdge(id,sizeChain[index+1]):""}`).join("");
  const fulfillmentCard=`<button class="semantic-node final-evaluation cat-derived ${isDimmed(evaluation)?"dimmed":""} ${nodePropagationClasses(evaluation.id)}" data-map-node="${evaluation.id}"><span class="node-head"><span class="node-category"><b>◎</b>最終評価</span>${badge("未算出","unresolved")}</span><span class="node-label">${esc(evaluation.label_ja)}</span><span class="final-definition">${esc(evaluation.definition_ja)}</span><code>${esc(evaluation.formula)}</code></button>`;
  const propagationControls=`<div class="propagation-toolbar"><div class="mode-switch" role="group" aria-label="表示モード"><button data-propagation-mode="normal" class="${!state.propagationMode?"active":""}">通常表示</button><button data-propagation-mode="propagation" class="${state.propagationMode?"active":""}">波及を見る</button></div>${state.propagationMode?`<div><span class="filter-label">波及の種類</span><div class="propagation-filter">${[["all","すべて"],...Object.entries(propagationMeta).map(([id,meta])=>[id,meta.label])].map(([id,label])=>`<button data-propagation-filter="${id}" class="${state.propagationFilter===id?"active":""}">${label}</button>`).join("")}</div></div>`:""}</div>`;
  $("graph").innerHTML=`<div class="graph-head sim-head"><div><p class="eyebrow">第2階層</p><h2>EV都市配送シミュレーションモデルマップ</h2><p>ある技術・社会条件の変化が、配送問題、計算規模、配送結果へどのように伝播するかを追跡します。</p></div><div class="map-controls"><button data-zoom="out">−</button><button data-zoom="fit">全体表示</button><button data-zoom="in">＋</button></div></div>${propagationControls}${state.propagationMode?renderPropagationSummary():""}<div class="map-legend">${Object.entries(categoryMeta).map(([,meta])=>`<span class="${meta.className}"><b>${meta.icon}</b>${meta.label}</span>`).join("")}${state.propagationMode?Object.entries(propagationMeta).map(([,meta])=>`<span class="propagation-legend ${meta.className}">${meta.label}</span>`).join("")+`<span class="propagation-legend unresolved">点線 = 未確定</span>`:""}<span class="legend-urgency">node header = 情報カテゴリ／線 = 波及種別</span></div><div class="sim-map-viewport"><div class="sim-map" style="--map-zoom:${state.zoom}">
  <section class="semantic-lane open-data-lane"><header><span>01</span><div><h3>オープンデータ</h3><p>採用中の公開データと、その利用先</p></div></header><div class="open-data-grid">${openData}</div></section><div class="lane-arrow">観測データからモデル要素を構成 ↓</div>
  <section class="semantic-lane model-lane"><header><span>02</span><div><h3>モデル化・導出</h3><p>入力を都市・需要条件へ変換</p></div></header><div class="model-source-grid">${mapCard(derived["map.derived.synthetic_delivery_demand"],{showUse:true})}${mapCard(derived["map.derived.road_network"],{showUse:true})}${mapCard(derived["map.derived.traffic_conditions"],{showUse:true})}</div></section>${propagationEdge("map.derived.synthetic_delivery_demand","map.derived.delivery_requests","↓")}
  <section class="instance-workbench"><aside class="parameter-bank"><header><span>03</span><h3>モデル引数</h3><p>研究者が設定・固定する条件</p></header>${parameters}</aside><div class="instance-main"><div class="derived-prep">${mapCard(derived["map.derived.delivery_requests"])}${propagationEdge("map.derived.delivery_requests","map.derived.stops")}${mapCard(derived["map.derived.stops"])}</div>${propagationEdge("map.derived.stops","map.process.common_delivery_instance","↓")} ${processCard("map.process.common_delivery_instance","instance-core")}<div class="matrix-row">${mapCard(derived["map.derived.distance_matrix"])}${mapCard(derived["map.derived.travel_time_matrix"])}${mapCard(derived["map.derived.energy_matrix"])}</div><div class="energy-branch">${processCard("map.process.energy_constraint")}${propagationEdge("map.process.energy_constraint","map.derived.feasible_delivery_plans")}</div></div></section>
  <section class="semantic-lane size-lane"><header><span>04</span><div><h3>問題サイズの伝播</h3><p>Stop数、Binary Variable数、Required Qubitsは別の量</p></div></header><div class="size-chain">${sizeCards}</div><div class="size-dependencies">${mapCard(sizes["map.size.customer_count"])}${mapCard(sizes["map.size.vehicle_count"])}${processCard("map.process.evrp_formulation")}${processCard("map.process.qubo_ising")}</div></section>
  <section class="semantic-lane solution-lane"><header><span>05</span><div><h3>解法・配送計画・交通シミュレーション</h3><p>配送成果への波及</p></div></header><div class="solution-flow">${processCard("map.process.common_delivery_instance")}${propagationEdge("map.process.common_delivery_instance","map.process.optimizers")}${processCard("map.process.optimizers")}${propagationEdge("map.process.optimizers","map.derived.feasible_delivery_plans")}${mapCard(derived["map.derived.feasible_delivery_plans"])}${propagationEdge("map.derived.feasible_delivery_plans","map.derived.selected_delivery_plan")}${mapCard(derived["map.derived.selected_delivery_plan"])}${propagationEdge("map.derived.selected_delivery_plan","map.process.sumo")}${processCard("map.process.sumo")}${propagationEdge("map.process.sumo","map.derived.delivered_parcel_equivalent")}${mapCard(derived["map.derived.delivered_parcel_equivalent"])}</div></section>
  <section class="evaluation-lane"><header><span>06</span><div><h3>最終評価</h3><p>配送成果側の終点は配送需要充足率のみ</p></div></header><div class="evaluation-equation">${mapCard(derived["map.derived.total_parcel_equivalent"],{className:"denominator"})}${propagationEdge("map.derived.total_parcel_equivalent",evaluation.id,"↘")}${fulfillmentCard}${propagationEdge("map.derived.delivered_parcel_equivalent",evaluation.id,"↗")}${mapCard(derived["map.derived.delivered_parcel_equivalent"],{className:"numerator"})}</div><div class="auxiliary-metrics"><strong>終点ではない補助情報</strong>${map.auxiliary_metrics.map((item)=>`<span>${esc(item.label_ja)}：${esc(item.role_ja)}</span>`).join("")}</div></section>
  </div></div>`;
  bindMapNodes();
  bindChainNodes();
  document.querySelectorAll("[data-clear-propagation]").forEach((button)=>{button.onclick=()=>{state.propagationOrigin=null;renderCurrentMap();};});
  document.querySelectorAll("[data-propagation-mode]").forEach((button)=>{button.onclick=()=>{state.propagationMode=button.dataset.propagationMode==="propagation";if(!state.propagationMode)state.propagationOrigin=null;renderCurrentMap();};});
  document.querySelectorAll("[data-propagation-filter]").forEach((button)=>{button.onclick=()=>{state.propagationFilter=button.dataset.propagationFilter;renderCurrentMap();};});
  document.querySelectorAll("[data-zoom]").forEach((button)=>{button.onclick=()=>{if(button.dataset.zoom==="in")state.zoom=Math.min(1.35,state.zoom+0.15);if(button.dataset.zoom==="out")state.zoom=Math.max(0.7,state.zoom-0.15);if(button.dataset.zoom==="fit")state.zoom=1;renderCurrentMap();};});
}

function registryNodeCard(node) { const urgency=node.urgency||"none"; return `<button class="node urgency-${urgency}" data-node="${esc(node.id)}"><span class="label">${esc(displayLabel(node))}</span><code>${esc(node.id)}</code><span class="badges">${badge(text(statusJa,node.status))}${badge(`緊急度: ${text(urgencyJa,urgency)}`,`urgency ${urgency}`)}</span></button>`; }
function renderScenario() {
  const lane=byId(state.registry.scenario_lanes,state.view); const map=simulationMap();
  const roleItems=[...map.model_parameters,...map.derived_values];
  const changing=roleItems.filter((item)=>["scenario_variable","derived"].includes(item.role_by_scenario?.[state.view]));
  const fixed=roleItems.filter((item)=>item.role_by_scenario?.[state.view]==="fixed_condition");
  $("graph").innerHTML=`<div class="graph-head"><p class="eyebrow">シナリオ支線</p><h2>${state.view==="battery"?"技術変化シナリオ":"社会変化シナリオ"}</h2><p>${esc(lane.summary_ja)}</p></div><div class="scenario-role-grid"><section><h3>変化・導出</h3>${changing.map(mapCard).join("")||'<p class="empty">社会変化側の人口・世帯・行動は将来モデル候補です。</p>'}</section><section><h3>固定条件</h3>${fixed.map(mapCard).join("")}</section></div><div class="scenario-flow">${lane.steps.map((step)=>{const node=registryNode(step.node_ref);return `<div class="scenario-step"><span>${esc(step.label_ja)}</span>${registryNodeCard(node)}${badge(text(roleJa,step.role))}<small>${step.value_status==="known"?"確認済み":`未確定：${esc(step.unknown_reason)}`}</small></div>`;}).join("")}</div>`;
  bindMapNodes();bindRegistryNodes();
}
function renderQuantum() {
  $("graph").innerHTML=`<div class="graph-head"><p class="eyebrow">補助縮尺</p><h2>量子問題スケール</h2><p>数値はRegistryに登録されたものだけを表示します。</p></div><div class="quantum-grid">${state.registry.quantum_scales.map((scale)=>`<article class="scale-card"><h3>${esc(scale.label_ja)}</h3><div class="scale-flow">${scale.stages.map((stage,index)=>`<div class="scale-step"><span>0${index+1}</span><strong>${esc(stage.label_ja)}</strong><em class="${stage.value_status!=="known"?"unknown":""}">${stage.value_status==="known"?esc(stage.value):"未算出"}</em><small>${esc(stage.unknown_reason||"確認済み")}</small></div>`).join("")}</div><p>${scale.id==="logistics_evrp"?"Binary Variable数とRequired Qubitsを分離します。Qiskit Aerは古典シミュレータです。":"材料instance・active orbitals・qubit数は未選定で推測しません。"}</p></article>`).join("")}</div>`;
}

function section(title,html){return `<section class="detail-section"><h3>${esc(title)}</h3>${html||"<p>未登録</p>"}</section>`;}
function referenceList(ids){return arr(ids).map((id)=>`<li><strong>${esc(mapItem(id)?.label_ja||id)}</strong><code>${esc(id)}</code></li>`).join("")||"<li>未登録</li>";}
function openMapDetail(id){
  const item=mapItem(id);if(!item)return;const meta=categoryMeta[item.information_category];const category=meta?.label||(item.id===simulationMap().final_evaluation.id?"最終評価":"処理");
  const outgoing=outgoingRelations(item.id);
  const impact=outgoing.length?`<p>${outgoing.map((relation)=>`${esc(relation.effect_label_ja)}ため、<strong>${esc(mapItem(relation.target)?.label_ja||relation.target)}</strong>を${relation.effect_semantics==="direct"?"直接更新します":relation.effect_semantics==="derived"?"再算出します":relation.effect_semantics==="conditional"?"変化させる可能性があります":`再検討します（未確定：${esc(relation.unresolved_reason)}）`}`).join("。<br>")}。</p>`:"<p>Registryに確認済みの下流波及relationはありません。</p>";
  const outcomePath=outcomePropagationPath(item.id);const scalePath=shortestPropagationPath(item.id,"map.size.required_qubits");
  const propagationDetail=`<div class="drawer-propagation-action"><button data-start-propagation="${esc(item.id)}">この変化の波及を見る</button></div>${section("この値が変わると",impact)}${section("波及チェーン",`<div class="drawer-branches">${propagationChain(outcomePath,"配送成果への波及")}${propagationChain(scalePath,"計算規模への波及")}</div>`)}${section("この変化が到達する主な終点",`<dl class="kv"><dt>配送成果側</dt><dd>${outcomePath?"配送需要充足率":"現在formal relationなし"}</dd><dt>計算規模側</dt><dd>${scalePath?"Required Qubits":"現在formal relationなし"}</dd></dl>`)} `;
  const common=`${section("由来",`<p>${esc(text(originJa,item.value_origin))}</p>`)}${item.value_status?section("現在値と状態",`<p class="detail-value">${esc(valueText(item))}</p>${badge(text(statusJa,item.value_status))}${item.unknown_reason?`<p>${esc(item.unknown_reason)}</p>`:""}`):""}`;
  let specific="";
  if(item.id===simulationMap().final_evaluation.id){const scope=item.evaluation_scope;specific=section("定義",`<p>${esc(item.definition_ja)}</p><code>${esc(item.formula)}</code>`)+section("分子・分母",`<dl class="kv"><dt>配送済需要</dt><dd>${esc(mapItem(item.numerator_ref).label_ja)}</dd><dt>総配送需要</dt><dd>${esc(mapItem(item.denominator_ref).label_ja)}</dd></dl>`)+section("どの範囲での評価か",`<dl class="kv"><dt>対象地域</dt><dd>${esc(scope.geography||"未確定")}<small>${esc(scope.geography_unknown_reason)}</small></dd><dt>対象時間</dt><dd>${esc(scope.time||"未確定")}<small>${esc(scope.time_unknown_reason)}</small></dd><dt>対象scenario</dt><dd>${esc(scope.scenario||"未確定")}<small>${esc(scope.scenario_unknown_reason)}</small></dd></dl>`);}
  else if(item.information_category==="open_data") specific=section("データソース",`<p><strong>${esc(item.provider)}</strong></p><p>${esc(item.description_ja)}</p><dl class="kv"><dt>Source ID</dt><dd>${item.source_registry_ids.map(esc).join("<br>")}</dd><dt>対象地域</dt><dd>${esc(item.geographic_scope)}</dd><dt>対象時点</dt><dd>${esc(item.time_basis)}</dd><dt>単位</dt><dd>${esc(item.unit)}</dd><dt>採用状態</dt><dd>${item.adoption_status==="adopted"?"採用中":esc(item.adoption_status)}</dd></dl>`)+section("このデータが決めるもの",`<ul>${referenceList(item.used_by)}</ul>`)+section("repo上の入力ファイル",item.repo_input_paths.map((path)=>`<code class="path">${esc(path)}</code>`).join(""))+section("外部URL",item.external_urls.map((url)=>`<a href="${esc(url)}" target="_blank" rel="noreferrer">${esc(url)}</a>`).join("<br>"));
  else if(item.information_category==="model_parameter") specific=section("意味",`<p>${esc(item.definition_ja||item.unknown_reason)}</p><dl class="kv"><dt>単位</dt><dd>${esc(item.unit)}</dd><dt>緊急度</dt><dd>${badge(text(urgencyJa,item.urgency),`urgency ${item.urgency}`)}</dd></dl>`)+section("シナリオ別role",`<dl class="kv"><dt>現在</dt><dd>${esc(text(roleJa,item.role_by_scenario.current))}</dd><dt>技術変化</dt><dd>${esc(text(roleJa,item.role_by_scenario.battery))}</dd><dt>社会変化</dt><dd>${esc(text(roleJa,item.role_by_scenario.social))}</dd></dl>`)+section("使用先",`<ul>${referenceList(item.used_by)}</ul>`);
  else if(item.information_category==="derived_value"||item.information_category==="problem_size") specific=section(item.information_category==="problem_size"?"この問題サイズを決めるもの":"上流",`<ul>${referenceList(item.determined_by)}</ul>`)+section("下流",`<ul>${referenceList(item.used_by)}</ul>`)+section("定義",`<p>${esc(item.definition_ja||"Registryに追加説明は未登録")}</p><dl class="kv"><dt>単位</dt><dd>${esc(item.unit)}</dd><dt>未確定理由</dt><dd>${esc(text(reasonJa,item.unknown_reason_type))}</dd></dl>`);
  else if(item.registry_node_ref){const node=registryNode(item.registry_node_ref);specific=section("Registry node",`<p>${esc(node.summary_ja)}</p><code>${esc(node.id)}</code><p>${esc(node.current_state_ja)}</p>`);}
  $("detail").innerHTML=`<div class="detail-title"><p class="eyebrow">${esc(category)}</p><h2>${esc(item.label_ja)}</h2><code>${esc(item.id)}</code></div>${propagationDetail}${common}${specific}`;openDrawer();
  document.querySelectorAll("[data-start-propagation]").forEach((button)=>{button.onclick=()=>activatePropagation(button.dataset.startPropagation);});bindChainNodes();
}
function openRegistryDetail(id){const node=registryNode(id);if(!node)return;const links=state.registry.implementation_links.filter((link)=>link.node_ref===id);const files=links.map((link)=>`<article class="file-record">${badge(text(roleJa,link.role))}<code>${esc(link.path)}</code><p>${esc(link.summary_ja)}</p></article>`).join("")||"<p>対応ファイル未確認</p>";$("detail").innerHTML=`<div class="detail-title"><p class="eyebrow">モデル要素</p><h2>${esc(displayLabel(node))}</h2><code>${esc(node.id)}</code></div>${section("何をするものか",`<p>${esc(displayText(node.summary_ja))}</p><p>${esc(displayText(node.current_state_ja))}</p>`)}${section("未確定事項",`<p>${esc(arr(node.not_claimed_ja).join("、")||"なし")}</p>`)}${section("このモデル要素を構成するファイル",files)}`;openDrawer();}
function openDrawer(){$("drawer").classList.add("open");$("drawer").setAttribute("aria-hidden","false");}
function activatePropagation(id){state.view="current";state.propagationMode=true;state.propagationOrigin=id;renderAll();openMapDetail(id);}
function bindMapNodes(){document.querySelectorAll("[data-map-node]").forEach((button)=>{button.onclick=()=>{if(state.propagationMode&&state.view==="current"){state.propagationOrigin=button.dataset.mapNode;renderCurrentMap();}openMapDetail(button.dataset.mapNode);};});}
function bindChainNodes(){document.querySelectorAll("[data-chain-node]").forEach((button)=>{button.onclick=()=>openMapDetail(button.dataset.chainNode);});}
function bindRegistryNodes(){document.querySelectorAll("[data-node]").forEach((button)=>{button.onclick=()=>openRegistryDetail(button.dataset.node);});}

function renderBlockers(){const issues=state.registry.nodes.filter((node)=>node.kind==="issue");$("blockers").innerHTML=`<h2>現在の研究上の未解決事項</h2><div class="blocker-grid">${issues.map((node)=>`<article class="blocker urgency-${node.urgency||"none"}"><button data-node="${esc(node.id)}"><h3>${esc(displayLabel(node))}</h3>${badge(`緊急度: ${text(urgencyJa,node.urgency||"none")}`,`urgency ${node.urgency||"none"}`)}<p>${esc(node.summary_ja)}</p></button></article>`).join("")}</div>`;bindRegistryNodes();}
function renderImplementation(){const grouped=state.registry.implementation_links.reduce((result,link)=>{(result[link.node_ref]||=[]).push(link);return result;},{});$("references").innerHTML=`<h2>研究構成と実装</h2><p class="section-lead">repo file mappingは第2階層のモデル要素へ紐づきます。</p><div class="implementation-grid">${Object.entries(grouped).map(([nodeId,links])=>`<article class="implementation-card"><h3>${esc(displayLabel(registryNode(nodeId)))}</h3><code>${esc(nodeId)}</code>${links.map((link)=>`<div class="file-record">${badge(text(roleJa,link.role))}<code>${esc(link.path)}</code></div>`).join("")}</article>`).join("")}</div>`;}
function renderAdmin(){const registry=state.registry;$("admin").innerHTML=`<details><summary>Portal管理情報</summary><div class="admin-grid"><span>Registry更新日: ${esc(registry.updated_at)}</span><span>Registry version: ${esc(registry.registry_version)}</span><span>schema version: ${esc(registry.schema_version)}</span><span>レビュー状態: ${registry.review.reviewed_by?"レビュー済み":"要レビュー"}</span></div></details>`;}
function renderAll(){renderTabs();renderCategoryFilter();renderContext();renderSummary();if(state.view==="overview")renderOverview();else if(state.view==="current")renderCurrentMap();else if(state.view==="quantum_scale")renderQuantum();else renderScenario();renderBlockers();renderImplementation();renderAdmin();}
function boot(registry){
  state.registry=registry;
  const query=new URLSearchParams(window.location.search);
  const requestedView=query.get("view");
  if(["overview","current","battery","social","quantum_scale"].includes(requestedView))state.view=requestedView;
  const requestedPropagation=query.get("propagate");
  if(requestedPropagation&&mapItem(requestedPropagation)){state.view="current";state.propagationMode=true;state.propagationOrigin=requestedPropagation;}
  renderAll();
  const requestedDetail=query.get("detail");
  if(requestedDetail)openMapDetail(requestedDetail);
  $("search").oninput=(event)=>{state.query=event.target.value.toLowerCase();renderAll();};
  $("close").onclick=()=>{$("drawer").classList.remove("open");$("drawer").setAttribute("aria-hidden","true");};
  document.addEventListener("keydown",(event)=>{if(event.key==="Escape")$("close").click();});
}
fetch("/api/registry").then((response)=>response.json()).then(boot).catch((error)=>{$("graph").innerHTML=`<div class="empty">Registryを読み込めません: ${esc(error.message)}</div>`;});
