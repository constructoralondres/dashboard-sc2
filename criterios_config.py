# ══════════════════════════════════════════════════════════════════════════════
# criterios_config.py
# Fuente única de verdad para criterios, etiquetas y ponderaciones de la
# Evaluación de Subcontratos. Reconstruido y validado contra el Excel histórico
# (consolidado.xlsx) — no modificar los pesos sin volver a validar contra datos
# reales, ya que la Nota Final del dashboard y del histórico deben coincidir.
# ══════════════════════════════════════════════════════════════════════════════

# ── Criterios de detalle por área ──────────────────────────────────────────────
CRITERIOS = {
    "TERRENO": [
        "Cumple los plazos internos de ejecución de la obra.",
        "Realiza trabajos en forma limpia, sin dañar trabajos ya realizados.",
        "Asiste a las reuniones de planificación.",
        "Cuenta con Supervisores competentes.",
        "Puntualidad.",
    ],
    "RRHH": [
        "Entrega certificado de la Inspección del Trabajo (Formulario n°30 y 30-1).",
        "Mantiene pactos de horas extras actualizado.",
        "Entrega certificado de Deuda Tributaria con sus respaldos, emitido por Tesorería General Republica.",
        "Entrega Copia de la entrega del Reglamento  Interno a los Trabajadores.",
        "Mantiene libro de Asistencia al dia.",
        "Entrega certificado y mantiene planilla de Leyes Sociales al día.",
        "Realiza y entrega Listado de Trabajadores Vigentes en obra mensual.",
        "Entrega Formulario  Pago de IVA (n°29).",
        "Presenta y entrega respaldo de Libro de Remuneraciones.",
        "Presentación de la Directiva de Funcionamiento con respaldo de jornada excepcional aprobada.",
        "Tiene curso SO10 con certificado vigente y en regla ",
    ],
    "SSOMA": [
        "Cumple con Implementación documental DS 44",
        "Participa en charlas y capacitaciones de obra.",
        "Manejo de accidentes con ingresos a mutualidad en obra",
        "Cumple con todos los protocolos Minsal que le apliquen",
        "Cumple con plan personalizado de actividades (foco en obra).",
        "Acata indicaciones de normas de seguridad  del depto SSOMA en Terreno.",
        "Colabora y participa en actividades extra de gestión en SSOMA.",
        "Utiliza de EPP y soluciones de seguridad en Terreno.",
    ],
    "CALIDAD": [
        "Cumple con las exigencias de calidad.",
        "Entrega protocolos",
        "Resuelve No Conformidades",
        "Demuestra conocimiento técnico.",
    ],
}

ETIQUETAS_CORTAS = {
    "Cumple los plazos internos de ejecución de la obra.": "Plazos",
    "Realiza trabajos en forma limpia, sin dañar trabajos ya realizados.": "Limpieza",
    "Asiste a las reuniones de planificación.": "Reuniones",
    "Cuenta con Supervisores competentes.": "Supervisores",
    "Puntualidad.": "Puntualidad",
    "Entrega certificado de la Inspección del Trabajo (Formulario n°30 y 30-1).": "F30/30-1",
    "Mantiene pactos de horas extras actualizado.": "Horas extras",
    "Entrega certificado de Deuda Tributaria con sus respaldos, emitido por Tesorería General Republica.": "Deuda tributaria",
    "Entrega Copia de la entrega del Reglamento  Interno a los Trabajadores.": "Reglamento interno",
    "Mantiene libro de Asistencia al dia.": "Libro asistencia",
    "Entrega certificado y mantiene planilla de Leyes Sociales al día.": "Leyes sociales",
    "Realiza y entrega Listado de Trabajadores Vigentes en obra mensual.": "Listado trab.",
    "Entrega Formulario  Pago de IVA (n°29).": "IVA F29",
    "Presenta y entrega respaldo de Libro de Remuneraciones.": "Libro remuner.",
    "Presentación de la Directiva de Funcionamiento con respaldo de jornada excepcional aprobada.": "Directiva jornada",
    "Tiene curso SO10 con certificado vigente y en regla ": "Curso SO10",
    "Cumple con Implementación documental DS 44": "DS44",
    "Participa en charlas y capacitaciones de obra.": "Charlas/Cap.",
    "Manejo de accidentes con ingresos a mutualidad en obra": "Accidentes",
    "Cumple con todos los protocolos Minsal que le apliquen": "Minsal",
    "Cumple con plan personalizado de actividades (foco en obra).": "Plan personal.",
    "Acata indicaciones de normas de seguridad  del depto SSOMA en Terreno.": "Normas SSOMA",
    "Colabora y participa en actividades extra de gestión en SSOMA.": "Gestión SSOMA",
    "Utiliza de EPP y soluciones de seguridad en Terreno.": "EPP",
    "Cumple con las exigencias de calidad.": "Exigencias cal.",
    "Entrega protocolos": "Protocolos",
    "Resuelve No Conformidades": "No conformid.",
    "Demuestra conocimiento técnico.": "Conocim. técn.",
}

TODOS_CRITERIOS = [c for lista in CRITERIOS.values() for c in lista]

# ── Ponderación de cada criterio dentro de su área (suman 1.0 por área) ────────
# Reconstruido a partir de la fila de pesos del Excel consolidado (fila 5,
# columnas V:AZ) y validado numéricamente contra ~39 evaluaciones reales.
CRITERIO_WEIGHTS = {
    "TERRENO": {
        "Cumple los plazos internos de ejecución de la obra.": 0.30,
        "Realiza trabajos en forma limpia, sin dañar trabajos ya realizados.": 0.20,
        "Asiste a las reuniones de planificación.": 0.20,
        "Cuenta con Supervisores competentes.": 0.20,
        "Puntualidad.": 0.10,
    },
    "RRHH": {
        "Entrega certificado de la Inspección del Trabajo (Formulario n°30 y 30-1).": 0.10,
        "Mantiene pactos de horas extras actualizado.": 0.10,
        "Entrega certificado de Deuda Tributaria con sus respaldos, emitido por Tesorería General Republica.": 0.10,
        "Entrega Copia de la entrega del Reglamento  Interno a los Trabajadores.": 0.10,
        "Mantiene libro de Asistencia al dia.": 0.05,
        "Entrega certificado y mantiene planilla de Leyes Sociales al día.": 0.10,
        "Realiza y entrega Listado de Trabajadores Vigentes en obra mensual.": 0.10,
        "Entrega Formulario  Pago de IVA (n°29).": 0.10,
        "Presenta y entrega respaldo de Libro de Remuneraciones.": 0.10,
        "Presentación de la Directiva de Funcionamiento con respaldo de jornada excepcional aprobada.": 0.05,
        "Tiene curso SO10 con certificado vigente y en regla ": 0.10,
    },
    "SSOMA": {
        "Cumple con Implementación documental DS 44": 0.15,
        "Participa en charlas y capacitaciones de obra.": 0.10,
        "Manejo de accidentes con ingresos a mutualidad en obra": 0.10,
        "Cumple con todos los protocolos Minsal que le apliquen": 0.10,
        "Cumple con plan personalizado de actividades (foco en obra).": 0.10,
        "Acata indicaciones de normas de seguridad  del depto SSOMA en Terreno.": 0.15,
        "Colabora y participa en actividades extra de gestión en SSOMA.": 0.15,
        "Utiliza de EPP y soluciones de seguridad en Terreno.": 0.15,
    },
    "CALIDAD": {
        "Cumple con las exigencias de calidad.": 0.40,
        "Entrega protocolos": 0.20,
        "Resuelve No Conformidades": 0.20,
        "Demuestra conocimiento técnico.": 0.20,
    },
}

# ── Ponderación de cada área en la Nota Final (suman 1.0) ──────────────────────
AREA_WEIGHTS = {
    "TERRENO": 0.34,
    "RRHH": 0.22,
    "SSOMA": 0.22,
    "CALIDAD": 0.22,
}

# ── Umbrales de estado (Nota Final, escala 1 a 7) ──────────────────────────────
UMBRAL_APROBADO = 5.5
UMBRAL_MEJORAR = 4.0

# ── Roles de evaluador → área que califican ────────────────────────────────────
# "terreno" evalúa TERRENO, etc. El admin (rol "admin") no evalúa, gestiona.
ROL_AREA = {
    "terreno": "TERRENO",
    "rrhh": "RRHH",
    "ssoma": "SSOMA",
    "calidad": "CALIDAD",
}
AREA_ROL = {v: k for k, v in ROL_AREA.items()}

ROLES_EVALUADORES = list(ROL_AREA.keys())
AREAS = ["TERRENO", "RRHH", "SSOMA", "CALIDAD"]

# Etiquetas visibles para cada rol. "admin" se muestra como "Desarrollador"
# para no confundirlo con el cargo de obra "Administrador de Obra".
ROL_LABELS = {
    "admin": "Desarrollador",
    "terreno": "Jefe de Terreno",
    "rrhh": "RRHH",
    "ssoma": "SSOMA",
    "calidad": "Calidad",
}
