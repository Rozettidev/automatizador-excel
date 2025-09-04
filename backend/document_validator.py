import re
import pandas as pd
from validate_docbr import CPF, CNPJ

cpf_validator = CPF()
cnpj_validator = CNPJ()

def detect_document_issues(column_data, col_idx, column_name):
    issues = []

    cpf_pattern = re.compile(r'^(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})$')
    cnpj_pattern = re.compile(r'^(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}|\d{14})$')

    non_empty = [v for v in column_data if v is not None and not pd.isna(v) and v != '']
    if not non_empty:
        return []

    doc_count = 0
    for value in non_empty:
        value_str = str(value)
        if cpf_pattern.fullmatch(value_str) or cnpj_pattern.fullmatch(value_str):
            doc_count += 1

    if doc_count < 0.3 * len(non_empty):
        return []

    for row_idx, value in enumerate(column_data):
        if value is None or pd.isna(value) or value == '':
            continue

        value_str = str(value)

        if cpf_pattern.fullmatch(value_str):
            clean = re.sub(r'[^\d]', '', value_str)
            if not cpf_validator.validate(clean):
                issues.append({
                    'row': row_idx, 'column': col_idx, 'column_name': column_name,
                    'value': value_str, 'issue_type': 'invalid_cpf',
                    'description': f'CPF inválido: {value_str}', 'suggested_value': None
                })
            elif value_str != cpf_validator.mask(clean):
                issues.append({
                    'row': row_idx, 'column': col_idx, 'column_name': column_name,
                    'value': value_str, 'issue_type': 'cpf_format',
                    'description': f'Formatação de CPF inconsistente: {value_str}',
                    'suggested_value': cpf_validator.mask(clean)
                })

        elif cnpj_pattern.fullmatch(value_str):
            clean = re.sub(r'[^\d]', '', value_str)
            if not cnpj_validator.validate(clean):
                issues.append({
                    'row': row_idx, 'column': col_idx, 'column_name': column_name,
                    'value': value_str, 'issue_type': 'invalid_cnpj',
                    'description': f'CNPJ inválido: {value_str}', 'suggested_value': None
                })
            elif value_str != cnpj_validator.mask(clean):
                issues.append({
                    'row': row_idx, 'column': col_idx, 'column_name': column_name,
                    'value': value_str, 'issue_type': 'cnpj_format',
                    'description': f'Formatação de CNPJ inconsistente: {value_str}',
                    'suggested_value': cnpj_validator.mask(clean)
                })

    return issues