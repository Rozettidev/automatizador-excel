import re
import pandas as pd

def _strip_sign(s: str):
    s = s.strip()
    sign = ''
    if s and s[0] in '+-':
        sign, s = s[0], s[1:]
    return sign, s

def _only_digits(s: str | None):
    if s is None:
        return ''
    return re.sub(r'\D', '', s)

def _format_thousand_br(integer_digits: str) -> str:
    integer_digits = (integer_digits or '').lstrip('0') or '0'
    out = ''
    while len(integer_digits) > 3:
        out = '.' + integer_digits[-3:] + out
        integer_digits = integer_digits[:-3]
    return integer_digits + out

def _detect_separators(s: str):
    has_dot = '.' in s
    has_comma = ',' in s
    if has_dot and has_comma:
        last_dot = s.rfind('.')
        last_comma = s.rfind(',')
        decimal = ',' if last_comma > last_dot else '.'
        thousand = '.' if decimal == ',' else ','
        return thousand, decimal
    if has_comma:
        parts = s.split(',')
        # se a última parte tem 1-2 dígitos, tratamos como decimal BR
        if parts[-1].isdigit() and 1 <= len(parts[-1]) <= 2:
            return '.', ','
        # caso contrário, provavelmente vírgula de milhar (US)
        return ',', None
    if has_dot:
        parts = s.split('.')
        if parts[-1].isdigit() and 1 <= len(parts[-1]) <= 2:
            return ',', '.'
        return '.', None
    return None, None

def _to_components(s: str):
    sign, s = _strip_sign(s)
    s = re.sub(r'\s+', '', s)
    thousand, decimal = _detect_separators(s)
    if decimal:
        idx = s.rfind(decimal)
        integer_part = s[:idx]
        decimal_part = s[idx+1:]
    else:
        integer_part = s
        decimal_part = None
    if thousand:
        integer_part = integer_part.replace(thousand, '')
    integer_digits = _only_digits(integer_part)
    decimal_digits = _only_digits(decimal_part) if decimal_part is not None else ''
    return sign, integer_digits, decimal_digits

def _to_br(value: str) -> str:
    sign, intd, decd = _to_components(value)
    integer_br = _format_thousand_br(intd)
    if decd:
        return f"{sign}{integer_br},{decd}"
    return f"{sign}{integer_br}"

def _numeric_like(s: str) -> bool:
    return bool(re.search(r'\d', s))

def detect_number_issues(column_data, col_idx, column_name):
    issues = []
    non_empty = [v for v in column_data if v is not None and not pd.isna(v) and str(v) != '']
    if not non_empty:
        return []

    for row_idx, raw in enumerate(column_data):
        if raw is None or pd.isna(raw) or raw == '':
            continue
        value_str = str(raw)
        if not _numeric_like(value_str):
            continue
        suggested = _to_br(value_str)
        if suggested != value_str:
            issues.append({
                'row': row_idx,
                'column': col_idx,
                'column_name': column_name,
                'value': value_str,
                'issue_type': 'number_format',
                'description': 'Formato numérico inconsistente. Normalizando para padrão BR (milhar "." e decimal ",").',
                'suggested_value': suggested
            })
    return issues