# ══════════════════════════════════════════════════════════════════════════════
# historico.py
# Lectura del Excel histórico (consolidado.xlsx) a un DataFrame estándar,
# compartida entre el dashboard (app_10.py), la página Admin y el merge con
# las evaluaciones nuevas hechas en la app (Firebase).
# ══════════════════════════════════════════════════════════════════════════════
import openpyxl
import pandas as pd
from io import BytesIO

from criterios_config import TODOS_CRITERIOS

ESTADOS_VALIDOS = ("APROBADO", "MEJORAR", "REPROBADO", "NO RECOMENDADO", "NO AUTORIZADO")

COLUMNAS_BASE = [
    "N_EVA", "CODIGO_OBRA", "FECHA", "OBRA", "SUBCONTRATO", "RUT",
    "ACTIVIDAD", "TERRENO", "RRHH", "SSOMA", "CALIDAD", "NOTA_FINAL", "ESTADO",
]


def leer_excel_bruto(file_bytes) -> pd.DataFrame:
    """
    file_bytes: bytes del archivo consolidado.xlsx
    Devuelve un DataFrame con el mismo esquema de columnas que usa el
    dashboard: N_EVA, CODIGO_OBRA, FECHA, OBRA, SUBCONTRATO, RUT, ACTIVIDAD,
    TERRENO, RRHH, SSOMA, CALIDAD, NOTA_FINAL, ESTADO + columnas de criterio.
    """
    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb["Consolidado"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[5]
    data = [r for r in rows[6:] if r[0] is not None and r[19] in ESTADOS_VALIDOS]
    df = pd.DataFrame(data, columns=header)
    df = df.rename(columns={
        "N° EVA": "N_EVA", "CÓDIGO OBRA": "CODIGO_OBRA", "FECHA EVALUACIÓN": "FECHA",
        "NOMBRE SUBCONTRATO": "SUBCONTRATO", "NOTA FINAL (1 a 7)": "NOTA_FINAL",
        "ESTADO": "ESTADO", "TERRENO": "TERRENO", "RRHH": "RRHH", "SSOMA": "SSOMA", "CALIDAD": "CALIDAD",
    })
    num_cols = ["NOTA_FINAL", "TERRENO", "RRHH", "SSOMA", "CALIDAD"] + TODOS_CRITERIOS
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["N_EVA"] = pd.to_numeric(df["N_EVA"], errors="coerce")
    df["OBRA"] = df["OBRA"].str.strip().str.title()
    df["SUBCONTRATO"] = df["SUBCONTRATO"].str.strip().str.title()
    df["ESTADO"] = df["ESTADO"].str.strip().str.upper()
    if "ACTIVIDAD" in df.columns:
        df["ACTIVIDAD"] = df["ACTIVIDAD"].str.strip().str.title()
    return df


def ultimos_subcontratos_obra(df: pd.DataFrame, obra: str) -> list:
    """Lista de subcontratos (subcontrato, rut, actividad) de la última N° EVA registrada para una obra."""
    sub = df[df["OBRA"].str.upper() == obra.strip().upper()]
    if sub.empty:
        return []
    ultima = sub["N_EVA"].max()
    filas = sub[sub["N_EVA"] == ultima].drop_duplicates(subset=["SUBCONTRATO"])
    out = []
    for _, r in filas.iterrows():
        out.append({
            "subcontrato": r["SUBCONTRATO"],
            "rut": str(r.get("RUT", "")) if pd.notna(r.get("RUT")) else "",
            "actividad": r.get("ACTIVIDAD", "") if pd.notna(r.get("ACTIVIDAD")) else "",
        })
    return out


def max_n_eva(df: pd.DataFrame, obra: str) -> int:
    sub = df[df["OBRA"].str.upper() == obra.strip().upper()]
    if sub.empty or sub["N_EVA"].isna().all():
        return 0
    return int(sub["N_EVA"].max())


def codigo_obra_de(df: pd.DataFrame, obra: str) -> str:
    sub = df[df["OBRA"].str.upper() == obra.strip().upper()]
    if sub.empty or "CODIGO_OBRA" not in sub.columns:
        return ""
    vals = sub["CODIGO_OBRA"].dropna().unique()
    return str(vals[0]) if len(vals) else ""
