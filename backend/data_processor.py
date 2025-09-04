import pandas as pd
from date_validator import detect_date_issues
from document_validator import detect_document_issues
from text_validator import detect_text_issues
from number_validator import detect_number_issues

def process_data(df: pd.DataFrame):
    results = {
        'data': df.to_dict('records'),
        'columns': df.columns.tolist(),
        'issues': []
    }

    for col_idx, column in enumerate(df.columns):
        column_data = df[column].tolist()

        date_issues = detect_date_issues(column_data, col_idx, column)
        if date_issues:
            results['issues'].extend(date_issues)

        doc_issues = detect_document_issues(column_data, col_idx, column)
        if doc_issues:
            results['issues'].extend(doc_issues)

        text_issues = detect_text_issues(column_data, col_idx, column)
        if text_issues:
            results['issues'].extend(text_issues)

        number_issues = detect_number_issues(column_data, col_idx, column)
        if number_issues:
            results['issues'].extend(number_issues)

    return results
