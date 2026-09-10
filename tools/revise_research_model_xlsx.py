from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research_model_3page_ja.xlsx"
TARGET = ROOT / "research_model_3page_ja_revised.xlsx"
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("x", NS)


def cell_map(root: ET.Element) -> dict[str, ET.Element]:
    return {c.attrib["r"]: c for c in root.findall(f".//{{{NS}}}c")}


def clear_cell(cell: ET.Element) -> None:
    for key in ("t",):
        cell.attrib.pop(key, None)
    for child in list(cell):
        cell.remove(child)


def set_text(cells: dict[str, ET.Element], ref: str, value: str) -> None:
    cell = cells[ref]
    style = cell.attrib.get("s")
    clear_cell(cell)
    if style is not None:
        cell.attrib["s"] = style
    cell.attrib["t"] = "inlineStr"
    is_node = ET.SubElement(cell, f"{{{NS}}}is")
    text = ET.SubElement(is_node, f"{{{NS}}}t")
    text.text = value


def set_number(cells: dict[str, ET.Element], ref: str, value: int | float) -> None:
    cell = cells[ref]
    style = cell.attrib.get("s")
    clear_cell(cell)
    if style is not None:
        cell.attrib["s"] = style
    v = ET.SubElement(cell, f"{{{NS}}}v")
    v.text = str(value)


def set_formula(cells: dict[str, ET.Element], ref: str, formula: str) -> None:
    cell = cells[ref]
    style = cell.attrib.get("s")
    clear_cell(cell)
    if style is not None:
        cell.attrib["s"] = style
    f = ET.SubElement(cell, f"{{{NS}}}f")
    f.text = formula
    # Do not retain a stale cached value. Excel is instructed to recalculate.


def clear(cells: dict[str, ET.Element], ref: str) -> None:
    cell = cells[ref]
    style = cell.attrib.get("s")
    clear_cell(cell)
    if style is not None:
        cell.attrib["s"] = style


def rewrite_sheet1(data: bytes) -> bytes:
    root = ET.fromstring(data)
    cells = cell_map(root)
    replacements = {
        "B4": "令和2年国勢調査500mメッシュ（e-Stat）",
        "C4": "世帯総数／合成世帯数",
        "F4": "参照入力",
        "J4": "T001141034（世帯総数）。384353は既存の合成世帯成果物で、観測世帯数ではない",
        "B5": "国勢調査・宅配統計・宅配受取調査",
        "C5": "旧トップダウン需要目標",
        "F5": "旧proxy",
        "J5": "82023は旧parcel-equivalent/day。新しいcustomer需要の確定値ではない",
        "B6": "既存合成需要成果物",
        "F6": "履歴成果物",
        "J6": "82246は旧生成段階の実現値。新Common Delivery Instanceへ自動投入しない",
        "B7": "既存合成request成果物",
        "F7": "履歴成果物",
        "J7": "73547は旧request行数。customer数・配送完了件数とは別単位",
        "B8": "候補地点／既存mapping",
        "F8": "候補母集団",
        "J8": "39956はC_all候補母集団。customer集合C_sとnは実験ごとに抽出する",
        "B9": "受入SUMO network（OSM由来）",
        "B10": "受入SUMO network（OSM由来）",
        "B11": "受入SUMO network（OSM由来）",
        "J9": "SUMO 1.24.0、受入authorityとnetwork hashを別途固定",
        "J10": "有向edge数。OSM単独の規模値として扱わない",
        "J11": "lane数。OSM単独の規模値として扱わない",
        "B12": "EV技術",
        "C12": "バッテリー容量",
        "B13": "EV技術",
        "C13": "エネルギー消費率",
        "E13": "kWh/km",
        "B14": "充電",
        "C14": "充電出力",
        "B15": "経済",
        "C15": "電力単価",
        "E15": "円/kWh",
        "B16": "経済",
        "C16": "人件費",
        "E16": "円/有給時間",
        "B17": "経済",
        "C17": "保守費用",
        "E17": "円/km",
        "J12": "車両profileと出典を固定。未入力値を補完しない",
        "J13": "航続距離は独立入力にせず、battery・usable SOC・消費率から検算する",
        "J14": "充電地点の出力・互換性・利用可能条件を別途固定",
        "J15": "時間帯・契約形態が必要。未入力",
        "J16": "賃金だけでなく雇用主負担と有給時間の定義が必要。未入力",
        "J17": "距離比例費と車齢・電池交換等の固定費を分離。未入力",
    }
    for ref, value in replacements.items():
        set_text(cells, ref, value)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rewrite_sheet2(data: bytes) -> bytes:
    root = ET.fromstring(data)
    cells = cell_map(root)
    replacements = {
        "B9": "バッテリー容量",
        "B10": "エネルギー消費率",
        "C10": "kWh/km",
        "H10": "航続距離はbattery・usable SOC・消費率から導出・検算",
        "B11": "充電出力",
        "B12": "出発時SOC",
        "C12": "%",
        "H12": "初期SOC。未入力",
        "B13": "帰着時最低SOC",
        "C13": "%",
        "G13": "入力",
        "H13": "設定する場合のみ適用。未入力",
        "B14": "車両台数",
        "C14": "台",
        "G14": "入力",
        "H14": "Baselineは単一depot。車両台数は未入力",
        "B15": "最大運行時間",
        "C15": "時間/台/日",
        "H15": "設定した場合にHard Constraintとして適用。未入力",
        "B17": "総荷物需要（旧proxy）",
        "H17": "82246は旧生成済みproxy。新B2C instanceの確定値ではない",
        "B18": "旧配送依頼件数",
        "H18": "73547は旧成果物。新customer数nとは別に記録",
        "B19": "候補地点数",
        "H19": "39956はC_all。customer集合C_sのnではない",
        "B28": "車両積載容量",
        "B29": "問題サイズ n=|C_s|",
        "C29": "customer",
        "H29": "候補母集団C_allから抽出する実験パラメータ",
        "H33": "kWh × 電力単価。時間帯・契約条件を固定",
        "H34": "有給時間 × loaded wage。運転・作業・待機・充電の境界を固定",
        "H35": "走行距離 × 変動保守費。車齢・電池交換費は分離",
        "H36": "車両取得／リース・保険・税等を日次換算",
        "H37": "充電による追加機会費用。人件費と二重計上しない",
        "H38": "未充足ペナルティ。失注・再配達費・社会的費用の意味を分離",
    }
    for ref, value in replacements.items():
        set_text(cells, ref, value)
    # Scenario demand remains blank until scenario input is supplied.
    set_formula(cells, "E17", 'IF(OR(E6="",E7=""),"",E6*E7)')
    set_formula(cells, "F17", 'IF(OR(F6="",F7=""),"",F6*F7)')
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rewrite_sheet3(data: bytes) -> bytes:
    root = ET.fromstring(data)
    cells = cell_map(root)
    # Summary block: link to the actual result rows, not the economic input rows.
    summary = {
        "C4": "'Page2_Model_Flow'!D17", "D4": "'Page2_Model_Flow'!E17", "E4": "'Page2_Model_Flow'!F17",
        "C5": "D18", "D5": "E18", "E5": "F18",
        "C6": "D19", "D6": "E19", "E6": "F19",
        "C7": "D20", "D7": "E20", "E7": "F20",
        "C8": "D21", "D8": "E21", "E8": "F21",
        "C9": "D22", "D9": "E22", "E9": "F22",
        "C10": "D23", "D10": "E23", "E10": "F23",
        "C11": "D46", "D11": "E46", "E11": "F46",
        "C12": "D47", "D12": "E47", "E12": "F47",
        "D13": "D48", "E13": "E48", "F13": "F48",
        "H5": "D40", "I5": "E40", "J5": "F40",
        "H6": "D41", "I6": "E41", "J6": "F41",
        "H7": "D42", "I7": "E42", "J7": "F42",
        "H8": "D43", "I8": "E43", "J8": "F43",
        "H9": "D44", "I9": "E44", "J9": "F44",
        "H10": "D45", "I10": "E45", "J10": "F45",
        "H11": "D46", "I11": "E46", "J11": "F46",
    }
    for ref, formula in summary.items():
        set_formula(cells, ref, formula)

    for col in "DEF":
        set_formula(cells, f"{col}19", f'IFERROR({col}18/\'Page2_Model_Flow\'!{col}17,"")')
        set_formula(cells, f"{col}20", f'IF(OR(\'Page2_Model_Flow\'!{col}17="",{col}18=""),"",\'Page2_Model_Flow\'!{col}17-{col}18)')
        set_formula(cells, f"{col}28", f'IFERROR({col}21/\'Page2_Model_Flow\'!{col}14,"")')
        set_formula(cells, f"{col}29", f'IFERROR({col}23/\'Page2_Model_Flow\'!{col}14,"")')
        set_formula(cells, f"{col}30", f'IFERROR({col}24/\'Page2_Model_Flow\'!{col}14,"")')
        set_formula(cells, f"{col}31", f'IFERROR({col}20/\'Page2_Model_Flow\'!{col}17,"")')
        set_formula(cells, f"{col}32", f'IFERROR({col}20/\'Page2_Model_Flow\'!{col}17,"")')
        set_formula(cells, f"{col}40", f'IF(OR({col}23="",{col}33=""),"",{col}23*{col}33)')
        set_formula(cells, f"{col}41", f'IF(OR({col}22="",{col}34=""),"",{col}22*{col}34)')
        set_formula(cells, f"{col}42", f'IF(OR({col}21="",{col}35=""),"",{col}21*{col}35)')
        set_formula(cells, f"{col}43", f'IF(OR(\'Page2_Model_Flow\'!{col}14="",{col}36=""),"",\'Page2_Model_Flow\'!{col}14*{col}36)')
        set_formula(cells, f"{col}44", f'IF(OR({col}24="",{col}37=""),"",{col}24*{col}37)')
        set_formula(cells, f"{col}45", f'IF(OR({col}20="",{col}38=""),"",{col}20*{col}38)')
        set_formula(cells, f"{col}46", f'IF(COUNT({col}40:{col}45)=0,"",SUM({col}40:{col}45))')
        set_formula(cells, f"{col}47", f'IFERROR({col}46/{col}18,"")')
    set_number(cells, "D48", 0)
    set_formula(cells, "E48", 'IF(OR(E46="",$D$46=""),"",E46-$D$46)')
    set_formula(cells, "F48", 'IF(OR(F46="",$D$46=""),"",F46-$D$46)')
    for ref in ["D49", "E49", "F49", "D50", "E50", "F50"]:
        clear(cells, ref)
    set_text(cells, "B48", "ベースライン比コスト差")
    set_text(cells, "C48", "円/日")
    set_text(cells, "H48", "シナリオ総費用－ベースライン総費用")
    set_text(cells, "B49", "")
    set_text(cells, "C49", "")
    set_text(cells, "B50", "")
    set_text(cells, "C50", "")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rewrite_chart(data: bytes) -> bytes:
    text = data.decode("utf-8")
    series = re.findall(r"<c:ser>.*?</c:ser>", text, flags=re.S)
    if series:
        ser = series[-1]
        ser = ser.replace("<c:v>Total modeled cost</c:v>", "<c:v>モデル総費用</c:v>")
        first = text.index("<c:ser>")
        last = text.rindex("</c:ser>") + len("</c:ser>")
        text = text[:first] + ser + text[last:]
        text = text.replace("='Page3_Results'!", "'Page3_Results'!")
    return text.encode("utf-8")


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"source not found: {SOURCE}")
    with zipfile.ZipFile(SOURCE) as zin:
        entries = {name: zin.read(name) for name in zin.namelist()}
    entries["xl/worksheets/sheet1.xml"] = rewrite_sheet1(entries["xl/worksheets/sheet1.xml"])
    entries["xl/worksheets/sheet2.xml"] = rewrite_sheet2(entries["xl/worksheets/sheet2.xml"])
    entries["xl/worksheets/sheet3.xml"] = rewrite_sheet3(entries["xl/worksheets/sheet3.xml"])
    entries["xl/drawings/charts/chart1.xml"] = rewrite_chart(entries["xl/drawings/charts/chart1.xml"])
    workbook = entries["xl/workbook.xml"].decode("utf-8")
    if "calcPr" not in workbook:
        workbook = workbook.replace("</x:workbook>", '<x:calcPr fullCalcOnLoad="1" forceFullCalc="1" calcMode="auto" /></x:workbook>')
    entries["xl/workbook.xml"] = workbook.encode("utf-8")
    with zipfile.ZipFile(TARGET, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)
    print(TARGET)


if __name__ == "__main__":
    main()
