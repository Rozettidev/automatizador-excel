import os
import re
import csv
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd

# ---- paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend"))
HTML_DIR = os.path.join(FRONTEND_DIR, "html")
ASSETS_DIR = os.path.join(FRONTEND_DIR, "assets")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="/")
CORS(app)

# ======================================================================
# Helpers
# ======================================================================

def get_col(df: pd.DataFrame, name_lower: str):
    for c in df.columns:
        if str(c).strip().lower() == name_lower:
            return c
    return None

_rgx_digits = re.compile(r"\D+")

def only_digits(s) -> str:
    if s is None:
        return ""
    return _rgx_digits.sub("", str(s))

def parse_number(value) -> float:
    """
    Aceita:
      - R$ 1.234,56
      - 1.234,56
      - 1,234.56
      - 119,9
      - 119.9
      - 119
    """
    if value is None:
        return 0.0
    s = str(value)

    # remove textos monetários e espaços
    s = re.sub(r"(?i)\s*(r\$|reais|real)\s*", "", s)
    s = s.replace("\xa0", "").strip()

    # se vier em formato já-numérico, retorna
    try:
        return float(s)
    except Exception:
        pass

    # detecta qual é o separador decimal:
    # regra: se tiver vírgula e ponto, assume BR (ponto milhar, vírgula decimal)
    # se tiver só vírgula, assume vírgula decimal
    # se tiver só ponto, assume ponto decimal
    has_comma = "," in s
    has_dot = "." in s

    if has_comma and has_dot:
        # BR: remove pontos (milhar) e troca vírgula por ponto
        s = s.replace(".", "").replace(",", ".")
    elif has_comma and not has_dot:
        # vírgula decimal
        s = s.replace(",", ".")
    else:
        # só ponto ou nenhum
        pass

    # remove qualquer coisa que não seja dígito, ponto ou sinal
    s = re.sub(r"[^0-9\.\-]+", "", s)

    # se ficou vazio, 0
    if s == "" or s == "." or s == "-":
        return 0.0

    try:
        return float(s)
    except Exception:
        return 0.0

def parse_qty(value) -> float:
    if value is None:
        return 0.0
    s = str(value).lower().replace(",", ".")
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m:
        return 0.0
    try:
        return float(m.group(0))
    except Exception:
        return 0.0

# ---------------- CPF/CNPJ ----------------
def cpf_valid(digs: str) -> bool:
    if len(digs) != 11 or len(set(digs)) == 1:
        return False
    s = sum(int(digs[i]) * (10 - i) for i in range(9))
    r = (s * 10) % 11
    dv1 = 0 if r == 10 else r
    s = sum(int(digs[i]) * (11 - i) for i in range(10))
    r = (s * 10) % 11
    dv2 = 0 if r == 10 else r
    return dv1 == int(digs[9]) and dv2 == int(digs[10])

def cnpj_valid(digs: str) -> bool:
    if len(digs) != 14 or len(set(digs)) == 1:
        return False
    p1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    p2 = [6] + p1
    r1 = sum(int(digs[i])*p1[i] for i in range(12)) % 11
    dv1 = 0 if r1 < 2 else 11 - r1
    r2 = sum(int(digs[i])*p2[i] for i in range(13)) % 11
    dv2 = 0 if r2 < 2 else 11 - r2
    return dv1 == int(digs[12]) and dv2 == int(digs[13])

def fmt_cpf(d: str) -> str:
    return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"

def fmt_cnpj(d: str) -> str:
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"

# ======================================================================
# Leitura CSV (prioriza ; do BR)
# ======================================================================
def read_csv_br_first(path: str) -> pd.DataFrame:
    # 1) tenta ; (BR)
    try:
        return pd.read_csv(path, sep=";", engine="python", encoding="utf-8-sig")
    except Exception:
        pass
    try:
        return pd.read_csv(path, sep=";", engine="python", encoding="latin-1")
    except Exception:
        pass

    # 2) tenta autodetectar
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(8192)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,")
                sep = dialect.delimiter
            except Exception:
                sep = ";" if sample.count(";") >= sample.count(",") else ","
        return pd.read_csv(path, sep=sep, engine="python", encoding="utf-8-sig")
    except Exception:
        pass

    # 3) tenta ,
    try:
        return pd.read_csv(path, sep=",", engine="python", encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path, sep=",", engine="python", encoding="latin-1")

# ======================================================================
# Normalização + Correções
# ======================================================================
def normalize_and_fix(df: pd.DataFrame) -> pd.DataFrame:
    # nomes minúsculos
    df.columns = [str(c).strip().lower() for c in df.columns]

    # aliases
    aliases = {
        "data":"data", "date":"data",
        "produto":"produto","product":"produto",
        "categoria":"categoria","category":"categoria",
        "quantidade":"quantidade","qtd":"quantidade","qtde":"quantidade",
        "preco_unitario":"preco_unitario","preço_unitario":"preco_unitario",
        "preço unitário":"preco_unitario","preco unitario":"preco_unitario",
        "preco":"preco_unitario","preço":"preco_unitario","valor_unitario":"preco_unitario",
        "cpf":"cpf","cnpj":"cnpj",
        "vendedor":"vendedor","seller":"vendedor",
        "valor_total":"valor_total","total":"valor_total","total_venda":"valor_total"
    }
    df = df.rename(columns={c: aliases.get(c, c) for c in df.columns})

    # garante colunas
    needed = ["data","produto","categoria","quantidade","preco_unitario","cpf","cnpj","vendedor","valor_total"]
    for c in needed:
        if c not in df.columns:
            df[c] = ""

    # limpeza básica
    df["data"] = df["data"].astype(str).str.strip()
    df["produto"] = df["produto"].astype(str).str.strip().str.title()
    df["categoria"] = df["categoria"].astype(str).str.strip().str.title()
    df["quantidade"] = df["quantidade"].apply(parse_qty)
    df["preco_unitario"] = df["preco_unitario"].apply(parse_number)

    # CPF/CNPJ sobrescrito com Inválido quando inválido
    def fix_cpf(x):
        d = only_digits(x)
        if cpf_valid(d):
            return fmt_cpf(d)
        return "Inválido"

    def fix_cnpj(x):
        d = only_digits(x)
        if cnpj_valid(d):
            return fmt_cnpj(d)
        return "Inválido"

    df["cpf"] = df["cpf"].apply(fix_cpf)
    df["cnpj"] = df["cnpj"].apply(fix_cnpj)

    # vendedor (título e espaços)
    df["vendedor"] = (
        df["vendedor"].astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.title()
    )

    # valor_total: se vier zerado/vazio, recalcula = quantidade * preço
    def calc_total(row):
        vt = parse_number(row.get("valor_total", 0))
        if vt > 0:
            return vt
        q = row.get("quantidade", 0) or 0
        p = row.get("preco_unitario", 0) or 0
        return round(float(q) * float(p), 2)

    df["valor_total"] = df.apply(calc_total, axis=1)

    # ordena/filtra
    df = df[["data","produto","categoria","quantidade","preco_unitario","cpf","cnpj","vendedor","valor_total"]]
    df = df[df["produto"].astype(str).str.strip() != ""].reset_index(drop=True)
    return df

# ======================================================================
# Rotas páginas
# ======================================================================
@app.route("/")
def index():
    return send_from_directory(HTML_DIR, "index.html")

@app.route("/login")
def login():
    return send_from_directory(HTML_DIR, "login.html")

@app.route("/dashboard")
def dashboard():
    return send_from_directory(HTML_DIR, "dashboard.html")

@app.route("/assets/<path:fname>")
def assets(fname):
    return send_from_directory(ASSETS_DIR, fname)

# ======================================================================
# API
# ======================================================================
ALLOWED = {".csv"}

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Arquivo sem nome."}), 400

    filename = secure_filename(f.filename)
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED:
        return jsonify({"error": "Apenas .csv é aceito."}), 400

    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)

    try:
        df = read_csv_br_first(save_path)
        if df.empty:
            return jsonify({"error":"Planilha sem linhas."}), 400

        issues = []
        cpf_c = get_col(df, "cpf")
        if cpf_c:
            bad = sum(1 for v in df[cpf_c] if len(only_digits(v)) != 11)
            if bad:
                issues.append(f"{bad} CPFs problemáticos")
        cnpj_c = get_col(df, "cnpj")
        if cnpj_c:
            bad = sum(1 for v in df[cnpj_c] if len(only_digits(v)) != 14)
            if bad:
                issues.append(f"{bad} CNPJs problemáticos")

        return jsonify({"filename": filename, "issues": issues})
    except Exception as e:
        return jsonify({"error": f"Falha ao ler CSV: {e}"}), 500

@app.route("/correct", methods=["POST"])
def correct():
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error":"filename ausente"}), 400

    src = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(src):
        return jsonify({"error":"Arquivo não encontrado"}), 404

    try:
        raw = read_csv_br_first(src)
        fixed = normalize_and_fix(raw)
        out_name = f"corrigido_{filename}"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        fixed.to_csv(out_path, sep=";", index=False, encoding="utf-8-sig", float_format="%.2f")
        return send_file(out_path, as_attachment=True, download_name=out_name)
    except Exception as e:
        return jsonify({"error": f"Falha ao corrigir: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
