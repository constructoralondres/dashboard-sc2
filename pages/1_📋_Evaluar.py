# ══════════════════════════════════════════════════════════════════════════════
# Página: Evaluar
# Para los 4 evaluadores de terreno (Jefe de Terreno, RRHH, SSOMA, Calidad).
# Cada uno ve solo los criterios de su área asignada, para las obras y la
# evaluación abierta que le correspondan.
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
from pathlib import Path
from PIL import Image

import auth
import firebase_db as fdb
from criterios_config import CRITERIOS, ROL_AREA

_favicon_path = next((p for p in [Path("logo_icono.jpeg"), Path("logo_icono.png")] if p.exists()), None)
_page_icon = Image.open(_favicon_path) if _favicon_path else "📋"

st.set_page_config(page_title="Evaluar Subcontratos", page_icon=_page_icon, layout="wide")

AZUL = "#1A1846"
NARANJO = "#E18426"

usuario = auth.require_login(titulo="Ingreso evaluadores")
auth.logout_button()

rol = usuario["rol"]
if rol == "admin":
    st.info("Tu usuario es administrador. Usa la página **Admin Evaluaciones** para abrir/cerrar evaluaciones.")
    st.stop()

area = ROL_AREA.get(rol)
if not area:
    st.error(f"Tu usuario tiene un rol no reconocido ({rol}). Contacta al administrador.")
    st.stop()

st.markdown(f"""
<div style="background:{AZUL};padding:18px 24px;border-radius:12px;margin-bottom:20px;border-bottom:4px solid {NARANJO};">
  <div style="color:white;font-size:1.5rem;font-weight:800;">📋 Evaluar Subcontratos — Área {area.title()}</div>
  <div style="color:{NARANJO};font-size:0.95rem;font-weight:600;">Evaluador: {usuario['nombre']}</div>
</div>
""", unsafe_allow_html=True)

obras_usuario = usuario.get("obras", [])
if not obras_usuario:
    st.warning("Tu usuario no tiene obras asignadas todavía. Contacta al administrador.")
    st.stop()

# ── Obras con evaluación abierta ────────────────────────────────────────────
obras_con_abierta = []
for obra in obras_usuario:
    ev = fdb.evaluacion_abierta_de_obra(obra)
    if ev:
        obras_con_abierta.append((obra, ev))

if not obras_con_abierta:
    st.info("No tienes ninguna evaluación abierta en tus obras asignadas por el momento.")
    st.stop()

opciones_obra = [f"{o}  —  N° EVA {e['n_eva']}  (cierra {e.get('fecha_limite','—')})" for o, e in obras_con_abierta]
idx_sel = st.selectbox("Selecciona la obra / evaluación", options=range(len(opciones_obra)),
                        format_func=lambda i: opciones_obra[i])
obra_sel, evaluacion = obras_con_abierta[idx_sel]
doc_id = fdb.doc_id_evaluacion(obra_sel, evaluacion["n_eva"])

subcontratos = evaluacion.get("subcontratos", [])
respuestas = fdb.obtener_respuestas(doc_id)
enviados = {r["subcontrato"]: r for r in respuestas if r["area"] == area}

n_total = len(subcontratos)
n_enviados = len(enviados)
st.progress(n_enviados / n_total if n_total else 0,
            text=f"Enviados: {n_enviados} / {n_total} subcontratos")

criterios_area = CRITERIOS[area]
OPCIONES_NOTA = ["No aplica", 1, 2, 3, 4, 5, 6, 7]

st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

for sc in subcontratos:
    nombre_sc = sc["subcontrato"]
    ya_enviado = nombre_sc in enviados
    icono = "✅" if ya_enviado else "⬜"
    with st.expander(f"{icono}  {nombre_sc}  —  {sc.get('actividad','')}"):
        notas_previas = enviados.get(nombre_sc, {}).get("notas", {})
        valores = {}
        with st.form(f"form_{doc_id}_{nombre_sc}_{area}"):
            for criterio in criterios_area:
                prev = notas_previas.get(criterio, "No aplica")
                idx_prev = OPCIONES_NOTA.index(prev) if prev in OPCIONES_NOTA else 0
                valores[criterio] = st.select_slider(
                    criterio, options=OPCIONES_NOTA, value=OPCIONES_NOTA[idx_prev],
                    key=f"crit_{doc_id}_{nombre_sc}_{criterio}",
                )
            enviar = st.form_submit_button("💾 Guardar evaluación" if not ya_enviado else "💾 Actualizar evaluación")
        if enviar:
            fdb.guardar_respuesta(doc_id, nombre_sc, area, usuario["username"], valores)
            st.success(f"Evaluación de {nombre_sc} guardada.")
            st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)
st.caption(f"Evaluación N°{evaluacion['n_eva']} de {obra_sel} · Área {area.title()} · Cierra {evaluacion.get('fecha_limite','—')}")
