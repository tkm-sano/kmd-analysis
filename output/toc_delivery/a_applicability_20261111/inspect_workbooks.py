"""Inspect XLSX/XML and ZIP inventories without executing third-party code."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import json
import posixpath

HERE = Path(__file__).resolve().parent
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def inspect_xlsx(source, include_rows=False):
    with ZipFile(source) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets = []
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS):
            target = rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            root = ET.fromstring(z.read(target))
            rows = []
            for row in root.findall('s:sheetData/s:row', NS):
                cells = {}
                for cell in row:
                    value = cell.find('s:v', NS)
                    text = value.text if value is not None else ''.join(cell.find('s:is', NS).itertext()) if cell.find('s:is', NS) is not None else None
                    if cell.attrib.get('t') == 's' and text is not None:
                        text = strings[int(text)]
                    cells[cell.attrib['r']] = text
                rows.append(cells)
            item = {'sheet': sheet.attrib['name'], 'dimension': root.find('s:dimension', NS).attrib if root.find('s:dimension', NS) is not None else None, 'row_count': len(rows), 'first_rows': rows[:5]}
            if include_rows:
                item['all_rows'] = rows
            sheets.append(item)
        return sheets


def main():
    sources = HERE / 'sources'
    results = {}
    for p in sorted(sources.glob('*.xlsx')):
        results[p.name] = inspect_xlsx(p)
    archive = sources / 'data.zip'
    if archive.exists():
        from io import BytesIO
        with ZipFile(archive) as z:
            results['Delivering_Data_inventory'] = z.namelist()
            for n in z.namelist():
                if n.lower().endswith('.xlsx') and ('orders' in n.lower() or 'distance_matrix_1.xlsx' in n):
                    results[n] = inspect_xlsx(BytesIO(z.read(n)))
    (HERE / 'WORKBOOK_INSPECTION.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    for name, result in results.items():
        print(name, str(result)[:4500])


if __name__ == '__main__':
    main()
