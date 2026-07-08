# ══════════════════════════════════════════════════════════════════════════════
# firebase_db.py
# Capa de acceso a Firebase (Firestore) para la Evaluación de Subcontratos en
# línea: usuarios, evaluaciones abiertas/cerradas, respuestas de evaluadores,
# e historial consolidado que se fusiona con consolidado.xlsx en el dashboard.
#
# Requiere un secret en Streamlit llamado "firebase" con el contenido de la
# cuenta de servicio (JSON) del proyecto Firebase "Evaluación de SC".
# Ver GUIA_FIREBASE.md para el paso a paso de configuración.
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date
import re

from criterios_config import AREAS, ROL_AREA


# ── Conexión ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase"])
        # Streamlit guarda saltos de línea de la private_key como texto plano;
        # aseguramos el formato correcto de la clave PEM.
        if "private_key" in cred_dict:
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def _slug(texto: str) -> str:
    s = texto.strip().upper()
    s = (s.replace("Á", "A").replace("É", "E").replace("Í", "I")
           .replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N"))
    s = re.sub(r"[^A-Z0-9]+", "_", s).strip("_")
    return s


def _hoy_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ══════════════════════════════════════════════════════════════════════════════
# USUARIOS
# ══════════════════════════════════════════════════════════════════════════════
def obtener_usuario(username: str):
    db = get_db()
    doc = db.collection("usuarios").document(username.strip().lower()).get()
    return doc.to_dict() if doc.exists else None


def listar_usuarios():
    db = get_db()
    docs = db.collection("usuarios").stream()
    out = []
    for d in docs:
        u = d.to_dict()
        u["username"] = d.id
        out.append(u)
    return sorted(out, key=lambda u: (u.get("rol", ""), u.get("nombre", "")))


def crear_o_actualizar_usuario(username: str, password_hash: str, nombre: str,
                                rol: str, obras: list, activo: bool = True):
    db = get_db()
    db.collection("usuarios").document(username.strip().lower()).set({
        "nombre": nombre,
        "rol": rol,
        "obras": obras,
        "activo": activo,
        "password_hash": password_hash,
        "actualizado_en": _hoy_str(),
    }, merge=True)


def eliminar_usuario(username: str):
    db = get_db()
    db.collection("usuarios").document(username.strip().lower()).delete()


# ══════════════════════════════════════════════════════════════════════════════
# EVALUACIONES ABIERTAS
# ══════════════════════════════════════════════════════════════════════════════
def _doc_id_evaluacion(obra: str, n_eva: int) -> str:
    return f"{_slug(obra)}__N{n_eva}"


# Alias público — usar este desde las páginas en vez del interno con guion bajo.
def doc_id_evaluacion(obra: str, n_eva: int) -> str:
    return _doc_id_evaluacion(obra, n_eva)


def crear_evaluacion(obra: str, n_eva: int, subcontratos: list,
                      fecha_limite: str, creado_por: str, codigo_obra: str = ""):
    """
    subcontratos: lista de dicts {subcontrato, rut, actividad}
    """
    db = get_db()
    doc_id = _doc_id_evaluacion(obra, n_eva)
    db.collection("evaluaciones").document(doc_id).set({
        "obra": obra,
        "codigo_obra": codigo_obra,
        "n_eva": n_eva,
        "subcontratos": subcontratos,
        "estado": "abierta",
        "fecha_apertura": _hoy_str(),
        "fecha_limite": fecha_limite,
        "creado_por": creado_por,
    })
    return doc_id


def obtener_evaluacion(doc_id: str):
    db = get_db()
    doc = db.collection("evaluaciones").document(doc_id).get()
    return doc.to_dict() if doc.exists else None


def listar_evaluaciones(estado: str = None):
    db = get_db()
    q = db.collection("evaluaciones")
    if estado:
        q = q.where("estado", "==", estado)
    docs = q.stream()
    out = []
    for d in docs:
        e = d.to_dict()
        e["doc_id"] = d.id
        out.append(e)
    return sorted(out, key=lambda e: e.get("fecha_apertura", ""), reverse=True)


def evaluacion_abierta_de_obra(obra: str):
    """Devuelve la evaluación con estado 'abierta' más reciente para una obra, o None."""
    abiertas = [e for e in listar_evaluaciones("abierta") if e["obra"] == obra]
    return abiertas[0] if abiertas else None


def siguiente_n_eva(obra: str, n_eva_historico_max: int = 0) -> int:
    """Calcula el próximo N° EVA para una obra considerando Firestore + histórico Excel."""
    todas = listar_evaluaciones()
    max_fb = max([e["n_eva"] for e in todas if e["obra"] == obra], default=0)
    return max(max_fb, n_eva_historico_max) + 1


# ══════════════════════════════════════════════════════════════════════════════
# RESPUESTAS DE EVALUADORES
# ══════════════════════════════════════════════════════════════════════════════
def _resp_doc_id(subcontrato: str, area: str) -> str:
    return f"{_slug(subcontrato)}__{area}"


def guardar_respuesta(doc_id_evaluacion: str, subcontrato: str, area: str,
                       evaluador: str, notas: dict):
    """
    notas: dict {criterio_texto: nota(1-7) o 'No aplica'}
    Sobrescribe si el mismo evaluador ya había enviado (permite corregir
    mientras la evaluación siga abierta).
    """
    db = get_db()
    resp_id = _resp_doc_id(subcontrato, area)
    (db.collection("evaluaciones").document(doc_id_evaluacion)
       .collection("respuestas").document(resp_id).set({
           "subcontrato": subcontrato,
           "area": area,
           "evaluador": evaluador,
           "notas": notas,
           "enviado_en": _hoy_str(),
       }))


def obtener_respuestas(doc_id_evaluacion: str) -> list:
    db = get_db()
    docs = (db.collection("evaluaciones").document(doc_id_evaluacion)
              .collection("respuestas").stream())
    return [d.to_dict() for d in docs]


def progreso_evaluacion(doc_id_evaluacion: str):
    """
    Devuelve dict {subcontrato: {area: bool_enviado}} para mostrarle al admin
    el avance de envíos (4 áreas × N subcontratos).
    """
    evaluacion = obtener_evaluacion(doc_id_evaluacion)
    if not evaluacion:
        return {}
    subcontratos = [s["subcontrato"] for s in evaluacion.get("subcontratos", [])]
    respuestas = obtener_respuestas(doc_id_evaluacion)
    enviado = {(r["subcontrato"], r["area"]) for r in respuestas}
    progreso = {}
    for sc in subcontratos:
        progreso[sc] = {area: (sc, area) in enviado for area in AREAS}
    return progreso


def cerrar_evaluacion(doc_id_evaluacion: str):
    db = get_db()
    db.collection("evaluaciones").document(doc_id_evaluacion).update({
        "estado": "cerrada",
        "fecha_cierre": _hoy_str(),
    })


def reabrir_evaluacion(doc_id_evaluacion: str):
    db = get_db()
    db.collection("evaluaciones").document(doc_id_evaluacion).update({
        "estado": "abierta",
    })


# ══════════════════════════════════════════════════════════════════════════════
# HISTORIAL CONSOLIDADO (evaluaciones ya cerradas y calculadas)
# ══════════════════════════════════════════════════════════════════════════════
def guardar_historial(doc_id_evaluacion: str, filas: list):
    """
    filas: lista de dicts ya con columnas compatibles con el esquema del
    dashboard (N_EVA, CODIGO_OBRA, FECHA, OBRA, SUBCONTRATO, RUT, ACTIVIDAD,
    TERRENO, RRHH, SSOMA, CALIDAD, NOTA_FINAL, ESTADO, + cada criterio).
    Se guarda una fila por subcontrato en la subcolección 'historial'.
    """
    db = get_db()
    batch = db.batch()
    ref = db.collection("evaluaciones").document(doc_id_evaluacion).collection("historial")
    for fila in filas:
        doc_id = _slug(fila["SUBCONTRATO"])
        batch.set(ref.document(doc_id), fila)
    batch.commit()


def obtener_todo_el_historial_app() -> list:
    """Trae todas las filas de historial de todas las evaluaciones CERRADAS (para fusionar con Excel)."""
    db = get_db()
    filas = []
    for e in listar_evaluaciones("cerrada"):
        docs = (db.collection("evaluaciones").document(e["doc_id"])
                  .collection("historial").stream())
        for d in docs:
            filas.append(d.to_dict())
    return filas


# ══════════════════════════════════════════════════════════════════════════════
# DIRECTORIO DE SUBCONTRATISTAS Y PROVEEDORES (maestro de contactos)
# ══════════════════════════════════════════════════════════════════════════════
def _doc_id_subcontratista(nombre: str, rut: str = "", actividad: str = "") -> str:
    """
    Usa el RUT (si existe) como llave — así una reimportación de la planilla
    actualiza en vez de duplicar. Si no hay RUT, se usa nombre+actividad, ya
    que un mismo subcontratista puede tener una fila por cada actividad.
    """
    rut = (rut or "").strip()
    if rut:
        return _slug(rut)
    return _slug(f"{nombre}_{actividad}")


def crear_o_actualizar_subcontratista(nombre: str, rut: str = "", actividad: str = "",
                                       region: str = "", contacto: str = "",
                                       telefono: str = "", correo: str = "",
                                       ultima_fecha_contacto: str = "",
                                       trabajado_londres: str = "No",
                                       comentario: str = "", doc_id: str = None,
                                       actualizado_por: str = ""):
    db = get_db()
    doc_id = doc_id or _doc_id_subcontratista(nombre, rut, actividad)
    db.collection("subcontratistas").document(doc_id).set({
        "nombre": nombre.strip(),
        "rut": (rut or "").strip(),
        "actividad": (actividad or "").strip(),
        "region": (region or "").strip(),
        "contacto": (contacto or "").strip(),
        "telefono": (telefono or "").strip(),
        "correo": (correo or "").strip(),
        "ultima_fecha_contacto": (ultima_fecha_contacto or "").strip(),
        "trabajado_londres": trabajado_londres or "No",
        "comentario": (comentario or "").strip(),
        "actualizado_en": _hoy_str(),
        "actualizado_por": actualizado_por,
    }, merge=True)
    return doc_id


def obtener_subcontratista(doc_id: str):
    db = get_db()
    doc = db.collection("subcontratistas").document(doc_id).get()
    return doc.to_dict() if doc.exists else None


def listar_subcontratistas() -> list:
    db = get_db()
    docs = db.collection("subcontratistas").stream()
    out = []
    for d in docs:
        s = d.to_dict()
        s["doc_id"] = d.id
        out.append(s)
    return sorted(out, key=lambda s: s.get("nombre", ""))


def eliminar_subcontratista(doc_id: str):
    db = get_db()
    db.collection("subcontratistas").document(doc_id).delete()


def importar_subcontratistas_masivo(filas: list, actualizado_por: str = "") -> int:
    """
    filas: lista de dicts con llaves nombre, rut, actividad, region, contacto,
    telefono, correo, ultima_fecha_contacto, trabajado_londres, comentario.
    Hace upsert por lotes (batch) usando RUT (o nombre+actividad) como llave,
    así se puede reimportar la planilla actualizada sin generar duplicados.
    Devuelve la cantidad de filas escritas.
    """
    db = get_db()
    escritas = 0
    filas_validas = [f for f in filas if str(f.get("nombre", "")).strip()]
    for i in range(0, len(filas_validas), 400):
        lote = filas_validas[i:i + 400]
        batch = db.batch()
        for f in lote:
            doc_id = _doc_id_subcontratista(f.get("nombre", ""), f.get("rut", ""), f.get("actividad", ""))
            ref = db.collection("subcontratistas").document(doc_id)
            batch.set(ref, {
                "nombre": str(f.get("nombre", "")).strip(),
                "rut": str(f.get("rut", "") or "").strip(),
                "actividad": str(f.get("actividad", "") or "").strip(),
                "region": str(f.get("region", "") or "").strip(),
                "contacto": str(f.get("contacto", "") or "").strip(),
                "telefono": str(f.get("telefono", "") or "").strip(),
                "correo": str(f.get("correo", "") or "").strip(),
                "ultima_fecha_contacto": str(f.get("ultima_fecha_contacto", "") or "").strip(),
                "trabajado_londres": str(f.get("trabajado_londres", "") or "No").strip(),
                "comentario": str(f.get("comentario", "") or "").strip(),
                "actualizado_en": _hoy_str(),
                "actualizado_por": actualizado_por,
            }, merge=True)
        batch.commit()
        escritas += len(lote)
    return escritas
