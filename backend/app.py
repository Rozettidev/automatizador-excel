from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import io
from data_processor import process_data


app = Flask(__name__)
# Em produção, restringe origens: CORS(app, resources={r"/api/*": {"origins": "http://localhost:8000"}})
CORS(app)

# Opcional: limite de upload (ex.: 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    # ==== ARQUIVO ENVIADO ====
    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        filename = (file.filename or "").lower()
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig', on_bad_lines='skip')
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file, engine='openpyxl')
            else:
                return jsonify({'error': 'Formato de arquivo não suportado'}), 400
        except Exception as e:
            return jsonify({'error': f'Falha ao ler arquivo: {str(e)}'}), 400

    # ==== TEXTO COLADO (CSV em string) ====
    elif 'data' in request.form:
        import csv, io
        raw = (request.form.get('data') or '').strip()
        if not raw:
            return jsonify({'error': 'Nenhum dado fornecido'}), 400

        # tenta detectar , ou ;
        sample = '\n'.join(raw.splitlines()[:10])
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;')
            sep = dialect.delimiter
        except Exception:
            first = raw.splitlines()[0] if raw.splitlines() else ''
            sep = ';' if first.count(';') > first.count(',') else ','

        try:
            df = pd.read_csv(io.StringIO(raw), sep=sep, engine='python', on_bad_lines='skip')
        except Exception as e:
            return jsonify({'error': f'Falha ao ler texto colado: {str(e)}'}), 400
    else:
        return jsonify({'error': 'Nenhum dado fornecido'}), 400

    # processa
    results = process_data(df)
    return jsonify(results), 200

@app.route('/api/apply_corrections', methods=['POST'])
def apply_corrections():
    payload = request.get_json()
    if not payload or 'data' not in payload or 'corrections' not in payload:
        return jsonify({'error': 'Dados ou correções ausentes'}), 400

    df = pd.DataFrame(payload['data'])
    corrections = payload['corrections']
    columns = payload.get('columns')

    for correction in corrections:
        row = correction['row']
        col_name = correction.get('column_name')
        if col_name is None:
            if columns is None:
                return jsonify({'error': 'Falta column_name ou columns para mapear índices'}), 400
            col_index = correction['column']
            if col_index < 0 or col_index >= len(columns):
                return jsonify({'error': f'Índice de coluna inválido: {col_index}'}), 400
            col_name = columns[col_index]

        new_value = correction['suggested_value']
        df.at[row, col_name] = new_value

    return jsonify({'corrected_data': df.to_dict('records')}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)