"""
app.py — Módulo 3: Interfaz Gráfica de Usuario (GUI)
Proyecto LinProd | CE-5507 Modelación Hardware/Software Orientado a Objetos
Instituto Tecnológico de Costa Rica | I Semestre 2026

GUI moderna con Tkinter:
  - Tema oscuro tipo dashboard
  - Tarjetas con sombras visuales y bordes redondeados (simulados con padding)
  - Tipografía moderna con jerarquía clara
  - Animaciones de estado vía colores
  - Layout responsivo en dos columnas

Depende de: linprod.model (Módulo 1) y linprod.simulator (Módulo 2).
NO modifica esos módulos.

Ejecución desde la raíz del repositorio:
    python3 -m linprod.gui.app
"""

from __future__ import annotations

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from linprod.model import Process, ProductionLine, Task
from linprod.simulator import Simulator


# ═══════════════════════════════════════════════════════════════════════════════
# Paleta de colores — Tema oscuro moderno (inspirado en dashboards modernos)
# ═══════════════════════════════════════════════════════════════════════════════

# Fondos
BG_BASE = "#0f1419"          # fondo principal muy oscuro
BG_PANEL = "#1a1f2e"         # paneles laterales
BG_CARD = "#242b3d"          # tarjetas elevadas
BG_CARD_HOVER = "#2d3548"    # cuando hover/activo
BG_INPUT = "#161b26"         # campos de texto

# Texto
TEXT_PRIMARY = "#e8eaed"     # texto principal
TEXT_SECONDARY = "#9aa0a6"   # texto secundario / labels
TEXT_MUTED = "#8a9099"       # texto tenue (contraste mínimo 3:1 sobre BG_CARD)
TEXT_ACCENT = "#8ab4f8"      # links / destacados

# Acentos
ACCENT_PRIMARY = "#4f8cff"   # azul principal (botón iniciar)
ACCENT_HOVER = "#3a78f0"     # hover del azul
ACCENT_SUCCESS = "#34d399"   # verde éxito
ACCENT_WARNING = "#fbbf24"   # amarillo advertencia
ACCENT_DANGER = "#f87171"    # rojo peligro
ACCENT_PURPLE = "#a78bfa"    # morado (cuello de botella)

# Estados de tarea
TASK_FREE_BG = "#1e3a32"     # verde oscuro: libre
TASK_FREE_BORDER = "#34d399"
TASK_FREE_TEXT = "#6ee7b7"

TASK_BUSY_BG = "#3d3520"     # ámbar oscuro: ocupada
TASK_BUSY_BORDER = "#fbbf24"
TASK_BUSY_TEXT = "#fde68a"

TASK_QUEUED_BG = "#3d2020"   # rojo oscuro: ocupada + cola
TASK_QUEUED_BORDER = "#f87171"
TASK_QUEUED_TEXT = "#fca5a5"

TASK_BOTTLENECK_BG = "#2e2640"  # morado oscuro: cuello de botella
TASK_BOTTLENECK_BORDER = "#a78bfa"
TASK_BOTTLENECK_TEXT = "#c4b5fd"

# Estados de proceso
PROC_INITIAL = "#34d399"     # verde
PROC_FINAL = "#f87171"       # rojo
PROC_MIDDLE = "#4f8cff"      # azul

# Tipografía
FONT_FAMILY = "DejaVu Sans"
FONT_DISPLAY = (FONT_FAMILY, 28, "bold")
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 11, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_TINY = (FONT_FAMILY, 9)
FONT_MONO = ("DejaVu Sans Mono", 10)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers de widgets modernos
# ═══════════════════════════════════════════════════════════════════════════════

class ModernButton(tk.Label):
    """
    Botón moderno hecho con Label (permite más control de estética que Button).
    Soporta hover, estados disabled, y diferentes variantes (primary/secondary/danger).
    """

    VARIANTS = {
        "primary":   (ACCENT_PRIMARY, ACCENT_HOVER, "#ffffff"),
        "secondary": (BG_CARD, BG_CARD_HOVER, TEXT_PRIMARY),
        "success":   (ACCENT_SUCCESS, "#10b981", "#0f1419"),
        "danger":    (ACCENT_DANGER, "#ef4444", "#ffffff"),
        "warning":   (ACCENT_WARNING, "#f59e0b", "#0f1419"),
    }

    def __init__(self, parent, text, command, variant="secondary", width=None, **kwargs):
        bg, hover, fg = self.VARIANTS.get(variant, self.VARIANTS["secondary"])
        self._bg = bg
        self._hover = hover
        self._fg = fg
        self._command = command
        self._enabled = True

        super().__init__(
            parent, text=text, bg=bg, fg=fg,
            font=FONT_BODY_BOLD, padx=14, pady=8,
            cursor="hand2", **kwargs
        )
        if width:
            self.config(width=width)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        if self._enabled:
            self.config(bg=self._hover)

    def _on_leave(self, _):
        if self._enabled:
            self.config(bg=self._bg)

    def _on_click(self, _):
        if self._enabled and self._command:
            self._command()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            self.config(bg=self._bg, fg=self._fg, cursor="hand2")
        else:
            self.config(bg=BG_CARD, fg=TEXT_MUTED, cursor="arrow")


class ModernEntry(tk.Entry):
    """Entry estilizado para el tema oscuro."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=BG_INPUT, fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat", borderwidth=0,
            font=FONT_BODY,
            highlightthickness=1,
            highlightbackground="#2d3548",
            highlightcolor=ACCENT_PRIMARY,
            **kwargs,
        )
        # padding interno simulado con un wrapper
        self.config(insertwidth=2)


class Card(tk.Frame):
    """
    Tarjeta con borde simulado.
    Tkinter no tiene esquinas redondeadas nativas, pero un buen padding
    y un borde fino del color del card consigue una sensación similar.
    """

    def __init__(self, parent, title=None, padding=14, **kwargs):
        super().__init__(parent, bg=BG_CARD, **kwargs)
        if title:
            header = tk.Frame(self, bg=BG_CARD)
            header.pack(side="top", fill="x", padx=padding, pady=(padding, 6))
            tk.Label(header, text=title, bg=BG_CARD, fg=TEXT_PRIMARY,
                     font=FONT_SUBTITLE, anchor="w").pack(side="left")
            # Línea sutil debajo
            tk.Frame(self, bg="#2d3548", height=1).pack(fill="x", padx=padding)

        self.body = tk.Frame(self, bg=BG_CARD)
        self.body.pack(side="top", fill="both", expand=True, padx=padding,
                       pady=(8 if title else padding, padding))


# ═══════════════════════════════════════════════════════════════════════════════
# Aplicación principal
# ═══════════════════════════════════════════════════════════════════════════════

class LinProdApp(tk.Tk):
    """Ventana principal de LinProd con estética moderna."""

    def __init__(self):
        super().__init__()
        self.title("LinProd · Simulador de Producción")
        self.geometry("1500x900")
        self.minsize(1280, 760)
        self.configure(bg=BG_BASE)

        # ── Estado ─────────────────────────────────────────────────────────────
        self._line: Optional[ProductionLine] = None
        self._sim: Optional[Simulator] = None
        self._timer_id: Optional[str] = None
        self._cycle_ms: int = 500
        self._task_widgets: dict[str, dict] = {}
        self._pause_window: Optional[tk.Toplevel] = None
        # Proceso en construcción (pendiente de confirmación)
        self._pending_process: Optional[Process] = None
        # Proceso confirmado que está siendo editado (agregar más tareas)
        self._edit_target: Optional[Process] = None
        # Mapa tree-item-id → Process para saber qué proceso seleccionó el usuario
        self._tree_item_to_proc: dict[str, Process] = {}
        # Modo de ejecución: "auto" corre el timer, "step" espera clic manual
        self._mode_var: tk.StringVar = tk.StringVar(value="auto")

        # ── Estilos ttk (solo para los pocos widgets ttk que usamos) ───────────
        self._setup_ttk_styles()

        # ── Construcción de la UI ──────────────────────────────────────────────
        self._build_ui()
        self._refresh_line_tree()
        self._update_button_states()

    def _setup_ttk_styles(self) -> None:
        """Configura los pocos widgets ttk (progressbar, treeview, scale)."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Progressbar
        style.configure("Modern.Horizontal.TProgressbar",
                        background=ACCENT_PRIMARY,
                        troughcolor=BG_INPUT,
                        bordercolor=BG_CARD,
                        lightcolor=ACCENT_PRIMARY,
                        darkcolor=ACCENT_PRIMARY,
                        thickness=8)

        # Progressbar dentro de tarjeta (verde para tareas activas)
        style.configure("Task.Horizontal.TProgressbar",
                        background=ACCENT_SUCCESS,
                        troughcolor="#0f1419",
                        bordercolor=BG_CARD,
                        lightcolor=ACCENT_SUCCESS,
                        darkcolor=ACCENT_SUCCESS,
                        thickness=4)

        # Treeview
        style.configure("Modern.Treeview",
                        background=BG_INPUT,
                        foreground=TEXT_PRIMARY,
                        fieldbackground=BG_INPUT,
                        bordercolor=BG_CARD,
                        font=FONT_BODY,
                        rowheight=24)
        style.configure("Modern.Treeview.Heading",
                        background=BG_CARD,
                        foreground=TEXT_SECONDARY,
                        font=FONT_SMALL,
                        relief="flat")
        style.map("Modern.Treeview.Heading",
                  background=[("active", BG_CARD_HOVER)])
        style.map("Modern.Treeview",
                  background=[("selected", ACCENT_PRIMARY)],
                  foreground=[("selected", "#ffffff")])

        # Scale (slider)
        style.configure("Modern.Horizontal.TScale",
                        background=BG_PANEL,
                        troughcolor=BG_INPUT,
                        bordercolor=BG_CARD)

        # Scrollbars
        style.configure("Modern.Vertical.TScrollbar",
                        background=BG_CARD,
                        troughcolor=BG_BASE,
                        bordercolor=BG_BASE,
                        arrowcolor=TEXT_SECONDARY,
                        relief="flat")
        style.configure("Modern.Horizontal.TScrollbar",
                        background=BG_CARD,
                        troughcolor=BG_BASE,
                        bordercolor=BG_BASE,
                        arrowcolor=TEXT_SECONDARY,
                        relief="flat")

        # Checkbutton
        style.configure("Modern.TCheckbutton",
                        background=BG_CARD,
                        foreground=TEXT_PRIMARY,
                        focuscolor=BG_CARD,
                        font=FONT_BODY)
        style.map("Modern.TCheckbutton",
                  background=[("active", BG_CARD)])

    # ══════════════════════════════════════════════════════════════════════════
    # Construcción de la UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        # ── Barra superior ─────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=BG_BASE, height=60)
        topbar.pack(side="top", fill="x", padx=20, pady=(16, 8))
        topbar.pack_propagate(False)

        # Logo / título
        tk.Label(topbar, text="◆", bg=BG_BASE, fg=ACCENT_PRIMARY,
                 font=(FONT_FAMILY, 22)).pack(side="left", padx=(0, 8))
        title_box = tk.Frame(topbar, bg=BG_BASE)
        title_box.pack(side="left")
        tk.Label(title_box, text="LinProd", bg=BG_BASE, fg=TEXT_PRIMARY,
                 font=(FONT_FAMILY, 18, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Simulador de Producción en Serie",
                 bg=BG_BASE, fg=TEXT_SECONDARY, font=FONT_SMALL).pack(anchor="w")

        # Status pill (a la derecha)
        self._status_pill = tk.Label(
            topbar, text="● Listo", bg=BG_BASE, fg=ACCENT_SUCCESS,
            font=FONT_BODY_BOLD, padx=14, pady=6
        )
        self._status_pill.pack(side="right")

        # ── Contenedor principal ───────────────────────────────────────────────
        main = tk.Frame(self, bg=BG_BASE)
        main.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 12))

        # Columna izquierda (configuración)
        left = tk.Frame(main, bg=BG_BASE, width=350)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        self._build_config_card(left)
        self._build_line_tree_card(left)

        # Columna derecha (visualización + controles)
        right = tk.Frame(main, bg=BG_BASE)
        right.pack(side="left", fill="both", expand=True)

        self._build_metrics_row(right)
        self._build_sim_canvas(right)
        self._build_controls_card(right)

    def _build_config_card(self, parent: tk.Widget) -> None:
        """Tarjeta de configuración (procesos, tareas, n_products)."""
        card = Card(parent, title="Configurar línea")
        card.pack(side="top", fill="x", pady=(0, 12))

        # ── Sección: Proceso ──────────────────────────────────────────────────
        self._label_section(card.body, "1 · NUEVO PROCESO")

        tk.Label(card.body, text="Nombre", bg=BG_CARD, fg=TEXT_SECONDARY,
                 font=FONT_SMALL).pack(anchor="w", pady=(4, 2))
        self._entry_proc_name = ModernEntry(card.body)
        self._entry_proc_name.pack(fill="x", ipady=6, pady=(0, 6))

        check_row = tk.Frame(card.body, bg=BG_CARD)
        check_row.pack(fill="x", pady=(2, 8))
        self._var_is_initial = tk.BooleanVar()
        self._var_is_final = tk.BooleanVar()
        ttk.Checkbutton(check_row, text="Inicial", style="Modern.TCheckbutton",
                        variable=self._var_is_initial).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(check_row, text="Final", style="Modern.TCheckbutton",
                        variable=self._var_is_final).pack(side="left")

        ModernButton(card.body, text="+  Crear proceso", variant="secondary",
                     command=self._add_process).pack(fill="x", pady=(0, 4))

        # Separador
        tk.Frame(card.body, bg="#2d3548", height=1).pack(fill="x", pady=8)

        # ── Sección: Tarea ────────────────────────────────────────────────────
        # Label dinámica — se actualiza con el proceso activo
        self._lbl_task_section = tk.Label(
            card.body,
            text="2 · TAREAS  (cree primero un proceso)",
            bg=BG_CARD, fg=TEXT_MUTED,
            font=(FONT_FAMILY, 9, "bold"), anchor="w"
        )
        self._lbl_task_section.pack(anchor="w")

        tk.Label(card.body, text="Nombre", bg=BG_CARD, fg=TEXT_SECONDARY,
                 font=FONT_SMALL).pack(anchor="w", pady=(4, 2))
        self._entry_task_name = ModernEntry(card.body)
        self._entry_task_name.pack(fill="x", ipady=6, pady=(0, 6))

        tk.Label(card.body, text="Tiempo de procesamiento (ciclos)",
                 bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL
                 ).pack(anchor="w", pady=(0, 2))
        self._entry_task_time = ModernEntry(card.body)
        self._entry_task_time.pack(fill="x", ipady=6, pady=(0, 8))

        ModernButton(card.body, text="+  Agregar tarea", variant="secondary",
                     command=self._add_task).pack(fill="x", pady=(0, 6))

        # Botón confirmar proceso (verde, prominente)
        self._btn_confirm_proc = ModernButton(
            card.body,
            text="✓  Confirmar proceso (requiere ≥1 tarea)",
            variant="success",
            command=self._confirm_process,
        )
        self._btn_confirm_proc.pack(fill="x", pady=(0, 4))
        self._btn_confirm_proc.set_enabled(False)

        # Separador
        tk.Frame(card.body, bg="#2d3548", height=1).pack(fill="x", pady=8)

        # ── Sección: Cantidad de productos ────────────────────────────────────
        self._label_section(card.body, "3 · PRODUCTOS A SIMULAR")
        self._entry_n_products = ModernEntry(card.body)
        self._entry_n_products.insert(0, "5")
        self._entry_n_products.pack(fill="x", ipady=6, pady=(4, 10))

        ModernButton(card.body, text="★  Cargar demo", variant="warning",
                     command=self._load_demo).pack(fill="x", pady=(0, 6))

        ModernButton(card.body, text="×  Limpiar línea", variant="danger",
                     command=self._clear_line).pack(fill="x")

    def _label_section(self, parent: tk.Widget, text: str) -> None:
        """Etiqueta tipo 'header' pequeña en mayúsculas."""
        tk.Label(parent, text=text, bg=BG_CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 9, "bold")).pack(anchor="w")

    def _build_line_tree_card(self, parent: tk.Widget) -> None:
        """Tarjeta con el árbol de la línea construida."""
        card = Card(parent, title="Estructura de la línea")
        card.pack(side="top", fill="both", expand=True)

        tree_wrap = tk.Frame(card.body, bg=BG_INPUT)
        tree_wrap.pack(fill="both", expand=True)

        cols = ("detalle",)
        self._tree = ttk.Treeview(tree_wrap, columns=cols, show="tree headings",
                                   style="Modern.Treeview", height=12)
        self._tree.heading("#0", text="PROCESO / TAREA", anchor="w")
        self._tree.heading("detalle", text="DETALLE", anchor="w")
        self._tree.column("#0", width=180, stretch=True)
        self._tree.column("detalle", width=110, stretch=False)

        vs = ttk.Scrollbar(tree_wrap, orient="vertical", command=self._tree.yview,
                           style="Modern.Vertical.TScrollbar")
        self._tree.configure(yscrollcommand=vs.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

        # Botonera de edición bajo el árbol
        edit_bar = tk.Frame(card.body, bg=BG_CARD)
        edit_bar.pack(side="top", fill="x", pady=(8, 0))

        self._btn_edit_proc = ModernButton(
            edit_bar, text="✎  Editar proceso seleccionado",
            variant="secondary", command=self._on_edit_selected,
        )
        self._btn_edit_proc.pack(side="left", padx=(0, 6), fill="x", expand=True)

        self._btn_cancel_edit = ModernButton(
            edit_bar, text="✕  Cancelar edición",
            variant="warning", command=self._cancel_edit,
        )
        self._btn_cancel_edit.pack(side="left", fill="x", expand=True)
        self._btn_cancel_edit.set_enabled(False)

    def _build_metrics_row(self, parent: tk.Widget) -> None:
        """Fila superior del panel derecho: 4 tarjetas de métricas."""
        row = tk.Frame(parent, bg=BG_BASE)
        row.pack(side="top", fill="x", pady=(0, 12))

        self._metric_cycle = self._build_metric_card(row, "CICLO", "0", ACCENT_PRIMARY)
        self._metric_cycle.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self._metric_done = self._build_metric_card(row, "COMPLETADOS", "0 / 0",
                                                     ACCENT_SUCCESS)
        self._metric_done.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self._metric_progress = self._build_metric_card(row, "EN PROCESO", "0",
                                                         ACCENT_WARNING)
        self._metric_progress.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Tarjeta con barra de progreso
        prog_card = tk.Frame(row, bg=BG_CARD)
        prog_card.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(prog_card, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=14, pady=14)
        tk.Label(inner, text="PROGRESO", bg=BG_CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        self._progress_global = ttk.Progressbar(inner,
                                                 style="Modern.Horizontal.TProgressbar",
                                                 mode="determinate")
        self._progress_global.pack(fill="x", pady=(12, 4))
        self._lbl_progress_pct = tk.Label(inner, text="0%", bg=BG_CARD,
                                           fg=TEXT_SECONDARY, font=FONT_BODY)
        self._lbl_progress_pct.pack(anchor="w")

    def _build_metric_card(self, parent: tk.Widget, label: str,
                            value: str, color: str) -> tk.Frame:
        """Tarjeta de métrica con label arriba y valor grande abajo."""
        card = tk.Frame(parent, bg=BG_CARD)
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=14, pady=14)
        tk.Label(inner, text=label, bg=BG_CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        value_lbl = tk.Label(inner, text=value, bg=BG_CARD, fg=color,
                              font=(FONT_FAMILY, 24, "bold"))
        value_lbl.pack(anchor="w", pady=(4, 0))
        # Guardamos referencia para poder actualizar
        card._value_label = value_lbl  # type: ignore
        return card

    def _build_sim_canvas(self, parent: tk.Widget) -> None:
        """Área scrolleable con los bloques de procesos."""
        wrap = Card(parent, title="Línea de producción en vivo")
        wrap.pack(side="top", fill="both", expand=True, pady=(0, 12))

        canvas_frame = tk.Frame(wrap.body, bg=BG_CARD)
        canvas_frame.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(canvas_frame, bg=BG_CARD, highlightthickness=0)
        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal",
                                  command=self._canvas.xview,
                                  style="Modern.Horizontal.TScrollbar")
        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self._canvas.yview,
                                  style="Modern.Vertical.TScrollbar")
        self._canvas.configure(xscrollcommand=h_scroll.set,
                                yscrollcommand=v_scroll.set)

        self._canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self._sim_frame = tk.Frame(self._canvas, bg=BG_CARD)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._sim_frame,
                                                          anchor="nw")
        self._sim_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )

        self._show_empty_state()

    def _show_empty_state(self):
        """Mensaje cuando aún no se ha iniciado simulación."""
        for w in self._sim_frame.winfo_children():
            w.destroy()
        wrap = tk.Frame(self._sim_frame, bg=BG_CARD)
        wrap.pack(padx=40, pady=40)
        tk.Label(wrap, text="◇", bg=BG_CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 36)).pack()
        tk.Label(wrap, text="Sin simulación activa",
                 bg=BG_CARD, fg=TEXT_PRIMARY,
                 font=FONT_TITLE).pack(pady=(6, 4))
        tk.Label(wrap, text="Configure procesos y tareas, luego pulse Iniciar.",
                 bg=BG_CARD, fg=TEXT_SECONDARY,
                 font=FONT_BODY).pack()

    def _build_controls_card(self, parent: tk.Widget) -> None:
        """Tarjeta con modo de ejecución, botonera y slider de velocidad."""
        card = Card(parent, padding=14)
        card.pack(side="top", fill="x")

        # ── Fila 1: Modo de ejecución ─────────────────────────────────────────
        mode_row = tk.Frame(card.body, bg=BG_CARD)
        mode_row.pack(side="top", fill="x", pady=(0, 10))

        tk.Label(mode_row, text="MODO DE EJECUCIÓN:", bg=BG_CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 9, "bold")).pack(side="left", padx=(0, 14))

        # Radio-buttons estilizados (indicatoron=False → aspecto de botón toggle)
        rb_style = dict(
            bg=BG_CARD, activebackground=BG_CARD_HOVER,
            selectcolor=ACCENT_PRIMARY,
            fg=TEXT_PRIMARY, activeforeground=TEXT_PRIMARY,
            font=FONT_BODY_BOLD, indicatoron=False,
            padx=14, pady=7, cursor="hand2", relief="flat",
            variable=self._mode_var, command=self._on_mode_change,
        )
        self._rb_auto = tk.Radiobutton(mode_row, text="▶▶  Automático",
                                        value="auto", **rb_style)
        self._rb_step = tk.Radiobutton(mode_row, text="▶|  Por ciclos (manual)",
                                        value="step", **rb_style)
        self._rb_auto.pack(side="left", padx=(0, 6))
        self._rb_step.pack(side="left")

        # Descripción dinámica del modo
        self._lbl_mode_hint = tk.Label(
            mode_row,
            text="  La simulación avanza sola ciclo a ciclo",
            bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL,
        )
        self._lbl_mode_hint.pack(side="left", padx=(16, 0))

        # Separador fino
        tk.Frame(card.body, bg="#2d3548", height=1).pack(fill="x", pady=(0, 10))

        # ── Fila 2: Botonera ──────────────────────────────────────────────────
        btns = tk.Frame(card.body, bg=BG_CARD)
        btns.pack(side="top", fill="x")

        self._btn_start = ModernButton(btns, text="▶  Iniciar", variant="primary",
                                        command=self._on_start)
        self._btn_start.pack(side="left", padx=(0, 6))

        self._btn_pause = ModernButton(btns, text="||  Pausar", variant="warning",
                                        command=self._on_pause)
        self._btn_pause.pack(side="left", padx=6)

        self._btn_resume = ModernButton(btns, text="▶  Reanudar", variant="success",
                                         command=self._on_resume)
        self._btn_resume.pack(side="left", padx=6)

        self._btn_step = ModernButton(btns, text="▶|  Siguiente ciclo",
                                       variant="secondary",
                                       command=self._on_step)
        self._btn_step.pack(side="left", padx=6)

        self._btn_reset = ModernButton(btns, text="↺  Reiniciar sim", variant="secondary",
                                        command=self._on_reset)
        self._btn_reset.pack(side="left", padx=6)

        self._btn_report = ModernButton(btns, text="=  Estadísticas",
                                         variant="secondary",
                                         command=self._on_show_stats)
        self._btn_report.pack(side="left", padx=6)

        self._btn_full_reset = ModernButton(btns, text="⊗  Reset total",
                                             variant="danger",
                                             command=self._full_reset)
        self._btn_full_reset.pack(side="left", padx=(18, 0))

        # ── Fila 3: Slider de velocidad (solo relevante en modo auto) ─────────
        speed = tk.Frame(card.body, bg=BG_CARD)
        speed.pack(side="top", fill="x", pady=(12, 0))
        tk.Label(speed, text="VELOCIDAD (modo auto)", bg=BG_CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 9, "bold")).pack(side="left")
        self._lbl_speed = tk.Label(speed, text=f"{self._cycle_ms} ms/ciclo",
                                    bg=BG_CARD, fg=TEXT_PRIMARY,
                                    font=FONT_BODY_BOLD)
        self._lbl_speed.pack(side="right")
        self._scale_speed = ttk.Scale(speed, from_=50, to=2000, orient="horizontal",
                                       style="Modern.Horizontal.TScale",
                                       command=self._on_speed_change)
        self._scale_speed.set(self._cycle_ms)
        self._scale_speed.pack(side="left", fill="x", expand=True, padx=12)

    # ══════════════════════════════════════════════════════════════════════════
    # Configuración de la línea
    # ══════════════════════════════════════════════════════════════════════════

    def _add_process(self) -> None:
        if self._sim_running():
            messagebox.showwarning("Simulación activa",
                                   "Detenga o reinicie la simulación antes de modificar la línea.")
            return

        # No se puede crear otro proceso mientras haya uno pendiente de confirmar
        if self._pending_process is not None:
            messagebox.showerror(
                "Proceso pendiente",
                f"El proceso '{self._pending_process.name}' aún no ha sido confirmado.\n"
                "Agréguele al menos una tarea y pulse '✓ Confirmar proceso' antes de continuar."
            )
            return

        name = self._entry_proc_name.get().strip()
        if not name:
            messagebox.showwarning("Dato faltante", "Ingrese el nombre del proceso.")
            return

        is_initial = self._var_is_initial.get()
        is_final = self._var_is_final.get()

        # Verificar unicidad de inicial/final contra la línea ya confirmada
        line = self._line
        if is_initial and line is not None and line.initial_process is not None:
            messagebox.showerror("Solo un proceso inicial",
                                 f"Ya existe un proceso inicial: '{line.initial_process.name}'.")
            return
        if is_final and line is not None and line.final_process is not None:
            messagebox.showerror("Solo un proceso final",
                                 f"Ya existe un proceso final: '{line.final_process.name}'.")
            return

        # Crear proceso pendiente; cancelar cualquier edición activa
        self._edit_target = None
        self._btn_cancel_edit.set_enabled(False)
        self._pending_process = Process(name=name, is_initial=is_initial, is_final=is_final)

        self._entry_proc_name.delete(0, "end")
        self._var_is_initial.set(False)
        self._var_is_final.set(False)

        self._refresh_line_tree()
        self._refresh_task_label()
        self._btn_confirm_proc.set_enabled(False)   # aún sin tareas
        self._set_status(
            f"Proceso '{name}' creado — agréguele tareas y confirme", ACCENT_WARNING
        )

    def _confirm_process(self) -> None:
        """Mueve el proceso pendiente a la línea confirmada (requiere ≥1 tarea)."""
        if self._pending_process is None:
            return
        if self._pending_process.task_count == 0:
            messagebox.showerror(
                "Sin tareas",
                f"El proceso '{self._pending_process.name}' necesita al menos una tarea\n"
                "antes de poder ser confirmado."
            )
            return
        if self._line is None:
            self._line = ProductionLine()
        self._line.add_process(self._pending_process)
        name = self._pending_process.name
        self._pending_process = None
        self._btn_confirm_proc.set_enabled(False)
        self._refresh_line_tree()
        self._refresh_task_label()
        self._set_status(f"Proceso '{name}' confirmado y añadido a la línea", ACCENT_SUCCESS)

    def _refresh_task_label(self) -> None:
        """Actualiza la etiqueta de la sección de tareas con el proceso activo."""
        if self._pending_process is not None:
            self._lbl_task_section.config(
                text=f"2 · TAREAS  →  '{self._pending_process.name}' (pendiente)",
                fg=ACCENT_WARNING,
            )
        elif self._edit_target is not None:
            self._lbl_task_section.config(
                text=f"2 · TAREAS  →  '{self._edit_target.name}' (editando)",
                fg=ACCENT_PRIMARY,
            )
        elif self._line is not None and self._line.processes:
            last = self._line.processes[-1]
            self._lbl_task_section.config(
                text=f"2 · TAREAS  →  '{last.name}' (último confirmado)",
                fg=TEXT_MUTED,
            )
        else:
            self._lbl_task_section.config(
                text="2 · TAREAS  (cree primero un proceso)",
                fg=TEXT_MUTED,
            )

    def _on_edit_selected(self) -> None:
        """Activa el modo edición para el proceso seleccionado en el árbol."""
        if self._sim_running():
            messagebox.showwarning("Simulación activa",
                                   "Detenga la simulación antes de editar la línea.")
            return
        if self._pending_process is not None:
            messagebox.showerror(
                "Proceso pendiente",
                f"Confirme primero el proceso '{self._pending_process.name}' "
                "antes de editar otro."
            )
            return
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un proceso en el árbol para editarlo.")
            return
        proc = self._tree_item_to_proc.get(sel[0])
        if proc is None:
            messagebox.showinfo("Selección inválida",
                                "Seleccione un proceso (no una tarea individual).")
            return
        self._edit_target = proc
        self._btn_cancel_edit.set_enabled(True)
        self._refresh_line_tree()
        self._refresh_task_label()
        self._set_status(f"Editando '{proc.name}' — agregue tareas y pulse Cancelar edición al terminar",
                         ACCENT_PRIMARY)

    def _cancel_edit(self) -> None:
        """Desactiva el modo edición."""
        self._edit_target = None
        self._btn_cancel_edit.set_enabled(False)
        self._refresh_line_tree()
        self._refresh_task_label()
        self._set_status("Edición finalizada", ACCENT_SUCCESS)

    def _add_task(self) -> None:
        if self._sim_running():
            messagebox.showwarning("Simulación activa",
                                   "Detenga o reinicie la simulación antes de modificar la línea.")
            return

        # Prioridad: pendiente > en edición > último confirmado
        if self._pending_process is not None:
            target = self._pending_process
        elif self._edit_target is not None:
            target = self._edit_target
        elif self._line is not None and self._line.processes:
            target = self._line.processes[-1]
        else:
            messagebox.showwarning(
                "Sin proceso",
                "Cree primero un proceso antes de agregar tareas."
            )
            return

        name = self._entry_task_name.get().strip()
        if not name:
            messagebox.showwarning("Dato faltante", "Ingrese el nombre de la tarea.")
            return

        try:
            t = int(self._entry_task_time.get())
            if t <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Valor inválido",
                                 "El tiempo debe ser un entero mayor a 0.")
            return

        target.add_task(Task(name=name, process_time=t))

        self._entry_task_name.delete(0, "end")
        self._entry_task_time.delete(0, "end")

        # Habilitar confirmar si el destino era el proceso pendiente
        if self._pending_process is not None:
            self._btn_confirm_proc.set_enabled(True)

        self._refresh_line_tree()
        self._set_status(f"Tarea '{name}' agregada a '{target.name}'", ACCENT_SUCCESS)

    def _clear_line(self) -> None:
        if self._sim_running():
            messagebox.showwarning("Simulación activa",
                                   "Detenga o reinicie la simulación antes de modificar la línea.")
            return
        if self._line is None and self._pending_process is None:
            return
        if not messagebox.askyesno("Confirmar",
                                   "¿Borrar TODA la línea (procesos, tareas y proceso pendiente)?"):
            return
        self._line = None
        self._pending_process = None
        self._edit_target = None
        self._btn_confirm_proc.set_enabled(False)
        self._btn_cancel_edit.set_enabled(False)
        self._refresh_line_tree()
        self._refresh_task_label()
        self._set_status("Línea limpiada", ACCENT_WARNING)

    def _load_demo(self) -> None:
        if self._sim_running():
            messagebox.showwarning("Simulación activa",
                                   "Detenga o reinicie la simulación antes de cargar el demo.")
            return
        if self._line is not None and self._line.processes:
            if not messagebox.askyesno("Confirmar",
                                       "Se reemplazará la línea actual con el demo. ¿Continuar?"):
                return

        demo = ProductionLine()
        demo_data = [
            ("Corte",    True,  False, [("Corte láser", 2), ("Pulido",      2)]),
            ("Ensamble", False, False, [("Armado",       3), ("Soldadura",   4)]),
            ("Pintura",  False, False, [("Imprimación",  2), ("Pintura",     3)]),
            ("Revisión", False, False, [("Inspección",   2), ("Corrección",  1)]),
            ("Empaque",  False, True,  [("Empacar",      2), ("Etiquetado",  1)]),
        ]
        for proc_name, is_initial, is_final, tasks in demo_data:
            proc = Process(name=proc_name, is_initial=is_initial, is_final=is_final)
            for task_name, t in tasks:
                proc.add_task(Task(name=task_name, process_time=t))
            demo.add_process(proc)

        self._line = demo
        self._pending_process = None
        self._edit_target = None
        self._btn_confirm_proc.set_enabled(False)
        self._btn_cancel_edit.set_enabled(False)
        self._entry_n_products.delete(0, "end")
        self._entry_n_products.insert(0, "5")
        self._refresh_line_tree()
        self._refresh_task_label()
        self._set_status("Demo cargado — 5 procesos × 2 tareas (cuello en Soldadura)", ACCENT_SUCCESS)

    def _refresh_line_tree(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._tree_item_to_proc.clear()

        has_content = (self._line is not None and self._line.processes) or \
                      self._pending_process is not None
        if not has_content:
            self._tree.insert("", "end", text="(línea vacía)", values=("—",))
            return

        if self._line is not None:
            for proc in self._line.processes:
                # Indicador visual extra si es el proceso en edición activa
                editing = (self._edit_target is proc)
                label = proc.name
                tag = ""
                if proc.is_initial:
                    tag = "  INICIAL"
                    label = "● " + label
                elif proc.is_final:
                    tag = "  FINAL"
                    label = "● " + label
                else:
                    label = "○ " + label
                if editing:
                    label += "  ← EDITANDO"
                proc_id = self._tree.insert("", "end", text=label + tag,
                                            values=(f"{proc.task_count} tareas",), open=True)
                self._tree_item_to_proc[proc_id] = proc
                for task in proc.tasks:
                    self._tree.insert(proc_id, "end", text="     " + task.name,
                                      values=(f"t = {task.process_time}",))

        # Proceso pendiente (aún sin confirmar)
        if self._pending_process is not None:
            p = self._pending_process
            tag = ""
            if p.is_initial:
                tag = "  INICIAL"
            elif p.is_final:
                tag = "  FINAL"
            label = f"◈ {p.name}{tag}  ← PENDIENTE"
            proc_id = self._tree.insert("", "end", text=label,
                                        values=(f"{p.task_count} tareas",), open=True)
            for task in p.tasks:
                self._tree.insert(proc_id, "end", text="     " + task.name,
                                  values=(f"t = {task.process_time}",))

    # ══════════════════════════════════════════════════════════════════════════
    # Control de simulación
    # ══════════════════════════════════════════════════════════════════════════

    def _check_initial_final(self) -> bool:
        """
        Verifica que el primer proceso sea INICIAL y el último sea FINAL.
        Ofrece auto-corregirlo si el usuario acepta.
        Retorna False si el usuario cancela o hay un conflicto no resolvible.
        """
        if self._line is None or not self._line.processes:
            return True
        procs = self._line.processes

        # ── Verificar proceso inicial ──────────────────────────────────────
        initials = [p for p in procs if p.is_initial]
        if not initials:
            resp = messagebox.askyesnocancel(
                "Sin proceso INICIAL",
                f"Ningún proceso está marcado como Inicial.\n\n"
                f"El primer proceso de la línea es '{procs[0].name}'.\n"
                f"¿Marcarlo automáticamente como Inicial?",
            )
            if resp is True:
                procs[0].is_initial = True
                self._refresh_line_tree()
            elif resp is False:
                messagebox.showinfo(
                    "Corrija la configuración",
                    "Edite la línea y marque un proceso como Inicial antes de iniciar."
                )
                return False
            else:  # Cancel
                return False
        elif not procs[0].is_initial:
            # Hay un inicial pero no es el primero — dejar que validate() lo atrape
            pass

        # ── Verificar proceso final ────────────────────────────────────────
        finals = [p for p in procs if p.is_final]
        if not finals:
            resp = messagebox.askyesnocancel(
                "Sin proceso FINAL",
                f"Ningún proceso está marcado como Final.\n\n"
                f"El último proceso de la línea es '{procs[-1].name}'.\n"
                f"¿Marcarlo automáticamente como Final?",
            )
            if resp is True:
                procs[-1].is_final = True
                self._refresh_line_tree()
            elif resp is False:
                messagebox.showinfo(
                    "Corrija la configuración",
                    "Edite la línea y marque un proceso como Final antes de iniciar."
                )
                return False
            else:
                return False

        return True

    def _on_start(self) -> None:
        if self._pending_process is not None:
            messagebox.showerror(
                "Proceso sin confirmar",
                f"El proceso '{self._pending_process.name}' aún está pendiente.\n"
                "Confírmelo (con ≥1 tarea) antes de iniciar la simulación."
            )
            return
        if self._line is None:
            messagebox.showerror("Línea vacía", "Cree al menos un proceso con sus tareas.")
            return
        if not self._check_initial_final():
            return
        try:
            self._line.validate()
        except ValueError as e:
            messagebox.showerror("Error de configuración", str(e))
            return

        try:
            n = int(self._entry_n_products.get())
            if n <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Valor inválido",
                                 "La cantidad de productos debe ser un entero > 0.")
            return

        self._sim = Simulator(self._line, n_products=n)
        self._sim.start()

        self._build_sim_view()
        self._refresh_ui(self._sim.snapshot())
        self._update_button_states()

        mode = self._mode_var.get()
        if mode == "auto":
            self._set_status(f"Simulación iniciada con {n} productos — Modo automático",
                             ACCENT_PRIMARY)
            self._schedule_next_cycle()
        else:
            self._set_status(
                f"Simulación iniciada con {n} productos — Modo ciclos: use '▶| Siguiente ciclo'",
                ACCENT_WARNING,
            )

    def _on_pause(self) -> None:
        if not self._sim or not self._sim.is_started or self._sim.is_paused:
            return
        self._cancel_timer()
        self._sim.pause()
        self._show_pause_window(self._sim.snapshot())
        self._update_button_states()
        self._set_status(f"Pausada en ciclo {self._sim.current_cycle}", ACCENT_WARNING)

    def _on_resume(self) -> None:
        if not self._sim or not self._sim.is_paused:
            return
        self._sim.resume()
        self._update_button_states()
        self._set_status("Reanudada", ACCENT_PRIMARY)
        self._schedule_next_cycle()

    def _on_step(self) -> None:
        if not self._sim or not self._sim.is_started or self._sim.is_done:
            return
        if self._mode_var.get() == "auto":
            # En modo auto: detener timer, hacer un paso y volver a pausar
            was_paused = self._sim.is_paused
            if not was_paused:
                self._cancel_timer()
                self._sim.pause()
            self._sim.resume()
            self._sim.step()
            if not self._sim.is_done:
                self._sim.pause()
        else:
            # En modo ciclos: avanzar directo sin jugar con el timer
            self._sim.step()
        self._refresh_ui(self._sim.snapshot())
        if self._sim.is_done:
            self._on_simulation_done()
        self._update_button_states()
        self._set_status(f"Ciclo {self._sim.current_cycle}", ACCENT_PRIMARY)

    def _on_reset(self) -> None:
        self._cancel_timer()
        if self._sim is not None:
            self._sim.reset()
            self._sim = None
        self._task_widgets.clear()
        self._show_empty_state()
        self._metric_cycle._value_label.config(text="0")  # type: ignore
        self._metric_done._value_label.config(text="0 / 0")  # type: ignore
        self._metric_progress._value_label.config(text="0")  # type: ignore
        self._progress_global["value"] = 0
        self._lbl_progress_pct.config(text="0%")
        if self._pause_window is not None and self._pause_window.winfo_exists():
            self._pause_window.destroy()
            self._pause_window = None
        self._update_button_states()
        self._set_status("Listo", ACCENT_SUCCESS)

    def _full_reset(self) -> None:
        """Detiene la simulación Y borra la línea: todo vuelve al estado inicial."""
        if not messagebox.askyesno("Reset total",
                                   "¿Borrar la línea de producción y detener la simulación?\n"
                                   "Todo comenzará desde cero."):
            return
        self._cancel_timer()
        self._sim = None
        self._line = None
        self._pending_process = None
        self._edit_target = None
        self._task_widgets.clear()
        self._show_empty_state()
        self._metric_cycle._value_label.config(text="0")       # type: ignore
        self._metric_done._value_label.config(text="0 / 0")    # type: ignore
        self._metric_progress._value_label.config(text="0")    # type: ignore
        self._progress_global["value"] = 0
        self._lbl_progress_pct.config(text="0%")
        if self._pause_window is not None and self._pause_window.winfo_exists():
            self._pause_window.destroy()
            self._pause_window = None
        self._btn_confirm_proc.set_enabled(False)
        self._btn_cancel_edit.set_enabled(False)
        self._refresh_line_tree()
        self._refresh_task_label()
        self._update_button_states()
        self._set_status("Reset total — línea y simulación borradas", ACCENT_DANGER)

    def _on_speed_change(self, value: str) -> None:
        try:
            self._cycle_ms = int(float(value))
            self._lbl_speed.config(text=f"{self._cycle_ms} ms/ciclo")
        except ValueError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # Loop de simulación (timer Tkinter)
    # ══════════════════════════════════════════════════════════════════════════

    def _schedule_next_cycle(self) -> None:
        self._timer_id = self.after(self._cycle_ms, self._tick)

    def _cancel_timer(self) -> None:
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    def _tick(self) -> None:
        self._timer_id = None
        if self._sim is None or self._sim.is_paused or self._sim.is_done:
            return
        self._sim.step()
        self._refresh_ui(self._sim.snapshot())
        if self._sim.is_done:
            self._on_simulation_done()
        else:
            self._schedule_next_cycle()

    # ══════════════════════════════════════════════════════════════════════════
    # Construcción dinámica de la vista de simulación
    # ══════════════════════════════════════════════════════════════════════════

    def _build_sim_view(self) -> None:
        for widget in self._sim_frame.winfo_children():
            widget.destroy()
        self._task_widgets.clear()
        if self._sim is None:
            return

        snap = self._sim.snapshot()
        processes = snap["line"]["processes"]

        for col, proc_data in enumerate(processes):
            proc_block = self._build_process_block(self._sim_frame, proc_data)
            proc_block.grid(row=0, column=col * 2, padx=4, pady=12, sticky="n")

            if col < len(processes) - 1:
                arrow = tk.Label(self._sim_frame, text="❯",
                                 font=(FONT_FAMILY, 22, "bold"),
                                 fg=TEXT_MUTED, bg=BG_CARD)
                arrow.grid(row=0, column=col * 2 + 1, padx=4, pady=80)

    def _build_process_block(self, parent: tk.Widget, proc_data: dict) -> tk.Widget:
        if proc_data["is_initial"]:
            accent = PROC_INITIAL
            tag = "INICIAL"
        elif proc_data["is_final"]:
            accent = PROC_FINAL
            tag = "FINAL"
        else:
            accent = PROC_MIDDLE
            tag = ""

        # Contenedor exterior (sin borde, con padding)
        outer = tk.Frame(parent, bg=BG_PANEL)

        # Header de proceso con indicador de color
        header = tk.Frame(outer, bg=BG_PANEL)
        header.pack(side="top", fill="x", padx=12, pady=(12, 6))

        # Indicador (puntito de color)
        tk.Label(header, text="●", bg=BG_PANEL, fg=accent,
                 font=(FONT_FAMILY, 14)).pack(side="left", padx=(0, 6))
        tk.Label(header, text=proc_data["process_name"], bg=BG_PANEL,
                 fg=TEXT_PRIMARY, font=FONT_SUBTITLE).pack(side="left")
        if tag:
            tk.Label(header, text=tag, bg=accent, fg=BG_BASE,
                     font=(FONT_FAMILY, 7, "bold"),
                     padx=6, pady=2).pack(side="right")

        # Cuerpo con las tareas
        body = tk.Frame(outer, bg=BG_PANEL)
        body.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 12))

        for task_data in proc_data["tasks"]:
            tw = self._build_task_widget(body, proc_data["process_name"], task_data)
            tw.pack(side="top", fill="x", pady=4)

        return outer

    def _build_task_widget(self, parent: tk.Widget, proc_name: str,
                            task_data: dict) -> tk.Widget:
        """Tarjeta visual de una tarea."""
        # Borde exterior (1px del color de estado, simula borde)
        outer = tk.Frame(parent, bg=TASK_FREE_BORDER, padx=1, pady=1)

        card = tk.Frame(outer, bg=TASK_FREE_BG)
        card.pack(fill="both", expand=True)

        # Header con nombre y tiempo
        header = tk.Frame(card, bg=TASK_FREE_BG)
        header.pack(side="top", fill="x", padx=10, pady=(8, 2))

        lbl_name = tk.Label(header, text=task_data["task_name"],
                            bg=TASK_FREE_BG, fg=TEXT_PRIMARY,
                            font=FONT_BODY_BOLD, anchor="w")
        lbl_name.pack(side="left")

        lbl_time = tk.Label(header, text=f"{task_data['process_time']}c",
                            bg=TASK_FREE_BG, fg=TEXT_MUTED,
                            font=FONT_TINY)
        lbl_time.pack(side="right")

        # Estado
        lbl_state = tk.Label(card, text="○ Libre",
                             bg=TASK_FREE_BG, fg=TASK_FREE_TEXT,
                             font=FONT_SMALL, anchor="w")
        lbl_state.pack(side="top", fill="x", padx=10, pady=(0, 4))

        # Barra de progreso del producto actual
        bar = ttk.Progressbar(card, length=180, mode="determinate",
                              style="Task.Horizontal.TProgressbar")
        bar.pack(side="top", padx=10, pady=(0, 4), fill="x")

        # Cola
        lbl_queue = tk.Label(card, text="Cola: 0", bg=TASK_FREE_BG,
                             fg=TEXT_MUTED, font=FONT_TINY, anchor="w")
        lbl_queue.pack(side="top", fill="x", padx=10, pady=(0, 8))

        key = f"{proc_name}::{task_data['task_name']}"
        self._task_widgets[key] = {
            "outer": outer, "card": card, "header": header,
            "lbl_name": lbl_name, "lbl_time": lbl_time,
            "lbl_state": lbl_state, "lbl_queue": lbl_queue,
            "bar": bar, "process_time": task_data["process_time"],
        }
        return outer

    # ══════════════════════════════════════════════════════════════════════════
    # Refresco visual
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_ui(self, snap: Optional[dict]) -> None:
        if snap is None:
            return

        # Métricas superiores
        self._metric_cycle._value_label.config(text=str(snap["cycle"]))  # type: ignore
        total = snap["products_total"]
        done = snap["products_completed"]
        self._metric_done._value_label.config(text=f"{done} / {total}")  # type: ignore
        self._metric_progress._value_label.config(  # type: ignore
            text=str(snap["products_in_progress"])
        )

        if total > 0:
            self._progress_global["maximum"] = total
            self._progress_global["value"] = done
            pct = int(100 * done / total)
            self._lbl_progress_pct.config(text=f"{pct}% completado")

        # Cada tarea
        for proc_data in snap["line"]["processes"]:
            for task_data in proc_data["tasks"]:
                key = f"{proc_data['process_name']}::{task_data['task_name']}"
                widgets = self._task_widgets.get(key)
                if widgets is None:
                    continue
                self._update_task_widget(widgets, task_data)

    def _update_task_widget(self, widgets: dict, task_data: dict) -> None:
        busy = task_data["busy"]
        queue = task_data["queue_size"]

        # Color según estado
        if busy and queue > 0:
            bg, border, accent_text = TASK_QUEUED_BG, TASK_QUEUED_BORDER, TASK_QUEUED_TEXT
        elif busy:
            bg, border, accent_text = TASK_BUSY_BG, TASK_BUSY_BORDER, TASK_BUSY_TEXT
        else:
            bg, border, accent_text = TASK_FREE_BG, TASK_FREE_BORDER, TASK_FREE_TEXT

        widgets["outer"].config(bg=border)
        for w in (widgets["card"], widgets["header"], widgets["lbl_name"],
                  widgets["lbl_time"], widgets["lbl_state"], widgets["lbl_queue"]):
            w.config(bg=bg)
        widgets["lbl_state"].config(fg=accent_text)

        # Estado textual + barra
        if busy:
            pid = task_data["current_product_id"]
            rem = task_data["remaining_cycles"]
            widgets["lbl_state"].config(
                text=f"● Procesando P{pid} · {rem}c restantes"
            )
            pt = widgets["process_time"]
            widgets["bar"]["maximum"] = pt
            widgets["bar"]["value"] = pt - rem
        else:
            widgets["lbl_state"].config(text="○ Libre")
            widgets["bar"]["value"] = 0

        # Cola
        if queue > 0:
            ids = task_data["queue_product_ids"]
            ids_str = " · ".join(f"P{i}" for i in ids[:4])
            if len(ids) > 4:
                ids_str += f" +{len(ids) - 4}"
            widgets["lbl_queue"].config(text=f"Cola: {queue}   {ids_str}")
        else:
            widgets["lbl_queue"].config(text="Cola: 0")

    # ══════════════════════════════════════════════════════════════════════════
    # Pausa / fin de simulación
    # ══════════════════════════════════════════════════════════════════════════

    def _show_pause_window(self, snap: dict) -> None:
        if self._pause_window is not None and self._pause_window.winfo_exists():
            self._pause_window.destroy()

        win = tk.Toplevel(self)
        win.title(f"Snapshot · Ciclo {snap['cycle']}")
        win.geometry("720x580")
        win.configure(bg=BG_BASE)
        self._pause_window = win

        # Header
        header = tk.Frame(win, bg=BG_BASE)
        header.pack(side="top", fill="x", padx=20, pady=(16, 4))
        tk.Label(header, text=f"Ciclo {snap['cycle']}", bg=BG_BASE,
                 fg=ACCENT_PRIMARY, font=FONT_DISPLAY).pack(side="left")
        info = tk.Frame(header, bg=BG_BASE)
        info.pack(side="left", padx=20, pady=(8, 0), anchor="s")
        tk.Label(info,
                 text=f"{snap['products_completed']} completados",
                 bg=BG_BASE, fg=ACCENT_SUCCESS, font=FONT_BODY_BOLD).pack(anchor="w")
        tk.Label(info,
                 text=f"{snap['products_in_progress']} en proceso · "
                      f"{snap['products_total']} totales",
                 bg=BG_BASE, fg=TEXT_SECONDARY, font=FONT_SMALL).pack(anchor="w")

        # Texto con detalle
        body = tk.Frame(win, bg=BG_BASE)
        body.pack(side="top", fill="both", expand=True, padx=20, pady=12)

        text = tk.Text(body, font=FONT_MONO, wrap="none",
                       bg=BG_CARD, fg=TEXT_PRIMARY,
                       borderwidth=0, padx=12, pady=12,
                       insertbackground=TEXT_PRIMARY)
        vs = ttk.Scrollbar(body, orient="vertical", command=text.yview,
                           style="Modern.Vertical.TScrollbar")
        text.configure(yscrollcommand=vs.set)
        text.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

        lines = []
        for proc in snap["line"]["processes"]:
            tag = ""
            if proc["is_initial"]:
                tag = "  [INICIAL]"
            elif proc["is_final"]:
                tag = "  [FINAL]"
            lines.append(f"━━━ {proc['process_name']}{tag} ━━━")
            for task in proc["tasks"]:
                if task["busy"]:
                    estado = (f"PROC P{task['current_product_id']} "
                              f"({task['remaining_cycles']}/{task['process_time']}c)")
                else:
                    estado = "LIBRE"
                cola = ""
                if task["queue_size"] > 0:
                    ids = ", ".join(f"P{i}" for i in task["queue_product_ids"])
                    cola = f"  cola=[{ids}]"
                lines.append(f"  · {task['task_name']:<24} t={task['process_time']:<2}  {estado}{cola}")
                lines.append(f"        procesados={task['products_processed']}  "
                             f"espera_prom={task['avg_wait_cycles']:.2f}c")
            lines.append("")

        if snap["completed_products"]:
            lines.append("━━━ Productos completados ━━━")
            for p in snap["completed_products"]:
                lines.append(f"  ✓ P{p['product_id']}  "
                             f"entró={p['entry_time']} salió={p['exit_time']} "
                             f"total={p['total_time']}c")

        text.insert("1.0", "\n".join(lines))
        text.config(state="disabled")

        # Botón cerrar
        ModernButton(win, text="Cerrar", variant="primary",
                     command=win.destroy).pack(side="bottom", pady=(0, 16))

    def _on_simulation_done(self) -> None:
        self._cancel_timer()
        self._update_button_states()
        self._set_status(f"Finalizada en ciclo {self._sim.current_cycle}",
                         ACCENT_SUCCESS)

        stats = self._sim.get_stats()
        if stats["bottleneck_task"]:
            key = f"{stats['bottleneck_process']}::{stats['bottleneck_task']}"
            widgets = self._task_widgets.get(key)
            if widgets is not None:
                widgets["outer"].config(bg=TASK_BOTTLENECK_BORDER)
                for w in (widgets["card"], widgets["header"], widgets["lbl_name"],
                          widgets["lbl_time"], widgets["lbl_state"], widgets["lbl_queue"]):
                    w.config(bg=TASK_BOTTLENECK_BG)
                widgets["lbl_state"].config(text="★ CUELLO DE BOTELLA",
                                             fg=TASK_BOTTLENECK_TEXT)

        msg = (f"Todos los {stats['products_total']} productos completaron la línea.\n\n"
               f"• Total ciclos:       {stats['total_cycles_run']}\n"
               f"• Primer producto:    ciclo {stats['first_completion_cycle']}\n"
               f"• Último producto:    ciclo {stats['last_completion_cycle']}\n"
               f"• Tiempo promedio:    {stats['avg_completion_time']:.2f} ciclos\n"
               f"• Cuello de botella:  {stats['bottleneck_process']} / "
               f"{stats['bottleneck_task']}")
        messagebox.showinfo("Simulación finalizada", msg)

    def _on_show_stats(self) -> None:
        if self._sim is None or not self._sim.is_started:
            messagebox.showinfo("Sin datos", "Inicie una simulación primero.")
            return
        self._show_stats_window(self._sim.get_stats())

    def _show_stats_window(self, stats: dict) -> None:
        win = tk.Toplevel(self)
        win.title("Estadísticas de la simulación")
        win.geometry("760x600")
        win.configure(bg=BG_BASE)

        header = tk.Frame(win, bg=BG_BASE)
        header.pack(side="top", fill="x", padx=20, pady=(16, 8))
        tk.Label(header, text="Estadísticas finales", bg=BG_BASE,
                 fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")

        body = tk.Frame(win, bg=BG_BASE)
        body.pack(side="top", fill="both", expand=True, padx=20, pady=12)

        text = tk.Text(body, font=FONT_MONO, wrap="none",
                       bg=BG_CARD, fg=TEXT_PRIMARY,
                       borderwidth=0, padx=14, pady=14,
                       insertbackground=TEXT_PRIMARY)
        vs = ttk.Scrollbar(body, orient="vertical", command=text.yview,
                           style="Modern.Vertical.TScrollbar")
        text.configure(yscrollcommand=vs.set)
        text.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

        def fmt(v):
            return "—" if v is None else v

        lines = [
            "═══ RESUMEN GENERAL ═══",
            f"  Ciclos corridos:               {stats['total_cycles_run']}",
            f"  Productos totales:             {stats['products_total']}",
            f"  Productos completados:         {stats['products_completed']}",
            "",
            "═══ TIEMPOS ═══",
            f"  Primer producto en ciclo:      {fmt(stats['first_completion_cycle'])}",
            f"  Último producto en ciclo:      {fmt(stats['last_completion_cycle'])}",
            f"  Tiempo promedio de paso:       {stats['avg_completion_time']:.2f} ciclos",
            f"  Tiempo total acumulado:        {stats['total_processing_time']} ciclos",
            "",
            "═══ ESPERAS Y CUELLO DE BOTELLA ═══",
            f"  Espera promedio para iniciar:  {stats['avg_wait_to_start']:.2f} ciclos",
            f"  Cuello de botella (proceso):   {fmt(stats['bottleneck_process'])}",
            f"  Cuello de botella (tarea):     {fmt(stats['bottleneck_task'])}",
            f"  Mayor espera promedio:         {stats['worst_wait_value']:.2f}c en "
            f"{fmt(stats['worst_wait_task'])}",
            "",
            "═══ DETALLE POR TAREA ═══",
        ]
        for ts in stats["task_stats"]:
            lines.append(
                f"  · [{ts['process_name']}] {ts['task_name']:<22} "
                f"procesados={ts['products_processed']:<3} "
                f"espera_prom={ts['avg_wait_cycles']:.2f}c"
            )
        lines.append("")
        lines.append("═══ DETALLE POR PRODUCTO ═══")
        for p in stats["product_stats"]:
            exit_str = str(p["exit_time"]) if p["exit_time"] is not None else "en proceso"
            total_str = str(p["total_time"]) if p["total_time"] is not None else "—"
            lines.append(
                f"  P{p['product_id']:<3} entrada={p['entry_time']:<3} "
                f"salida={exit_str:<12} total={total_str}"
            )

        text.insert("1.0", "\n".join(lines))
        text.config(state="disabled")

        ModernButton(win, text="Cerrar", variant="primary",
                     command=win.destroy).pack(side="bottom", pady=(0, 16))

    # ══════════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _sim_running(self) -> bool:
        return self._sim is not None and self._sim.is_started and not self._sim.is_done

    def _update_button_states(self) -> None:
        sim = self._sim
        no_sim = sim is None
        started = (sim is not None) and sim.is_started
        paused = (sim is not None) and sim.is_paused
        done = (sim is not None) and sim.is_done
        mode = self._mode_var.get()

        self._btn_start.set_enabled(no_sim or done)

        if mode == "auto":
            self._btn_pause.set_enabled(started and not paused and not done)
            self._btn_resume.set_enabled(paused and not done)
            # "Paso" en modo auto actúa como step forzado; habilitado solo si pausado o no corriendo
            self._btn_step.set_enabled(started and not done)
        else:
            # Modo ciclos: Pausa/Reanudar no aplican; "Siguiente ciclo" es el control principal
            self._btn_pause.set_enabled(False)
            self._btn_resume.set_enabled(False)
            self._btn_step.set_enabled(started and not done)

        self._btn_reset.set_enabled(started)
        self._btn_report.set_enabled(started)

        # Bloquear cambio de modo mientras hay simulación activa
        sim_active = started and not done
        state = "disabled" if sim_active else "normal"
        self._rb_auto.config(state=state)
        self._rb_step.config(state=state)

    def _on_mode_change(self) -> None:
        mode = self._mode_var.get()
        if mode == "auto":
            self._lbl_mode_hint.config(
                text="  La simulación avanza sola ciclo a ciclo"
            )
        else:
            self._lbl_mode_hint.config(
                text="  Usted controla cada ciclo pulsando '▶| Siguiente ciclo'"
            )
        self._update_button_states()

    def _set_status(self, msg: str, color: str = ACCENT_SUCCESS) -> None:
        self._status_pill.config(text=f"● {msg}", fg=color)


# ═══════════════════════════════════════════════════════════════════════════════
# Punto de entrada
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    app = LinProdApp()
    app.mainloop()


if __name__ == "__main__":
    main()