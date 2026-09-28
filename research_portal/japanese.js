/* Localize visible text only. IDs, URLs, status classes and commands stay exact. */
let japaneseTerms = {};
let japanesePattern;
function initializeJapanese(terms) {
  japaneseTerms = terms;
  const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  japanesePattern = new RegExp(`(?<![A-Za-z0-9_])(?:${Object.keys(terms).sort((a,b)=>b.length-a.length).map(escape).join('|')})(?![A-Za-z0-9_])`, 'g');
}
function japaneseText(value) {
  const text = String(value ?? '');
  if (Object.hasOwn(japaneseTerms, text)) return japaneseTerms[text];
  // Machine references and quoted commands must remain usable for verification.
  return text.split(/(`[^`]*`|https?:\/\/\S+|(?:[A-Za-z0-9_.-]+\/)+[A-Za-z0-9_./#-]+|\b[A-Za-z0-9_.-]+\.(?:md|py|json|yml|yaml|csv|xml|svg|png|txt|pdf|html)\b|\b[a-f0-9]{32,}\b)/g)
    .map((part,index)=>index%2 ? part : part.replace(japanesePattern, word=>japaneseTerms[word])).join('');
}
function localizeJapanese(root = document.body) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    if (node.parentElement.closest('code, pre, script, style')) continue;
    node.nodeValue = japaneseText(node.nodeValue);
  }
  for (const element of root.querySelectorAll('[aria-label], [title]')) {
    for (const attribute of ['aria-label','title']) {
      if (element.hasAttribute(attribute)) element.setAttribute(attribute,japaneseText(element.getAttribute(attribute)));
    }
  }
  for (const name of root.querySelectorAll('svg .node-name')) {
    const text = name.textContent;
    if (text.length <= 12) continue;
    name.replaceChildren();
    const lines = [text.slice(0,12),text.slice(12)];
    lines.forEach((line,index)=>{
      const span = document.createElementNS('http://www.w3.org/2000/svg','tspan');
      span.setAttribute('x','85');span.setAttribute('y',String(17+index*15));
      if (line.length > 12) {span.setAttribute('textLength','150');span.setAttribute('lengthAdjust','spacingAndGlyphs');}
      span.textContent=line;name.append(span);
    });
    const status=name.parentElement.querySelector('.node-status');
    if (status) status.setAttribute('y','49');
  }
}
