import pandas as pd
import re
from datetime import datetime

# ---------- VALIDAÇÕES ----------
def validar_data(valor):
    try:
        return datetime.strptime(valor, "%d/%m/%Y").strftime("%d/%m/%Y")
    except:
        return "INVÁLIDO"

def validar_cpf(valor):
    cpf = re.sub(r"\D", "", str(valor))

    # Precisa ter 11 dígitos
    if len(cpf) != 11:
        return "INVÁLIDO"

    # Elimina CPFs com todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return "INVÁLIDO"

    # Validação dos dígitos verificadores
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]):
            return "INVÁLIDO"

    # Se passou, formata
    return f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"

def validar_valor(valor):
    try:
        val = float(str(valor).replace(",", "."))
        return f"{val:.2f}"
    except:
        return "INVÁLIDO"

# ---------- DETECÇÃO DE ERROS ----------
def detect_issues(df):
    issues = []
    for i, row in df.iterrows():
        row_issues = {}
        if validar_data(str(row["DataNascimento"])) == "INVÁLIDO":
            row_issues["DataNascimento"] = "Data inválida"
        if validar_cpf(str(row["CPF"])) == "INVÁLIDO":
            row_issues["CPF"] = "CPF inválido"
        if validar_valor(str(row["Valor"])) == "INVÁLIDO":
            row_issues["Valor"] = "Valor inválido"

        if row_issues:
            issues.append({"linha": i+1, "erros": row_issues})
    return issues

# ---------- CORREÇÃO ----------
def apply_corrections(df):
    corrected = df.copy()
    corrected["DataNascimento"] = corrected["DataNascimento"].apply(validar_data)
    corrected["CPF"] = corrected["CPF"].apply(validar_cpf)
    corrected["Valor"] = corrected["Valor"].apply(validar_valor)
    return corrected
