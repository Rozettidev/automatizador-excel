import re
import pandas as pd

def detect_text_issues(column_data, col_idx, column_name):
    issues = []

    non_empty = [v for v in column_data if v is not None and not pd.isna(v) and v != '']
    if not non_empty:
        return []

    text_count = sum(1 for v in non_empty if isinstance(v, str) and not v.isdigit())
    if text_count < 0.3 * len(non_empty):
        return []

    uppercase = lowercase = titlecase = mixed = 0
    for v in non_empty:
        if not isinstance(v, str):
            continue
        if v.isupper():
            uppercase += 1
        elif v.islower():
            lowercase += 1
        elif v == v.title():
            titlecase += 1
        else:
            mixed += 1

    total = uppercase + lowercase + titlecase + mixed
    if total == 0:
        return []

    if uppercase / total > 0.5:
        predominant = 'UPPERCASE'
    elif lowercase / total > 0.5:
        predominant = 'lowercase'
    elif titlecase / total > 0.5:
        predominant = 'Title Case'
    else:
        predominant = None

    if predominant:
        for row_idx, value in enumerate(column_data):
            if value is None or pd.isna(value) or value == '' or not isinstance(value, str):
                continue
            if predominant == 'UPPERCASE' and not value.isupper():
                issues.append({
                    'row': row_idx, 'column': col_idx, 'column_name': column_name,
                    'value': value, 'issue_type': 'text_case',
                    'description': 'Texto não está em maiúsculas como o padrão da coluna',
                    'suggested_value': value.upper()
                })
            elif predominant == 'lowercase' and not value.islower():
                issues.append({
                    'row': row_idx, 'column': col_idx, 'column_name': column_name,
                    'value': value, 'issue_type': 'text_case',
                    'description': 'Texto não está em minúsculas como o padrão da coluna',
                    'suggested_value': value.lower()
                })
            elif predominant == 'Title Case' and value != value.title():
                issues.append({
                    'row': row_idx, 'column': col_idx, 'column_name': column_name,
                    'value': value, 'issue_type': 'text_case',
                    'description': 'Texto não está em formato título como o padrão da coluna',
                    'suggested_value': value.title()
                })

    return issues