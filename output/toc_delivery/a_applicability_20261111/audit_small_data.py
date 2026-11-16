"""Audit provided fields and nine OD inputs. Does not generate a delivery plan."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
from datetime import datetime
from io import BytesIO, StringIO
import csv
import json
import math
from inspect_workbooks import inspect_xlsx

HERE = Path(__file__).resolve().parent


def column(cell):
    return ''.join(c for c in cell if c.isalpha())


def main():
    sources = HERE / 'sources'
    result = {}
    with ZipFile(sources / 'data.zip') as z:
        orders = inspect_xlsx(BytesIO(z.read('orders/orders.xlsx')), True)
        matrices = []
        for day in range(1, 10):
            path = f'time_and_distance_matrices/day_{day}/distance_matrix_{day}.xlsx'
            rows = inspect_xlsx(BytesIO(z.read(path)), True)[0]['all_rows']
            cols = {column(k): int(v) for k, v in rows[0].items() if v is not None}
            labels, matrix = set(cols.values()), {}
            for row in rows[1:]:
                label = next((v for k, v in row.items() if column(k) == 'A'), None)
                if label is None or not label.isdigit() or int(label) not in labels:
                    continue
                for k, v in row.items():
                    if column(k) in cols:
                        matrix[int(label), cols[column(k)]] = float(v) if v is not None else None
            request_rows = orders[day-1]['all_rows'][1:]
            ids = [int(next(v for k, v in row.items() if column(k) == 'A')) for row in request_rows if any(v is not None for v in row.values())]
            matrices.append({'day': day, 'nodes_including_depot': len(labels), 'order_count': len(ids),
                             'unique_order_count': len(set(ids)), 'matrix_cells': len(matrix),
                             'missing_or_nonfinite': sum(v is None or not math.isfinite(v) for v in matrix.values()),
                             'negative': sum(v is not None and v < 0 for v in matrix.values()),
                             'nonzero_diagonal': sum(matrix.get((i, i)) != 0 for i in labels),
                             'asymmetric_directed_pairs': sum(matrix.get((i, j)) != matrix.get((j, i)) for i in labels for j in labels if i != j),
                             'orders_equal_matrix_customers': set(ids) == labels - {0}})
        result['delivering_matrices'] = matrices
        result['delivering_no_route_sequence_file'] = not any('route' in n.lower() or 'sequence' in n.lower() for n in z.namelist())
    raw = inspect_xlsx(sources / 'URBANE_BCL_LL_Data_(Raw).xlsx', True)[0]['all_rows']
    descriptions = Counter(next((v for k, v in row.items() if column(k) == 'E'), None) for row in raw[2:])
    header_names = {v for v in raw[1].values() if v}
    result['urbane_raw'] = {'header': raw[1], 'description_counts': dict(descriptions),
                           'data_rows_including_tests': len(raw)-2,
                           'has_dedicated_vehicle_trip_or_loading_ready_columns': bool(header_names & {'vehicle_id', 'trip_id', 'berth_id', 'load_start', 'ready'})}
    prefix = (sources / 'QUEUE_PARTIAL_64KiB.csv').read_bytes()
    # Drop the truncated final record; GB18030 is an observed decoding, not a publisher guarantee.
    text = prefix[:prefix.rfind(b'\n')+1].decode('gb18030')
    rows = list(csv.DictReader(StringIO(text)))
    first, fmt = rows[0], '%Y-%m-%d %H:%M:%S'
    difference = lambda end: (datetime.strptime(first[end], fmt) - datetime.strptime(first['queue_start_time'], fmt)).total_seconds()/60
    result['queue_prefix'] = {'bytes': len(prefix), 'complete_rows': len(rows), 'header': list(first),
                              'queue_types': dict(Counter(r['queue_type'] for r in rows)),
                              'observed_unique_plan_ids': len({r['plan_no'] for r in rows}),
                              'declared_queuing_time_first_row': float(first['queuing_time']),
                              'calling_minus_queue_start_min_first_row': difference('calling_time'),
                              'entry_minus_queue_start_min_first_row': difference('entry_time'),
                              'interpretation': 'arithmetic only; no validated mapping to common ready/load_start; prefix not representative sample'}
    (HERE/'DATA_QUALITY_CHECKS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print('Audited 9 distance matrices, URBANE fields and 247 complete queue-prefix records; no routes generated')


if __name__ == '__main__':
    main()
