# ══════════════════════════════════════════════════════════════════════════════
# auth.py
# Login por usuario/contraseña individual para la Evaluación de Subcontratos en
# línea. Contraseñas con hash bcrypt guardadas en Firestore (usuarios).
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import bcrypt
from pathlib import Path

import firebase_db as fdb
from criterios_config import ROL_LABELS

SESSION_KEY = "eva_sc_usuario"


def _encabezado_login():
    """Logo + botón para volver al dashboard, mostrado arriba de cualquier
    pantalla de login/bootstrap."""
    col_logo, col_btn = st.columns([3, 2])
    with col_logo:
        logo_path = next((p for p in [Path("logo.png"), Path("logo.jpg"), Path("logo.jpeg")] if p.exists()), None)
        if logo_path:
            st.image(str(logo_path), width=160)
    with col_btn:
        st.markdown("<div style='padding-top:18px; text-align:right;'>", unsafe_allow_html=True)
        st.page_link("app_10.py", label="← Volver al dashboard", icon="🏠")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def usuario_actual():
    return st.session_state.get(SESSION_KEY)


def logout():
    if SESSION_KEY in st.session_state:
        del st.session_state[SESSION_KEY]
    st.rerun()


def _hay_usuarios() -> bool:
    return len(fdb.listar_usuarios()) > 0


def _pantalla_bootstrap_admin():
    """Primera vez que se usa el sistema: no hay ningún usuario cargado todavía.
    Permite crear el primer administrador usando la clave maestra de secrets."""
    _encabezado_login()
    st.warning("Aún no hay usuarios configurados. Crea la cuenta de desarrollador inicial.")
    with st.form("bootstrap_admin"):
        clave_maestra = st.text_input("Clave maestra de configuración", type="password",
                                       help="La misma que definiste en los secrets de Streamlit (setup_key)")
        username = st.text_input("Usuario desarrollador (ej: cesar)")
        nombre = st.text_input("Nombre completo")
        password = st.text_input("Contraseña", type="password")
        password2 = st.text_input("Repite la contraseña", type="password")
        enviar = st.form_submit_button("Crear desarrollador")
    if enviar:
        setup_key = st.secrets.get("setup_key", None)
        if not setup_key or clave_maestra != setup_key:
            st.error("Clave maestra incorrecta.")
            return
        if not username or not password:
            st.error("Usuario y contraseña son obligatorios.")
            return
        if password != password2:
            st.error("Las contraseñas no coinciden.")
            return
        fdb.crear_o_actualizar_usuario(
            username=username, password_hash=hash_password(password),
            nombre=nombre or username, rol="admin", obras=[], activo=True,
        )
        st.success("Desarrollador creado. Ya puedes iniciar sesión.")
        st.rerun()


def login_form(titulo: str = "Iniciar sesión"):
    """Muestra el formulario de login. Devuelve True si ya hay sesión activa."""
    if usuario_actual():
        return True

    if not _hay_usuarios():
        _pantalla_bootstrap_admin()
        return False

    _encabezado_login()
    st.markdown(f"### {titulo}")
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        enviar = st.form_submit_button("Ingresar")
    if enviar:
        u = fdb.obtener_usuario(username)
        if not u or not u.get("activo", True):
            st.error("Usuario o contraseña incorrectos.")
        elif not verify_password(password, u.get("password_hash", "")):
            st.error("Usuario o contraseña incorrectos.")
        else:
            st.session_state[SESSION_KEY] = {
                "username": username.strip().lower(),
                "nombre": u.get("nombre", username),
                "rol": u.get("rol"),
                "obras": u.get("obras", []),
            }
            st.rerun()
    return False


def require_login(roles_permitidos=None, titulo: str = "Iniciar sesión") -> dict:
    """
    Bloquea la página hasta que haya login válido (y, si se especifica,
    del rol correcto). Devuelve el dict de usuario si todo OK.
    Uso: usuario = require_login(["admin"])
    """
    if not login_form(titulo):
        st.stop()
    usuario = usuario_actual()
    if roles_permitidos and usuario["rol"] not in roles_permitidos:
        rol_label = ROL_LABELS.get(usuario["rol"], usuario["rol"])
        st.error(f"Tu usuario ({rol_label}) no tiene acceso a esta página.")
        if st.button("Cerrar sesión"):
            logout()
        st.stop()
    return usuario


def logout_button(sidebar: bool = True):
    contenedor = st.sidebar if sidebar else st
    usuario = usuario_actual()
    if usuario:
        rol_label = ROL_LABELS.get(usuario["rol"], usuario["rol"])
        contenedor.markdown(f"**{usuario['nombre']}** · _{rol_label}_")
        if contenedor.button("Cerrar sesión", key="btn_logout"):
            logout()
