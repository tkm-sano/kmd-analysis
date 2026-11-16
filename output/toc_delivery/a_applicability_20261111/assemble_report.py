from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
text = ((HERE/'REPORT_INTRO.md').read_text() + '<!-- score-table:start -->\n'
        + (HERE/'SCORE_TABLE.md').read_text() + '<!-- score-table:end -->\n\n'
        + '## 4. 原資料と各観点の判断根拠\n\n' + (HERE/'SCORE_DETAILS.md').read_text()
        + '\n' + (HERE/'REPORT_CONCLUSION.md').read_text())
(ROOT/'docs/research/toc_delivery_a/A_APPLICABILITY_ASSESSMENT.md').write_text(text)
print('Assessment Markdown assembled from rubric, computed table, reasons and conclusions')
