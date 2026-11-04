from common import *
sys.path.insert(0,str(O/'rendering_tools/python'))
from docx import Document
from docx.shared import Inches
import latex2mathml.converter,mathml2omml
x=Document();samples=[('original signed subscript',r'M_{Al}=A_{+}t_{Al}\rho_{Al}/2',False),('literal signed subscript',r'M_{Al}=A_{+}t_{Al}\rho_{Al}/2',True),('pos-neg equivalent notation',r'M_{Al}=A_{pos}t_{Al}\rho_{Al}/2',False),('pore volume pos',r'V_{pos}=\frac{c_{pos}}{\rho_{pos}}\frac{\epsilon_{pos}}{1-\epsilon_{pos}}',False),('liquid mass equation',r'M_{liq}=\rho_{liq}(V_{pos}+V_{neg}+V_{sep}+V_{extra})',False)]
for title,s,lit in samples:
 x.add_paragraph(title);el=E.fromstring(('<root xmlns:m="'+NS['m']+'">'+mathml2omml.convert(latex2mathml.converter.convert(s))+'</root>').encode())[0]
 if lit:
  for m in el.xpath('.//m:r',namespaces=NS):
   if ''.join(m.xpath('./m:t/text()',namespaces=NS)) in ['+','−','-']:
    pr=m.find(qn) if False else m.find('{'+NS['m']+'}rPr')
    if pr is None:pr=E.SubElement(m,'{'+NS['m']+'}rPr')
    E.SubElement(pr,'{'+NS['m']+'}lit',{'{'+NS['m']+'}val':'1'})
 x.add_paragraph()._p.append(el)
x.save(O/'MATH_LAYOUT_FIXTURE.docx')
