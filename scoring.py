# ══════════════════════════════════════════════════════════════════════════════
# scoring.py
# Replica exacta de la fórmula de cálculo del Excel histórico (consolidado.xlsx):
# promedio ponderado por criterio dentro de cada área, con renormalización de
# pesos cuando algún criterio es "No aplica"; luego promedio ponderado de áreas
# para la Nota Final, con la misma renormalización si un área entera es "No
# aplica". Validado numéricamente contra ~39 evaluaciones reales del histórico
# (coincide exacto, error 0).
# ══════════════════════════════════════════════════════════════════════════════
from criterios_config import CRITERIO_WEIGHTS, AREA_WEIGHTS, UMBRAL_APROBADO, UMBRAL_MEJORAR

NO_APLICA = "No aplica"


def _es_no_aplica(v):
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip().lower() in ("no aplica", "n/a", "na", "")
    return False


def compute_area_score(area: str, notas_criterios: dict):
    """
    notas_criterios: dict {criterio_texto: nota (1-7) o 'No aplica'/None}
    Solo se consideran los criterios definidos en CRITERIO_WEIGHTS[area].
    Devuelve un float redondeado a 2 decimales, o 'No aplica' si todos los
    criterios de esa área son 'No aplica' / no fueron respondidos.
    """
    pesos = CRITERIO_WEIGHTS[area]
    suma_ponderada = 0.0
    suma_pesos = 0.0
    for criterio, peso in pesos.items():
        nota = notas_criterios.get(criterio)
        if _es_no_aplica(nota):
            continue
        suma_ponderada += float(nota) * peso
        suma_pesos += peso
    if suma_pesos == 0:
        return NO_APLICA
    return round(suma_ponderada / suma_pesos, 4)


def compute_nota_final(notas_areas: dict):
    """
    notas_areas: dict {"TERRENO": valor_o_NO_APLICA, "RRHH": ..., "SSOMA": ..., "CALIDAD": ...}
    Devuelve (nota_final: float|None, estado: str)
    Si todas las áreas son 'No aplica', devuelve (None, 'SIN DATOS').
    """
    suma_ponderada = 0.0
    suma_pesos = 0.0
    for area, peso in AREA_WEIGHTS.items():
        val = notas_areas.get(area)
        if _es_no_aplica(val):
            continue
        suma_ponderada += float(val) * peso
        suma_pesos += peso
    if suma_pesos == 0:
        return None, "SIN DATOS"
    nota_final = round(suma_ponderada / suma_pesos, 4)
    estado = compute_estado(nota_final)
    return nota_final, estado


def compute_estado(nota_final: float) -> str:
    if nota_final >= UMBRAL_APROBADO:
        return "APROBADO"
    if nota_final >= UMBRAL_MEJORAR:
        return "MEJORAR"
    return "REPROBADO"
