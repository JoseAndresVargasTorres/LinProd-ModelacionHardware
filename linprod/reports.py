"""
reports.py — Módulo 4: Reportería PDF
Proyecto LinProd | CE-5507 Modelación Hardware/Software Orientado a Objetos
Instituto Tecnológico de Costa Rica | I Semestre 2026

Genera un reporte PDF profesional a partir de los datos entregados por
Simulator.get_stats().  No modifica ningún otro módulo del proyecto.

Dependencia externa:
    pip install reportlab

Ejecución autónoma (sin GUI) desde la raíz del repositorio:
    python3 -m linprod.reports
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Optional

# ── ReportLab ─────────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
    PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Paleta de colores (alineada con la GUI del Módulo 3) ──────────────────────
COLOR_AZUL_OSCURO  = colors.HexColor("#004680")
COLOR_AZUL_CLARO   = colors.HexColor("#4f8cff")
COLOR_VERDE        = colors.HexColor("#34d399")
COLOR_AMBAR        = colors.HexColor("#fbbf24")
COLOR_ROJO         = colors.HexColor("#f87171")
COLOR_MORADO       = colors.HexColor("#a78bfa")
COLOR_FILA_PAR     = colors.HexColor("#f0f4ff")
COLOR_FILA_IMPAR   = colors.white
COLOR_BORDE_TABLA  = colors.HexColor("#cccccc")
COLOR_TEXTO_OSCURO = colors.HexColor("#1a1f2e")

# ── Fuente con soporte UTF-8 ──────────────────────────────────────────────────
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    # macOS / Homebrew
    "/opt/homebrew/share/fonts/dejavu-fonts/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
]

def _register_fonts() -> tuple[str, str]:
    """
    Intenta registrar DejaVuSans (soporta tildes y UTF-8).
    Si no está disponible en el sistema, cae a Helvetica.
    Retorna (nombre_normal, nombre_bold).
    """
    normal_path = None
    bold_path   = None

    candidates_normal = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/opt/homebrew/share/fonts/dejavu-fonts/DejaVuSans.ttf",
    ]
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/opt/homebrew/share/fonts/dejavu-fonts/DejaVuSans-Bold.ttf",
    ]

    for p in candidates_normal:
        if os.path.exists(p):
            normal_path = p
            break
    for p in candidates_bold:
        if os.path.exists(p):
            bold_path = p
            break

    if normal_path:
        try:
            pdfmetrics.registerFont(TTFont("DejaVu", normal_path))
            if bold_path:
                pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold_path))
            else:
                pdfmetrics.registerFont(TTFont("DejaVu-Bold", normal_path))
            return "DejaVu", "DejaVu-Bold"
        except Exception:
            pass

    # Fallback: Helvetica no soporta tildes pero no falla
    return "Helvetica", "Helvetica-Bold"


FONT_NORMAL, FONT_BOLD = _register_fonts()


# ═══════════════════════════════════════════════════════════════════════════════
# Función pública principal
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(stats: dict, output_path: str) -> None:
    """
    Genera el reporte PDF de la simulación LinProd.

    Parámetros
    ----------
    stats : dict
        Diccionario devuelto por Simulator.get_stats().
    output_path : str
        Ruta completa del archivo PDF a generar.
        Ejemplo: "/home/usuario/reporte_linprod.pdf"
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title="LinProd - Reporte de Simulacion",
        author="CE-5507 LinProd",
        subject="Simulacion de linea de produccion",
    )

    story: list = []
    styles = _build_styles()

    # ── Secciones del reporte ──────────────────────────────────────────────────
    _add_header(story, styles, stats)          # 1. Portada / encabezado
    _add_summary(story, styles, stats)         # 2. Resumen de tiempos (req. enunciado)
    _add_bottleneck(story, styles, stats)      # 3. Cuello de botella y esperas
    _add_task_table(story, styles, stats)      # 4. Detalle por tarea
    _add_product_table(story, styles, stats)   # 5. Detalle por producto
    _add_product_history(story, styles, stats) # 6. Historial de tareas por producto
    _add_footer_note(story, styles)            # 7. Nota de cierre

    doc.build(story)


# ═══════════════════════════════════════════════════════════════════════════════
# Estilos de párrafo
# ═══════════════════════════════════════════════════════════════════════════════

def _build_styles() -> dict:
    """Construye y retorna todos los estilos de párrafo usados en el reporte."""
    base = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "LinProdTitle",
        parent=base["Title"],
        fontName=FONT_BOLD,
        fontSize=22,
        textColor=COLOR_AZUL_OSCURO,
        spaceAfter=4,
        alignment=TA_CENTER,
    )

    subtitle_style = ParagraphStyle(
        "LinProdSubtitle",
        parent=base["Normal"],
        fontName=FONT_NORMAL,
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=2,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "LinProdHeading",
        parent=base["Heading2"],
        fontName=FONT_BOLD,
        fontSize=13,
        textColor=COLOR_AZUL_OSCURO,
        spaceBefore=14,
        spaceAfter=4,
        borderPad=0,
    )

    subheading_style = ParagraphStyle(
        "LinProdSubheading",
        parent=base["Heading3"],
        fontName=FONT_BOLD,
        fontSize=11,
        textColor=colors.HexColor("#333333"),
        spaceBefore=10,
        spaceAfter=2,
    )

    body_style = ParagraphStyle(
        "LinProdBody",
        parent=base["Normal"],
        fontName=FONT_NORMAL,
        fontSize=10,
        textColor=COLOR_TEXTO_OSCURO,
        spaceAfter=4,
        leading=14,
    )

    centered_style = ParagraphStyle(
        "LinProdCentered",
        parent=body_style,
        alignment=TA_CENTER,
    )

    note_style = ParagraphStyle(
        "LinProdNote",
        parent=body_style,
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER,
    )

    highlight_style = ParagraphStyle(
        "LinProdHighlight",
        parent=body_style,
        fontName=FONT_BOLD,
        fontSize=10,
        textColor=COLOR_AZUL_OSCURO,
        backColor=COLOR_FILA_PAR,
        borderPad=4,
    )

    return {
        "title":      title_style,
        "subtitle":   subtitle_style,
        "heading":    heading_style,
        "subheading": subheading_style,
        "body":       body_style,
        "centered":   centered_style,
        "note":       note_style,
        "highlight":  highlight_style,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers de tablas
# ═══════════════════════════════════════════════════════════════════════════════

def _base_table_style(header_color=None) -> list:
    """Retorna el estilo base compartido por todas las tablas del reporte."""
    hc = header_color or COLOR_AZUL_OSCURO
    return [
        # Encabezado
        ("BACKGROUND",    (0, 0), (-1, 0),  hc),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  FONT_BOLD),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
        # Cuerpo
        ("FONTNAME",      (0, 1), (-1, -1), FONT_NORMAL),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [COLOR_FILA_PAR, COLOR_FILA_IMPAR]),
        # Bordes
        ("GRID",          (0, 0), (-1, -1), 0.5, COLOR_BORDE_TABLA),
        # Padding
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        # Valign
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]


def _fmt(v) -> str:
    """Formatea None como guion, cualquier otro valor como str."""
    return "—" if v is None else str(v)


def _separator(story: list, space: float = 0.3) -> None:
    """Agrega un separador horizontal azul y espacio."""
    story.append(Spacer(1, space * cm))
    story.append(HRFlowable(
        width="100%",
        thickness=1,
        color=COLOR_AZUL_CLARO,
        spaceAfter=0.2 * cm,
    ))
    story.append(Spacer(1, space * cm))


# ═══════════════════════════════════════════════════════════════════════════════
# Sección 1 — Encabezado / portada
# ═══════════════════════════════════════════════════════════════════════════════

def _add_header(story: list, styles: dict, stats: dict) -> None:
    """Portada con logo textual, título y datos generales de la simulación."""

    # Título principal
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("LinProd", styles["title"]))
    story.append(Paragraph(
        "Reporte de Simulacion de Linea de Produccion",
        styles["subtitle"],
    ))
    story.append(Paragraph(
        "CE-5507 Modelacion Hardware/Software Orientado a Objetos  ·  I Semestre 2026",
        styles["subtitle"],
    ))
    story.append(Paragraph(
        "Instituto Tecnologico de Costa Rica  ·  Escuela de Ingenieria en Computadores",
        styles["subtitle"],
    ))

    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(
        width="100%", thickness=3,
        color=COLOR_AZUL_CLARO,
        spaceAfter=0.4 * cm,
    ))

    # Tabla de datos generales de la simulación
    now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    data_gen = [
        ["Fecha de generacion:", now],
        ["Ciclos totales ejecutados:", str(stats.get("total_cycles_run", 0))],
        ["Productos en la linea:", str(stats.get("products_total", 0))],
        ["Productos completados:", str(stats.get("products_completed", 0))],
    ]

    t = Table(data_gen, colWidths=[9 * cm, 7 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), FONT_NORMAL),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("FONTNAME",      (0, 0), (0, -1),  FONT_BOLD),
        ("TEXTCOLOR",     (0, 0), (0, -1),  COLOR_AZUL_OSCURO),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("ALIGN",         (1, 0), (1, -1),  "LEFT"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))


# ═══════════════════════════════════════════════════════════════════════════════
# Sección 2 — Resumen de tiempos (7 ítems obligatorios del enunciado)
# ═══════════════════════════════════════════════════════════════════════════════

def _add_summary(story: list, styles: dict, stats: dict) -> None:
    """
    Tabla con los 7 ítems de reportería obligatorios según el enunciado:
      1. Primer producto completado
      2. Último producto completado
      3. Tiempo promedio de paso
      4. Cuello de botella (proceso / tarea)  ← también en sección 3
      5. Tiempo promedio de espera global
      6. Proceso y tarea con mayor espera
      7. Tiempo total de procesamiento
    """
    story.append(Paragraph("Resumen General", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    bneck = (
        f"{_fmt(stats.get('bottleneck_process'))} / "
        f"{_fmt(stats.get('bottleneck_task'))}"
    )
    worst = (
        f"{_fmt(stats.get('worst_wait_process'))} / "
        f"{_fmt(stats.get('worst_wait_task'))}"
        + (f"  ({stats.get('worst_wait_value', 0.0):.2f} ciclos)"
           if stats.get("worst_wait_value", 0.0) > 0 else "")
    )

    data = [
        ["Metrica", "Valor"],
        ["1. Primer producto completado (ciclo)",
         _fmt(stats.get("first_completion_cycle"))],
        ["2. Ultimo producto completado (ciclo)",
         _fmt(stats.get("last_completion_cycle"))],
        ["3. Tiempo promedio de paso",
         f"{stats.get('avg_completion_time', 0.0):.2f} ciclos"],
        ["4. Cuello de botella (proceso / tarea)",
         bneck],
        ["5. Espera promedio global antes de iniciar tarea",
         f"{stats.get('avg_wait_to_start', 0.0):.2f} ciclos"],
        ["6. Proceso / tarea con mayor espera promedio",
         worst],
        ["7. Tiempo total de procesamiento (todos los productos)",
         f"{_fmt(stats.get('total_processing_time'))} ciclos"],
    ]

    t = Table(data, colWidths=[11 * cm, 5.5 * cm])
    style = _base_table_style()
    # Resaltar filas de "cuello de botella" en amarillo suave
    style += [
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#fff8e1")),
        ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#fff8e1")),
    ]
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))


# ═══════════════════════════════════════════════════════════════════════════════
# Sección 3 — Cuello de botella y análisis de esperas
# ═══════════════════════════════════════════════════════════════════════════════

def _add_bottleneck(story: list, styles: dict, stats: dict) -> None:
    """Análisis narrativo del cuello de botella y esperas críticas."""
    story.append(Paragraph("Analisis del Cuello de Botella", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    bneck_proc  = stats.get("bottleneck_process") or ""
    bneck_task  = stats.get("bottleneck_task") or ""
    worst_val   = stats.get("worst_wait_value", 0.0)
    worst_task  = stats.get("worst_wait_task") or ""
    worst_proc  = stats.get("worst_wait_process") or ""
    avg_wait    = stats.get("avg_wait_to_start", 0.0)
    total_prods = stats.get("products_total", 0)

    if bneck_task:
        texto_bneck = (
            f"El cuello de botella detectado es la tarea <b>{bneck_task}</b> "
            f"del proceso <b>{bneck_proc}</b>. "
            f"Esta tarea registro la mayor espera promedio en cola: "
            f"<b>{worst_val:.2f} ciclos</b> por producto. "
            "Esto indica que los productos tienden a acumularse antes de esta tarea, "
            "reduciendo el throughput global de la linea."
        )
    else:
        texto_bneck = (
            "No se detecto un cuello de botella significativo: "
            "ninguna tarea registro esperas promedio mayores a cero. "
            "La linea opero de forma fluida con los parametros dados."
        )

    story.append(Paragraph(texto_bneck, styles["body"]))
    story.append(Spacer(1, 0.3 * cm))

    # Sub-tabla: métricas de espera
    data_wait = [
        ["Indicador", "Valor"],
        ["Espera promedio global (todas las tareas)",
         f"{avg_wait:.2f} ciclos"],
        ["Tarea con mayor espera promedio",
         f"{worst_task}  ({worst_proc})"],
        ["Valor de esa espera maxima",
         f"{worst_val:.2f} ciclos / producto"],
        ["Productos que pasaron por la linea",
         str(total_prods)],
    ]

    t = Table(data_wait, colWidths=[10 * cm, 6.5 * cm])
    t.setStyle(TableStyle(_base_table_style(
        header_color=colors.HexColor("#7c3aed")  # morado para cuello
    )))
    story.append(KeepTogether(t))
    story.append(Spacer(1, 0.6 * cm))


# ═══════════════════════════════════════════════════════════════════════════════
# Sección 4 — Tabla de detalle por tarea
# ═══════════════════════════════════════════════════════════════════════════════

def _add_task_table(story: list, styles: dict, stats: dict) -> None:
    """Tabla con estadísticas de cada tarea (proceso, nombre, t, procesados, espera)."""
    story.append(Paragraph("Detalle por Tarea", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    encabezado = [["Proceso", "Tarea", "t (ciclos)", "Procesados", "Espera prom."]]
    filas = []

    bottleneck_key = (
        stats.get("bottleneck_process", ""),
        stats.get("bottleneck_task", ""),
    )

    for ts in stats.get("task_stats", []):
        filas.append([
            ts.get("process_name", ""),
            ts.get("task_name", ""),
            str(ts.get("process_time", "")),
            str(ts.get("products_processed", 0)),
            f"{ts.get('avg_wait_cycles', 0.0):.2f}",
        ])

    data = encabezado + filas
    col_w = [4 * cm, 4.5 * cm, 2.5 * cm, 2.5 * cm, 3 * cm]
    t = Table(data, colWidths=col_w)

    style = _base_table_style()
    # Alineación centrada para columnas numéricas
    style += [("ALIGN", (2, 1), (-1, -1), "CENTER")]

    # Resaltar cuello de botella en morado claro
    for i, ts in enumerate(stats.get("task_stats", []), start=1):
        if (ts.get("process_name"), ts.get("task_name")) == bottleneck_key:
            style += [
                ("BACKGROUND",  (0, i), (-1, i), colors.HexColor("#ede9fe")),
                ("FONTNAME",    (0, i), (-1, i), FONT_BOLD),
                ("TEXTCOLOR",   (0, i), (-1, i), colors.HexColor("#5b21b6")),
            ]

    t.setStyle(TableStyle(style))
    story.append(KeepTogether(t))

    # Leyenda del cuello de botella
    if bottleneck_key[1]:
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(
            f"* Fila resaltada = cuello de botella: "
            f"{bottleneck_key[0]} / {bottleneck_key[1]}",
            styles["note"],
        ))

    story.append(Spacer(1, 0.6 * cm))


# ═══════════════════════════════════════════════════════════════════════════════
# Sección 5 — Tabla de detalle por producto
# ═══════════════════════════════════════════════════════════════════════════════

def _add_product_table(story: list, styles: dict, stats: dict) -> None:
    """Tabla resumen de cada producto: entrada, salida, total, estado."""
    story.append(Paragraph("Detalle por Producto", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    encabezado = [["Producto", "Entrada", "Salida", "Total (ciclos)", "Estado"]]
    filas = []

    for p in stats.get("product_stats", []):
        estado = "Completado" if p.get("is_completed") else "En proceso"
        filas.append([
            f"P{p.get('product_id', '?')}",
            str(p.get("entry_time", "")),
            _fmt(p.get("exit_time")),
            _fmt(p.get("total_time")),
            estado,
        ])

    data = encabezado + filas
    col_w = [2.5 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm, 5 * cm]
    t = Table(data, colWidths=col_w)

    style = _base_table_style()
    style += [("ALIGN", (1, 1), (3, -1), "CENTER")]

    # Verde para completados, rojo para en proceso
    for i, p in enumerate(stats.get("product_stats", []), start=1):
        if p.get("is_completed"):
            style += [("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#065f46"))]
        else:
            style += [("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#991b1b"))]

    t.setStyle(TableStyle(style))
    story.append(KeepTogether(t))
    story.append(Spacer(1, 0.6 * cm))


# ═══════════════════════════════════════════════════════════════════════════════
# Sección 6 — Historial de tareas por producto (estadística adicional)
# ═══════════════════════════════════════════════════════════════════════════════

def _add_product_history(story: list, styles: dict, stats: dict) -> None:
    """
    Para cada producto, muestra el historial detallado de paso por cada tarea:
    proceso, tarea, ciclo inicio, ciclo fin, tiempo de espera en cola.
    Esto cumple el ítem 'Cualquier otra estadística que el grupo considere necesaria'.
    """
    story.append(PageBreak())
    story.append(Paragraph("Historial Detallado por Producto", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "A continuacion se muestra el recorrido de cada producto por cada tarea "
        "de la linea, incluyendo tiempos de inicio, fin y espera en cola.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.4 * cm))

    for p in stats.get("product_stats", []):
        pid = p.get("product_id", "?")
        estado = "Completado" if p.get("is_completed") else "En proceso"
        total  = _fmt(p.get("total_time"))

        story.append(Paragraph(
            f"Producto P{pid}  —  {estado}  |  Entrada: ciclo {p.get('entry_time', '?')}  "
            f"|  Salida: {_fmt(p.get('exit_time'))}  |  Total: {total} ciclos",
            styles["subheading"],
        ))

        history = p.get("task_history", [])
        if history:
            enc = [["Proceso", "Tarea", "Inicio", "Fin", "Espera en cola"]]
            filas = []
            for h in history:
                filas.append([
                    h.get("process_name", ""),
                    h.get("task_name", ""),
                    str(h.get("start_cycle", "")),
                    _fmt(h.get("end_cycle")),
                    f"{h.get('wait_cycles', 0)} ciclos",
                ])
            data = enc + filas
            col_w = [4 * cm, 4 * cm, 2 * cm, 2 * cm, 3.5 * cm]
            t = Table(data, colWidths=col_w)
            t.setStyle(TableStyle(_base_table_style(
                header_color=colors.HexColor("#1e3a5f")
            )))
            story.append(t)
        else:
            story.append(Paragraph("(sin historial de tareas registrado)", styles["body"]))

        story.append(Spacer(1, 0.4 * cm))


# ═══════════════════════════════════════════════════════════════════════════════
# Sección 7 — Nota de pie de reporte
# ═══════════════════════════════════════════════════════════════════════════════

def _add_footer_note(story: list, styles: dict) -> None:
    """Línea de cierre del reporte."""
    _separator(story, 0.4)
    story.append(Paragraph(
        f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}  "
        "·  LinProd  ·  CE-5507 OO  ·  TEC  I Semestre 2026",
        styles["note"],
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# Ejecución autónoma (sin GUI) — para pruebas
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Agrega la raíz del repositorio al path para que funcione sin instalar
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)

    from linprod.model import Process, ProductionLine, Task
    from linprod.simulator import Simulator

    print("Construyendo linea de demo (5 procesos x 2 tareas, 5 productos)...")

    line = ProductionLine()

    demo_data = [
        ("Corte",    True,  False, [("Corte laser", 2), ("Pulido",      2)]),
        ("Ensamble", False, False, [("Armado",       3), ("Soldadura",   4)]),
        ("Pintura",  False, False, [("Imprimacion",  2), ("Pintura",     3)]),
        ("Revision", False, False, [("Inspeccion",   2), ("Correccion",  1)]),
        ("Empaque",  False, True,  [("Empacar",      2), ("Etiquetado",  1)]),
    ]

    for proc_name, is_initial, is_final, tasks in demo_data:
        proc = Process(name=proc_name, is_initial=is_initial, is_final=is_final)
        for task_name, t in tasks:
            proc.add_task(Task(name=task_name, process_time=t))
        line.add_process(proc)

    sim = Simulator(line, n_products=5)
    sim.start()
    sim.run(500)  # más que suficiente para 5 productos

    stats = sim.get_stats()

    output = "reporte_prueba_linprod.pdf"
    generate_report(stats, output)
    print(f"PDF generado: {output}")
    print(f"  Ciclos:      {stats['total_cycles_run']}")
    print(f"  Completados: {stats['products_completed']} / {stats['products_total']}")
    print(f"  Cuello:      {stats['bottleneck_process']} / {stats['bottleneck_task']}")