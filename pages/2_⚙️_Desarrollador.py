# ══════════════════════════════════════════════════════════════════════════════
# Página: Desarrollador (antes "Admin Evaluaciones")
# Solo para el desarrollador (César). Abrir/cerrar evaluaciones por obra,
# ver avance de envíos de los 4 evaluadores, y gestionar usuarios.
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

import auth
import firebase_db as fdb
import historico
from criterios_config import AREAS, CRITERIOS, ROLES_EVALUADORES, ROL_AREA, ROL_LABELS
from obras_config import ORDEN_OBRAS
from scoring import compute_area_score, compute_nota_final

st.set_page_config(page_title="Desarrollador", page_icon="⚙️", layout="wide")

AZUL = "#1A1846"
NARANJO = "#E18426"

usuario = auth.require_login(roles_permitidos=["admin"], titulo="Ingreso desarrollador")
auth.logout_button()

st.markdown(f"""
<div style="background:{AZUL};padding:18px 24px;border-radius:12px;margin-bottom:20px;border-bottom:4px solid {NARANJO};">
  <div style="color:white;font-size:1.6rem;font-weight:800;">⚙️ Panel del Desarrollador</div>
</div>
""", unsafe_allow_html=True)

tab_abrir, tab_abiertas, tab_usuarios, tab_directorio = st.tabs(
    ["🆕 Abrir evaluación", "📋 Evaluaciones abiertas / cerrar", "👥 Usuarios", "📇 Directorio"])

excel_path = Path("consolidado.xlsx")
df_hist = historico.leer_excel_bruto(excel_path.read_bytes()) if excel_path.exists() else pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ABRIR NUEVA EVALUACIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tab_abrir:
    obra_sel = st.selectbox("Obra", ORDEN_OBRAS, key="obra_abrir")

    ya_abierta = fdb.evaluacion_abierta_de_obra(obra_sel)
    if ya_abierta:
        st.warning(f"Ya hay una evaluación abierta para **{obra_sel}** — N° EVA {ya_abierta['n_eva']}. "
                   f"Ciérrala en la pestaña 'Evaluaciones abiertas' antes de abrir una nueva.")
    else:
        n_eva_max_hist = historico.max_n_eva(df_hist, obra_sel) if not df_hist.empty else 0
        n_eva_nuevo = fdb.siguiente_n_eva(obra_sel, n_eva_max_hist)
        codigo_obra_sugerido = historico.codigo_obra_de(df_hist, obra_sel) if not df_hist.empty else ""

        st.info(f"Se abrirá la evaluación **N° {n_eva_nuevo}** para {obra_sel}.")

        subcontratos_sugeridos = historico.ultimos_subcontratos_obra(df_hist, obra_sel) if not df_hist.empty else []
        if "editor_subcontratos" not in st.session_state or st.session_state.get("editor_obra") != obra_sel:
            st.session_state["editor_subcontratos"] = pd.DataFrame(subcontratos_sugeridos) if subcontratos_sugeridos else pd.DataFrame(
                columns=["subcontrato", "rut", "actividad"])
            st.session_state["editor_obra"] = obra_sel

        st.markdown("**Subcontratos a evaluar** (precargados de la última evaluación — puedes agregar, quitar o editar filas)")
        df_editado = st.data_editor(
            st.session_state["editor_subcontratos"],
            num_rows="dynamic", use_container_width=True, key="data_editor_subcontratos",
            column_config={
                "subcontrato": st.column_config.TextColumn("Subcontrato", required=True),
                "rut": st.column_config.TextColumn("RUT"),
                "actividad": st.column_config.TextColumn("Actividad"),
            },
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_limite = st.date_input("Fecha límite de la evaluación", value=date.today() + timedelta(days=14))
        with col_f2:
            codigo_obra = st.text_input("Código de obra", value=codigo_obra_sugerido)

        if st.button("🚀 Abrir evaluación", type="primary"):
            filas_validas = df_editado.dropna(subset=["subcontrato"])
            filas_validas = filas_validas[filas_validas["subcontrato"].str.strip() != ""]
            if filas_validas.empty:
                st.error("Agrega al menos un subcontrato antes de abrir la evaluación.")
            else:
                subcontratos = filas_validas.to_dict("records")
                doc_id = fdb.crear_evaluacion(
                    obra=obra_sel, n_eva=n_eva_nuevo, subcontratos=subcontratos,
                    fecha_limite=fecha_limite.strftime("%d/%m/%Y"),
                    creado_por=usuario["username"], codigo_obra=codigo_obra,
                )
                st.success(f"Evaluación N°{n_eva_nuevo} de {obra_sel} abierta con {len(subcontratos)} subcontratos.")
                del st.session_state["editor_subcontratos"]
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — EVALUACIONES ABIERTAS: PROGRESO Y CIERRE
# ══════════════════════════════════════════════════════════════════════════════
with tab_abiertas:
    abiertas = fdb.listar_evaluaciones("abierta")
    if not abiertas:
        st.info("No hay evaluaciones abiertas actualmente.")
    for ev in abiertas:
        doc_id = ev["doc_id"]
        with st.expander(f"📋 {ev['obra']} — N° EVA {ev['n_eva']}  (cierra {ev.get('fecha_limite','—')})", expanded=True):
            progreso = fdb.progreso_evaluacion(doc_id)
            subcontratos = ev.get("subcontratos", [])
            n_sub = len(subcontratos)

            tabla = []
            for sc in subcontratos:
                nombre = sc["subcontrato"]
                fila = {"Subcontrato": nombre}
                for area in AREAS:
                    fila[area.title()] = "✅" if progreso.get(nombre, {}).get(area) else "⬜"
                tabla.append(fila)
            df_tabla = pd.DataFrame(tabla)
            st.dataframe(df_tabla, use_container_width=True, height=min(400, 45 + 35 * len(df_tabla)))

            total_celdas = n_sub * len(AREAS)
            enviadas = sum(1 for sc in subcontratos for area in AREAS if progreso.get(sc["subcontrato"], {}).get(area))
            st.progress(enviadas / total_celdas if total_celdas else 0,
                        text=f"Avance total: {enviadas}/{total_celdas} envíos")

            nombres_sc = [sc["subcontrato"] for sc in subcontratos]
            col_flag1, col_flag2 = st.columns(2)
            with col_flag1:
                no_recomendados = st.multiselect(
                    "🚫 Marcar como NO RECOMENDADO (anula la nota calculada)",
                    nombres_sc, key=f"no_rec_{doc_id}")
            with col_flag2:
                no_autorizados = st.multiselect(
                    "⛔ Marcar como NO AUTORIZADO (anula la nota calculada)",
                    nombres_sc, key=f"no_aut_{doc_id}")

            col_a, col_b = st.columns([1, 3])
            with col_a:
                cerrar = st.button("🔒 Cerrar evaluación", key=f"cerrar_{doc_id}")
            if cerrar:
                respuestas = fdb.obtener_respuestas(doc_id)
                # Indexar respuestas por (subcontrato, area) -> notas
                resp_idx = {(r["subcontrato"], r["area"]): r["notas"] for r in respuestas}

                filas_historial = []
                incompletos = []
                for sc in subcontratos:
                    nombre = sc["subcontrato"]
                    notas_areas = {}
                    fila = {
                        "N_EVA": ev["n_eva"], "CODIGO_OBRA": ev.get("codigo_obra", ""),
                        "FECHA": pd.Timestamp.now().strftime("%Y-%m-%d"),
                        "OBRA": ev["obra"].title(), "SUBCONTRATO": nombre,
                        "RUT": sc.get("rut", ""), "ACTIVIDAD": sc.get("actividad", ""),
                    }
                    areas_faltantes = []
                    for area in AREAS:
                        notas = resp_idx.get((nombre, area))
                        if notas is None:
                            areas_faltantes.append(area)
                            notas_areas[area] = "No aplica"
                            fila[area] = None
                        else:
                            valor = compute_area_score(area, notas)
                            notas_areas[area] = valor
                            fila[area] = None if valor == "No aplica" else valor
                            for criterio, nota in notas.items():
                                fila[criterio] = None if str(nota).lower() == "no aplica" else nota
                    if areas_faltantes:
                        incompletos.append((nombre, areas_faltantes))
                    nota_final, estado = compute_nota_final(notas_areas)
                    fila["NOTA_FINAL"] = nota_final
                    if nombre in no_autorizados:
                        fila["ESTADO"] = "NO AUTORIZADO"
                    elif nombre in no_recomendados:
                        fila["ESTADO"] = "NO RECOMENDADO"
                    else:
                        fila["ESTADO"] = estado if estado != "SIN DATOS" else "MEJORAR"
                    filas_historial.append(fila)

                if incompletos:
                    st.warning("Algunos subcontratos quedaron sin respuesta en una o más áreas "
                               "(se guardaron igual, considerando esa área 'No aplica'): " +
                               "; ".join(f"{n} (falta {', '.join(a.title() for a in areas)})" for n, areas in incompletos))

                fdb.guardar_historial(doc_id, filas_historial)
                fdb.cerrar_evaluacion(doc_id)
                st.cache_data.clear()  # fuerza que el dashboard principal recargue con la nueva evaluación
                st.success(f"Evaluación N°{ev['n_eva']} de {ev['obra']} cerrada y consolidada. "
                           f"Ya aparecerá en el dashboard principal.")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — USUARIOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_usuarios:
    st.markdown("#### Usuarios del sistema")
    usuarios = fdb.listar_usuarios()
    if usuarios:
        df_u = pd.DataFrame([{
            "Usuario": u["username"], "Nombre": u.get("nombre", ""),
            "Rol": ROL_LABELS.get(u.get("rol", ""), u.get("rol", "")), "Obras": ", ".join(u.get("obras", [])),
            "Activo": "Sí" if u.get("activo", True) else "No",
        } for u in usuarios])
        st.dataframe(df_u, use_container_width=True)

    st.markdown("#### Crear / editar usuario")
    with st.form("form_usuario"):
        col1, col2 = st.columns(2)
        with col1:
            username_in = st.text_input("Usuario (identificador único, sin espacios)")
            nombre_in = st.text_input("Nombre completo")
            rol_in = st.selectbox("Rol", ["admin"] + ROLES_EVALUADORES,
                                   format_func=lambda r: ROL_LABELS.get(r, r))
        with col2:
            password_in = st.text_input("Contraseña (dejar en blanco para no cambiarla)", type="password")
            obras_in = st.multiselect("Obras asignadas", ORDEN_OBRAS)
            activo_in = st.checkbox("Usuario activo", value=True)
        guardar = st.form_submit_button("💾 Guardar usuario")

    if guardar:
        if not username_in.strip():
            st.error("El nombre de usuario es obligatorio.")
        else:
            existente = fdb.obtener_usuario(username_in)
            if not password_in and not existente:
                st.error("La contraseña es obligatoria para un usuario nuevo.")
            else:
                pw_hash = auth.hash_password(password_in) if password_in else existente.get("password_hash")
                fdb.crear_o_actualizar_usuario(
                    username=username_in, password_hash=pw_hash, nombre=nombre_in,
                    rol=rol_in, obras=obras_in, activo=activo_in,
                )
                st.success(f"Usuario '{username_in}' guardado.")
                st.rerun()

    st.markdown("#### Eliminar usuario")
    if usuarios:
        u_del = st.selectbox("Selecciona usuario a eliminar", [u["username"] for u in usuarios], key="del_user_sel")
        if st.button("🗑️ Eliminar usuario seleccionado"):
            fdb.eliminar_usuario(u_del)
            st.success(f"Usuario '{u_del}' eliminado.")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DIRECTORIO DE SUBCONTRATISTAS Y PROVEEDORES
# ══════════════════════════════════════════════════════════════════════════════
with tab_directorio:
    st.markdown("#### 📥 Importar planilla")
    st.caption("Sube un Excel con columnas NOMBRE, RUT, ACTIVIDAD, REGION, CONTACTO, TELEFONO, CORREO, "
               "ULTIMA_FECHA_CONTACTO, TRABAJADO_LONDRES (Sí/No), COMENTARIO. Si un RUT (o nombre+actividad) "
               "ya existe en el directorio, se actualiza en vez de duplicarse — puedes reimportar cuando quieras.")
    archivo_directorio = st.file_uploader("Excel del directorio", type=["xlsx", "xls"], key="upload_directorio")
    if archivo_directorio is not None:
        try:
            df_import = pd.read_excel(archivo_directorio)
            df_import.columns = [str(c).strip().upper() for c in df_import.columns]
            st.dataframe(df_import.head(10), use_container_width=True)
            st.caption(f"{len(df_import)} filas detectadas. Se muestran las primeras 10.")
            if st.button("🚀 Importar al directorio", type="primary"):
                col_map = {
                    "NOMBRE": "nombre", "RUT": "rut", "ACTIVIDAD": "actividad", "REGION": "region",
                    "CONTACTO": "contacto", "TELEFONO": "telefono", "CORREO": "correo",
                    "ULTIMA_FECHA_CONTACTO": "ultima_fecha_contacto",
                    "TRABAJADO_LONDRES": "trabajado_londres", "COMENTARIO": "comentario",
                }
                filas = []
                for _, row in df_import.iterrows():
                    fila = {v: row.get(k, "") for k, v in col_map.items() if k in df_import.columns}
                    filas.append(fila)
                n = fdb.importar_subcontratistas_masivo(filas, actualizado_por=usuario["username"])
                st.success(f"{n} filas importadas/actualizadas en el directorio.")
                st.rerun()
        except Exception as e:
            st.error(f"No se pudo leer el archivo: {e}")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("#### ➕ Agregar / editar contacto")
    with st.form("form_subcontratista"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_dir = st.text_input("Nombre del subcontratista/proveedor")
            rut_dir = st.text_input("RUT (opcional, pero recomendado)")
            actividad_dir = st.text_input("Actividad")
            region_dir = st.text_input("Región")
        with col2:
            contacto_dir = st.text_input("Nombre de contacto")
            telefono_dir = st.text_input("Teléfono")
            correo_dir = st.text_input("Correo")
            fecha_contacto_dir = st.text_input("Última fecha de contacto (ej: 2026-05-20)")
        trabajado_dir = st.radio("¿Ha trabajado con Londres?", ["No", "Sí"], horizontal=True)
        comentario_dir = st.text_area("Comentario")
        guardar_dir = st.form_submit_button("💾 Guardar contacto")

    if guardar_dir:
        if not nombre_dir.strip():
            st.error("El nombre es obligatorio.")
        else:
            fdb.crear_o_actualizar_subcontratista(
                nombre=nombre_dir, rut=rut_dir, actividad=actividad_dir, region=region_dir,
                contacto=contacto_dir, telefono=telefono_dir, correo=correo_dir,
                ultima_fecha_contacto=fecha_contacto_dir, trabajado_londres=trabajado_dir,
                comentario=comentario_dir, actualizado_por=usuario["username"],
            )
            st.success(f"Contacto '{nombre_dir}' guardado.")
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("#### 📇 Directorio completo")
    subcontratistas = fdb.listar_subcontratistas()
    if not subcontratistas:
        st.info("Aún no hay contactos en el directorio. Impórtalos arriba o agrégalos uno a uno.")
    else:
        df_dir = pd.DataFrame(subcontratistas)
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            busq_dir = st.text_input("Buscar por nombre", key="busq_directorio")
        with col_f2:
            regiones_dir = sorted([r for r in df_dir.get("region", pd.Series()).dropna().unique() if r])
            region_sel = st.selectbox("Filtrar por región", ["Todas"] + regiones_dir, key="filtro_region_dir")
        with col_f3:
            londres_sel = st.selectbox("Trabajado con Londres", ["Todos", "Sí", "No"], key="filtro_londres_dir")

        df_dir_f = df_dir.copy()
        if busq_dir:
            df_dir_f = df_dir_f[df_dir_f["nombre"].str.contains(busq_dir, case=False, na=False)]
        if region_sel != "Todas":
            df_dir_f = df_dir_f[df_dir_f.get("region", "") == region_sel]
        if londres_sel != "Todos":
            df_dir_f = df_dir_f[df_dir_f.get("trabajado_londres", "") == londres_sel]

        cols_mostrar = ["nombre", "rut", "actividad", "region", "contacto", "telefono", "correo",
                        "ultima_fecha_contacto", "trabajado_londres", "comentario"]
        cols_mostrar = [c for c in cols_mostrar if c in df_dir_f.columns]
        st.caption(f"{len(df_dir_f)} de {len(df_dir)} contactos")
        st.dataframe(df_dir_f[cols_mostrar], use_container_width=True, height=450)

        st.markdown("#### 🗑️ Eliminar contacto")
        opciones_del = {f"{s['nombre']} — {s.get('actividad','')}": s["doc_id"] for s in subcontratistas}
        sel_del = st.selectbox("Selecciona el contacto a eliminar", list(opciones_del.keys()), key="del_dir_sel")
        if st.button("🗑️ Eliminar contacto seleccionado"):
            fdb.eliminar_subcontratista(opciones_del[sel_del])
            st.success("Contacto eliminado.")
            st.rerun()
