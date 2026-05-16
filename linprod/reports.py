"""
reports.py — Módulo 4: Generación de reportes PDF
Proyecto LinProd | CE-5507 Modelación Hardware/Software Orientado a Objetos
Instituto Tecnológico de Costa Rica | I Semestre 2026

Genera un reporte PDF completo de la simulación usando reportlab.
Única fuente de datos: Simulator.get_stats().
No importa nada de app.py ni de tkinter.
"""

from __future__ import annotations

import os
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ─── Registro de fuente con soporte UTF-8 (tildes, ñ) ────────────────────────

_DEJAVU_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]
_DEJAVU_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]

_FONT_NORMAL = "Helvetica"
_FONT_BOLD   = "Helvetica-Bold"

def _register_fonts() -> None:
    global _FONT_NORMAL, _FONT_BOLD
    for path in _DEJAVU_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", path))
                _FONT_NORMAL = "DejaVuSans"
            except Exception:
                pass
            break
    for path in _DEJAVU_BOLD_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", path))
                _FONT_BOLD = "DejaVuSans-Bold"
            except Exception:
                pass
            break

_register_fonts()

# ─── Paleta de colores ────────────────────────────────────────────────────────

_AZUL_TEC    = colors.HexColor("#004680")
_AZUL_CLARO  = colors.HexColor("#4f8cff")
_VERDE       = colors.HexColor("#34d399")
_ROJO        = colors.HexColor("#f87171")
_MORADO      = colors.HexColor("#a78bfa")
_AMARILLO    = colors.HexColor("#fbbf24")
_FILA_PAR    = colors.HexColor("#eef3fb")
_FILA_IMPAR  = colors.white
_BORDE       = colors.HexColor("#cccccc")


# ═══════════════════════════════════════════════════════════════════════════════
# Función pública
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
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title="LinProd - Reporte de Simulacion",
        author="LinProd CE-5507 TEC",
    )

    styles = _build_styles()
    story: list = []

    _add_header(story, styles, stats)
    _add_summary(story, styles, stats)
    _add_bottleneck(story, styles, stats)
    _add_process_stats(story, styles, stats)
    _add_task_table(story, styles, stats)
    story.append(PageBreak())
    _add_product_table(story, styles, stats)

    doc.build(story)


# ═══════════════════════════════════════════════════════════════════════════════
# Estilos
# ═══════════════════════════════════════════════════════════════════════════════

def _build_styles() -> dict:
    base = getSampleStyleSheet()
    fn, fb = _FONT_NORMAL, _FONT_BOLD

    title_style = ParagraphStyle(
        "LinProdTitle",
        fontName=fb,
        fontSize=22,
        textColor=_AZUL_TEC,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "LinProdSubtitle",
        fontName=fn,
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    heading_style = ParagraphStyle(
        "LinProdHeading",
        fontName=fb,
        fontSize=13,
        textColor=_AZUL_TEC,
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "LinProdBody",
        fontName=fn,
        fontSize=10,
        leading=14,
        spaceAfter=4,
    )
    note_style = ParagraphStyle(
        "LinProdNote",
        fontName=fn,
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=2,
    )

    return {
        "title":    title_style,
        "subtitle": subtitle_style,
        "heading":  heading_style,
        "body":     body_style,
        "note":     note_style,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Secciones del reporte
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt(v) -> str:
    """Convierte None a '—' y cualquier otro valor a str."""
    return "—" if v is None else str(v)


def _add_header(story: list, styles: dict, stats: dict) -> None:
    story.append(Paragraph("LinProd", styles["title"]))
    story.append(Paragraph(
        "Reporte de Simulacion de Linea de Produccion", styles["subtitle"]
    ))
    story.append(Paragraph(
        "CE-5507 — Modelacion Hardware/Software OO | Instituto Tecnologico de Costa Rica",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=_AZUL_TEC))
    story.append(Spacer(1, 0.4 * cm))

    resumen = [
        ["Ciclos totales ejecutados:", _fmt(stats["total_cycles_run"])],
        ["Productos en la linea:",     _fmt(stats["products_total"])],
        ["Productos completados:",     _fmt(stats["products_completed"])],
    ]
    t = Table(resumen, colWidths=[10 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), _FONT_NORMAL),
        ("FONTSIZE",      (0, 0), (-1, -1), 11),
        ("FONTNAME",      (0, 0), (0, -1),  _FONT_BOLD),
        ("TEXTCOLOR",     (0, 0), (0, -1),  _AZUL_TEC),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))


def _add_summary(story: list, styles: dict, stats: dict) -> None:
    story.append(Paragraph("Resumen de Tiempos", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    # ① primer producto   ② último producto   ③ promedio   ④ tiempo total
    # ⑤ espera promedio global — todos los ítems obligatorios del enunciado
    avg = stats.get("avg_completion_time", 0.0)
    avg_wait = stats.get("avg_wait_to_start", 0.0)
    total_proc = stats.get("total_processing_time", 0)

    data = [
        ["Metrica", "Valor"],
        ["① Primer producto completado (ciclo)",
         _fmt(stats.get("first_completion_cycle"))],
        ["② Ultimo producto completado (ciclo)",
         _fmt(stats.get("last_completion_cycle"))],
        ["③ Tiempo promedio de paso por la linea",
         f"{avg:.2f} ciclos"],
        ["④ Tiempo total acumulado de procesamiento",
         f"{total_proc} ciclos"],
        ["⑤ Espera promedio global antes de iniciar tarea",
         f"{avg_wait:.2f} ciclos"],
    ]

    t = _make_table(data, col_widths=[11 * cm, 5 * cm], header_bg=_AZUL_TEC)
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))


def _add_bottleneck(story: list, styles: dict, stats: dict) -> None:
    story.append(Paragraph("Cuello de Botella y Congestionamiento", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    bneck_proc = stats.get("bottleneck_process") or "—"
    bneck_task = stats.get("bottleneck_task") or "—"
    worst_proc = stats.get("worst_wait_process") or "—"
    worst_task = stats.get("worst_wait_task") or "—"
    worst_val  = stats.get("worst_wait_value", 0.0)

    # ⑥ proceso/tarea con mayor congestionamiento
    # ⑦ proceso/tarea con mayor espera promedio
    data = [
        ["Indicador", "Proceso", "Tarea", "Valor"],
        ["⑥ Cuello de botella (mayor cola)", bneck_proc, bneck_task, "—"],
        ["⑦ Mayor espera promedio", worst_proc, worst_task,
         f"{worst_val:.2f} ciclos"],
    ]
    t = _make_table(data, col_widths=[6 * cm, 3.5 * cm, 3.5 * cm, 3 * cm],
                    header_bg=_MORADO)
    story.append(t)

    if bneck_task != "—":
        story.append(Spacer(1, 0.3 * cm))
        texto = (
            f"La tarea <b>{bneck_task}</b> del proceso <b>{bneck_proc}</b> "
            f"genero el mayor nivel de congestionamiento, con una espera promedio "
            f"de <b>{worst_val:.2f} ciclos</b> por producto en cola."
        )
        story.append(Paragraph(texto, styles["body"]))
    story.append(Spacer(1, 0.6 * cm))


def _add_process_stats(story: list, styles: dict, stats: dict) -> None:
    """Estadísticas por proceso (inicio/fin/duración) — ítem extra."""
    task_stats = stats.get("task_stats", [])
    if not task_stats:
        return

    story.append(Paragraph("Estadisticas por Proceso", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    # Agrupar task_stats por proceso
    processes: dict[str, list[dict]] = {}
    for ts in task_stats:
        proc = ts["process_name"]
        processes.setdefault(proc, []).append(ts)

    product_stats = stats.get("product_stats", [])

    data = [["Proceso", "Productos proc.", "Espera total prom.", "t minimo tarea", "t maximo tarea"]]
    for proc_name, tasks in processes.items():
        prods = sum(t["products_processed"] for t in tasks) // max(len(tasks), 1)
        avg_w = sum(t["avg_wait_cycles"] for t in tasks) / max(len(tasks), 1)
        t_min = min(t["process_time"] for t in tasks)
        t_max = max(t["process_time"] for t in tasks)
        data.append([
            proc_name,
            str(prods),
            f"{avg_w:.2f} ciclos",
            str(t_min),
            str(t_max),
        ])

    t = _make_table(data, col_widths=[4.5*cm, 3*cm, 3.5*cm, 3*cm, 2*cm],
                    header_bg=_AZUL_CLARO)
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))


def _add_task_table(story: list, styles: dict, stats: dict) -> None:
    task_stats = stats.get("task_stats", [])
    if not task_stats:
        return

    story.append(Paragraph("Detalle por Tarea", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    data = [["Proceso", "Tarea", "t (ciclos)", "Procesados", "Espera prom."]]
    for ts in task_stats:
        data.append([
            ts["process_name"],
            ts["task_name"],
            str(ts["process_time"]),
            str(ts["products_processed"]),
            f"{ts['avg_wait_cycles']:.2f}",
        ])

    t = _make_table(data, col_widths=[4*cm, 4.5*cm, 2.5*cm, 2.5*cm, 2.5*cm],
                    header_bg=_AZUL_TEC)
    story.append(KeepTogether([t]))
    story.append(Spacer(1, 0.6 * cm))


def _add_product_table(story: list, styles: dict, stats: dict) -> None:
    product_stats = stats.get("product_stats", [])
    if not product_stats:
        return

    story.append(Paragraph("Detalle por Producto", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    data = [["Producto", "Entrada", "Salida", "Total (ciclos)", "Estado"]]
    for p in product_stats:
        data.append([
            f"P{p['product_id']}",
            _fmt(p["entry_time"]),
            _fmt(p["exit_time"]),
            _fmt(p["total_time"]),
            "Completado" if p["is_completed"] else "En proceso",
        ])

    t = _make_table(data, col_widths=[2.5*cm, 2.5*cm, 2.5*cm, 3.5*cm, 5*cm],
                    header_bg=_AZUL_TEC)
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))

    # Historial por producto (tarea a tarea)
    story.append(Paragraph("Historial de Paso por Tarea (por producto)", styles["heading"]))
    story.append(Spacer(1, 0.2 * cm))

    for p in product_stats:
        if not p.get("task_history"):
            continue
        header_row = [
            f"P{p['product_id']} — entrada: {p['entry_time']}  salida: {_fmt(p['exit_time'])}  "
            f"total: {_fmt(p['total_time'])} ciclos"
        ]
        hist_data = [["Proceso", "Tarea", "Inicio", "Fin", "Espera en cola"]]
        for entry in p["task_history"]:
            hist_data.append([
                entry.get("process_name", "—"),
                entry.get("task_name", "—"),
                _fmt(entry.get("start_cycle")),
                _fmt(entry.get("end_cycle")),
                f"{entry.get('wait_cycles', 0)} ciclos",
            ])
        ht = _make_table(hist_data, col_widths=[3.5*cm, 4*cm, 2*cm, 2*cm, 4.5*cm],
                         header_bg=colors.HexColor("#2d3548"), font_size=8)
        cap = Paragraph(header_row[0], styles["note"])
        story.append(KeepTogether([cap, Spacer(1, 0.15*cm), ht, Spacer(1, 0.3*cm)]))


# ═══════════════════════════════════════════════════════════════════════════════
# Helper para construir tablas con estilo uniforme
# ═══════════════════════════════════════════════════════════════════════════════

def _make_table(
    data: list[list],
    col_widths: list,
    header_bg: colors.Color = _AZUL_TEC,
    font_size: int = 9,
) -> Table:
    fn, fb = _FONT_NORMAL, _FONT_BOLD
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        # Encabezado
        ("BACKGROUND",    (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), fb),
        ("FONTSIZE",      (0, 0), (-1, 0), font_size),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        # Cuerpo
        ("FONTNAME",      (0, 1), (-1, -1), fn),
        ("FONTSIZE",      (0, 1), (-1, -1), font_size),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_FILA_PAR, _FILA_IMPAR]),
        ("GRID",          (0, 0), (-1, -1), 0.5, _BORDE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ═══════════════════════════════════════════════════════════════════════════════
# Prueba autónoma (python3 -m linprod.reports)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from linprod.model import Process, ProductionLine, Task
    from linprod.simulator import Simulator

    line = ProductionLine()

    p1 = Process("Corte",    is_initial=True)
    p1.add_task(Task("Corte laser", 2))
    p1.add_task(Task("Pulido",      2))

    p2 = Process("Ensamble")
    p2.add_task(Task("Armado",    3))
    p2.add_task(Task("Soldadura", 4))

    p3 = Process("Pintura")
    p3.add_task(Task("Imprimacion", 2))
    p3.add_task(Task("Pintura",     3))

    p4 = Process("Empaque", is_final=True)
    p4.add_task(Task("Empacar",    2))
    p4.add_task(Task("Etiquetado", 1))

    line.add_process(p1)
    line.add_process(p2)
    line.add_process(p3)
    line.add_process(p4)

    sim = Simulator(line, n_products=5)
    sim.start()
    sim.run(500)

    stats = sim.get_stats()
    output = "reporte_linprod_prueba.pdf"
    generate_report(stats, output)
    print(f"PDF generado: {output}")
    print(f"Ciclos totales: {stats['total_cycles_run']}")
    print(f"Productos completados: {stats['products_completed']}/{stats['products_total']}")
    print(f"Cuello de botella: {stats['bottleneck_process']} / {stats['bottleneck_task']}")
