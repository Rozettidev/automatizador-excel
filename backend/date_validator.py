from datetime import datetime
import re
from dateutil import parser
import pandas as pd

def detect_date_issues(column_data, col_idx, column_name):
    issues = []
    date_formats = {}
    date_pattern = re.compile(r'(\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4})')

    non_empty = [v for v in column_data if v is not None and not pd.isna(v) and v != '']
    if not non_empty:
        return []

    date_count = sum(1 for v in non_empty if date_pattern.search(str(v)))
    if date_count < 0.3 * len(non_empty):
        return []

    for row_idx, value in enumerate(column_data):
        if value is None or pd.isna(value) or value == '':
            continue

        value_str = str(value)
        if not date_pattern.search(value_str):
            continue

        try:
            parsed_date = parser.parse(value_str, fuzzy=True)
            if '/' in value_str:
                sep = '/'
            elif '-' in value_str:
                sep = '-'
            elif '.' in value_str:
                sep = '.'
            else:
                sep = None

            if sep:
                parts = value_str.split(sep)
                if len(parts[0]) == 4:
                    date_format = f'yyyy{sep}mm{sep}dd'
                elif len(parts[-1]) == 4:
                    date_format = f'dd{sep}mm{sep}yyyy'
                else:
                    if int(parts[0]) > 12:
                        date_format = f'dd{sep}mm{sep}yyyy'
                    else:
                        date_format = f'mm{sep}dd{sep}yyyy'

                date_formats[date_format] = date_formats.get(date_format, 0) + 1

                if len(date_formats) > 1:
                    standard_value = parsed_date.strftime('%d/%m/%Y')
                    issues.append({
                        'row': row_idx,
                        'column': col_idx,
                        'column_name': column_name,
                        'value': value_str,
                        'issue_type': 'date_format',
                        'description': f'Formato de data inconsistente: {value_str}',
                        'suggested_value': standard_value
                    })
        except Exception:
            pass

    return issues
