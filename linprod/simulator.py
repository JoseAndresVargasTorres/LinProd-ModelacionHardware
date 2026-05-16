"""
simulator.py — Módulo 2: Motor de Simulación
Proyecto LinProd | CE-5507 Modelación Hardware/Software Orientado a Objetos
Instituto Tecnológico de Costa Rica | I Semestre 2026

Este módulo orquesta el avance del tiempo y el movimiento de productos en la
línea de producción. Depende únicamente del Módulo 1 (model.py).

Responsabilidades:
  1. Inyectar productos al proceso inicial al arrancar.
  2. Avanzar la simulación ciclo a ciclo (tick a cada proceso en orden).
  3. Transferir productos entre procesos con semántica de PIPELINE REAL:
     un producto que termina un proceso en el ciclo N entra al proceso
     siguiente en el ciclo N+1 (no en el mismo ciclo).
  4. Marcar productos completados al salir del proceso final.
  5. Soportar pause / resume / reset.
  6. Exportar snapshot del estado y estadísticas para los Módulos 3 y 4.
"""

from __future__ import annotations

from typing import Callable, Optional

from linprod.model import Process, Product, ProductionLine


# ═══════════════════════════════════════════════════════════════════════════════
# Clase Simulator
# ═══════════════════════════════════════════════════════════════════════════════

class Simulator:
    """
    Motor de simulación por eventos discretos para una ProductionLine.

    No crea ni modifica los objetos del modelo: recibe la línea ya construida
    y solo controla su avance en el tiempo.

    Parámetros
    ----------
    line : ProductionLine
        Línea de producción ya construida (con procesos y tareas).
    n_products : int
        Cantidad de productos que se inyectarán a la línea. Debe ser > 0.
    on_pause : callable | None
        Función opcional que recibe el snapshot cuando se llama a pause().
        Usada por la GUI (Módulo 3) para refrescar la vista al pausar.
    """

    def __init__(
        self,
        line: ProductionLine,
        n_products: int,
        on_pause: Optional[Callable[[dict], None]] = None,
    ):
        if n_products <= 0:
            raise ValueError(
                f"n_products debe ser > 0, se recibió {n_products!r}"
            )

        # ── Referencias y configuración ────────────────────────────────────────
        self._line: ProductionLine = line
        self._n_products: int = n_products
        self._on_pause: Optional[Callable[[dict], None]] = on_pause

        # ── Estado público (la GUI puede leer current_cycle directamente) ──────
        self.current_cycle: int = 0

        # ── Estado interno ─────────────────────────────────────────────────────
        self._started: bool = False
        self._paused: bool = False
        self._all_products: list[Product] = []
        self._completed_products: list[Product] = []
        self._snapshots: list[dict] = []

        # Cola de transferencias diferidas entre procesos (pipeline real):
        # cuando un producto termina un proceso en el ciclo N, NO entra al
        # proceso siguiente en ese mismo ciclo, sino al inicio del ciclo N+1.
        self._pending_inter_transfers: list[tuple[Product, Process]] = []

    # ══════════════════════════════════════════════════════════════════════════
    # Métodos públicos de control de simulación
    # ══════════════════════════════════════════════════════════════════════════

    def start(self) -> None:
        """
        Arranca la simulación.

        - Valida la línea de producción.
        - Crea n_products instancias de Product con IDs 1, 2, 3, ...
        - Inyecta todos los productos en el proceso inicial (cycle=0).
          Los que no caben en la primera tarea quedan en su cola FIFO.
        - Marca la simulación como iniciada.
        """
        # Validar la línea (lanza ValueError si no es válida)
        self._line.validate()

        # Crear los productos e inyectarlos en el proceso inicial
        initial = self._line.initial_process
        for i in range(1, self._n_products + 1):
            product = Product(product_id=i, entry_cycle=0)
            self._all_products.append(product)
            initial.receive(product, current_cycle=0)

        self._started = True

    def run(self, n_cycles: int = 100_000) -> None:
        """
        Avanza la simulación hasta `n_cycles` ciclos (por defecto 100 000).

        Se detiene antes de tiempo si la simulación está pausada o si todos
        los productos ya completaron la línea, por lo que llamar a run() sin
        argumentos equivale a "correr hasta terminar".

        Lanza RuntimeError si start() no fue llamado antes.
        """
        if not self._started:
            raise RuntimeError("La simulación no ha sido iniciada. Llame a start() primero.")

        for _ in range(n_cycles):
            if self._paused or self.is_done:
                break
            self._advance_one_cycle()

    def step(self) -> None:
        """
        Avanza la simulación exactamente UN ciclo.

        Pensado para que la GUI llame a este método una vez por frame/timer.
        Si la simulación ya terminó, no hace nada (sin error).

        Lanza RuntimeError si está pausada o no iniciada.
        """
        if not self._started:
            raise RuntimeError("La simulación no ha sido iniciada. Llame a start() primero.")
        if self._paused:
            raise RuntimeError("La simulación está pausada. Llame a resume() primero.")
        if self.is_done:
            return
        self._advance_one_cycle()

    def pause(self) -> dict:
        """
        Pausa la simulación y captura una "foto" del estado actual.

        - Marca la simulación como pausada (run/step ya no avanzan).
        - Genera un snapshot completo y lo guarda en el historial.
        - Si se registró on_pause, lo invoca pasándole el snapshot.

        Retorna
        -------
        dict
            El snapshot del estado actual.
        """
        self._paused = True
        snap = self.snapshot()
        self._snapshots.append(snap)

        if self._on_pause is not None:
            self._on_pause(snap)

        return snap

    def resume(self) -> None:
        """
        Reanuda una simulación previamente pausada.

        Lanza RuntimeError si la simulación no estaba pausada.
        """
        if not self._paused:
            raise RuntimeError("La simulación no está pausada.")
        self._paused = False

    def reset(self) -> None:
        """
        Reinicia toda la simulación SIN recrear los objetos de la línea.

        Después de reset(), llamar a start() vuelve a producir exactamente
        los mismos resultados que la primera vez (determinismo requerido
        por el enunciado).
        """
        # Limpia el estado de procesos y tareas (sin destruirlos)
        self._line.reset()

        # Resetea estado del simulador
        self.current_cycle = 0
        self._started = False
        self._paused = False
        self._all_products.clear()
        self._completed_products.clear()
        self._snapshots.clear()
        self._pending_inter_transfers.clear()

    # ══════════════════════════════════════════════════════════════════════════
    # Propiedades de solo lectura
    # ══════════════════════════════════════════════════════════════════════════

    @property
    def is_started(self) -> bool:
        """True si start() fue llamado al menos una vez."""
        return self._started

    @property
    def is_paused(self) -> bool:
        """True si la simulación está pausada en este momento."""
        return self._paused

    @property
    def is_done(self) -> bool:
        """True si todos los productos completaron la línea de producción."""
        return (
            self._started
            and len(self._completed_products) == self._n_products
        )

    @property
    def completed_products(self) -> list[Product]:
        """Copia de la lista de productos terminados."""
        return list(self._completed_products)

    @property
    def snapshots(self) -> list[dict]:
        """Copia del historial de snapshots de pausas anteriores."""
        return list(self._snapshots)

    # ══════════════════════════════════════════════════════════════════════════
    # Snapshot del estado
    # ══════════════════════════════════════════════════════════════════════════

    def snapshot(self) -> dict:
        """
        Retorna un diccionario con el estado completo de la simulación
        en el ciclo actual.

        Estructura usada directamente por el Módulo 3 (GUI) para refrescar
        la vista, y por el Módulo 4 (Reportería) como complemento de
        get_stats().
        """
        in_progress = sum(
            1 for p in self._all_products if not p.is_completed
        )

        return {
            "cycle": self.current_cycle,
            "started": self._started,
            "paused": self._paused,
            "is_done": self.is_done,
            "products_total": self._n_products,
            "products_completed": len(self._completed_products),
            "products_in_progress": in_progress,
            "line": self._line.snapshot(),
            "completed_products": [p.snapshot() for p in self._completed_products],
            "all_products": [p.snapshot() for p in self._all_products],
        }

    # ══════════════════════════════════════════════════════════════════════════
    # Estadísticas para el Módulo 4 (Reportería)
    # ══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> dict:
        """
        Retorna un diccionario con las estadísticas finales de la simulación.

        Es la interfaz que consume el Módulo 4 para generar el reporte.
        Todas las claves están especificadas en la guía de implementación.
        """
        completed = self._completed_products

        # ── Métricas de tiempo de los productos completados ────────────────────
        if completed:
            first_cycle = min(p.exit_time for p in completed)
            last_cycle = max(p.exit_time for p in completed)
            total_time = sum(p.total_time for p in completed)
            avg_completion_time = total_time / len(completed)
        else:
            first_cycle = None
            last_cycle = None
            total_time = 0
            avg_completion_time = 0.0

        # ── Recolectar snapshots de todas las tareas ───────────────────────────
        task_stats: list[dict] = []
        for proc in self._line.processes:
            for task in proc.tasks:
                task_stats.append(task.snapshot())

        # ── Cuello de botella: tarea con mayor avg_wait_cycles ─────────────────
        bottleneck_task: Optional[str] = None
        bottleneck_process: Optional[str] = None
        if task_stats:
            worst = max(task_stats, key=lambda t: t["avg_wait_cycles"])
            # Solo lo consideramos cuello si efectivamente hubo espera
            if worst["avg_wait_cycles"] > 0:
                bottleneck_task = worst["task_name"]
                bottleneck_process = worst["process_name"]

        # ── Tiempo promedio de espera global (en cola, antes de iniciar tarea) ──
        total_wait = 0
        total_starts = 0
        for p in self._all_products:
            for entry in p.task_history:
                total_wait += entry["wait_cycles"]
                total_starts += 1
        avg_wait_to_start = (
            total_wait / total_starts if total_starts > 0 else 0.0
        )

        # ── Tarea con mayor tiempo de espera promedio ──────────────────────────
        worst_wait_task: Optional[str] = None
        worst_wait_process: Optional[str] = None
        worst_wait_value: float = 0.0
        if task_stats:
            worst = max(task_stats, key=lambda t: t["avg_wait_cycles"])
            if worst["avg_wait_cycles"] > 0:
                worst_wait_task = worst["task_name"]
                worst_wait_process = worst["process_name"]
                worst_wait_value = worst["avg_wait_cycles"]

        return {
            # ── Claves obligatorias por la guía ────────────────────────────────
            "total_cycles_run": self.current_cycle,
            "products_total": self._n_products,
            "products_completed": len(completed),
            "first_completion_cycle": first_cycle,
            "last_completion_cycle": last_cycle,
            "avg_completion_time": avg_completion_time,
            "total_processing_time": total_time,
            "bottleneck_task": bottleneck_task,
            "bottleneck_process": bottleneck_process,
            "task_stats": task_stats,
            "product_stats": [p.snapshot() for p in self._all_products],
            # ── Métricas extra (solicitadas por el enunciado del proyecto) ─────
            "avg_wait_to_start": avg_wait_to_start,
            "worst_wait_task": worst_wait_task,
            "worst_wait_process": worst_wait_process,
            "worst_wait_value": worst_wait_value,
        }

    # ══════════════════════════════════════════════════════════════════════════
    # Lógica interna de avance de ciclos
    # ══════════════════════════════════════════════════════════════════════════

    def _advance_one_cycle(self) -> None:
        """
        Avanza la simulación EXACTAMENTE un ciclo de tiempo, respetando la
        semántica de PIPELINE REAL en los DOS niveles de transferencia:

          (a) Entre procesos: un producto que termina el proceso N en el
              ciclo K entra al proceso N+1 en el ciclo K+1. Se logra con
              la cola self._pending_inter_transfers (Paso 1 + Paso 4).

          (b) Entre tareas del mismo proceso: para evitar que una tarea
              "consuma tiempo" del producto recién recibido en el mismo
              ciclo, se tickean las tareas en ORDEN INVERSO (de la última
              a la primera). Así cada tarea avanza con el producto que ya
              tenía al inicio del ciclo, y solo después puede recibir uno
              nuevo desde la tarea anterior (que ya no le hará tick este
              ciclo).

        Esto garantiza que un producto que necesita 3+2+4+1+2=12 ciclos de
        procesamiento tarde exactamente 12 ciclos (sin ciclos regalados).
        """
        self.current_cycle += 1

        # ── Paso 1: aplicar transferencias inter-proceso diferidas ─────────────
        for product, next_proc in self._pending_inter_transfers:
            next_proc.receive(product, self.current_cycle)
        self._pending_inter_transfers = []

        # ── Paso 2 + 3: tickear procesos respetando pipeline real ──────────────
        new_pending: list[tuple[Product, Process]] = []

        for proc in self._line.processes:
            tasks = proc.tasks
            n_tasks = len(tasks)

            # Tickeamos las tareas en orden INVERSO (última → primera).
            for i in range(n_tasks - 1, -1, -1):
                task = tasks[i]
                finished = task.tick(self.current_cycle)
                if finished is None:
                    continue

                is_last_task = (i == n_tasks - 1)
                if is_last_task:
                    if proc.is_final:
                        finished.mark_completed(self.current_cycle)
                        self._completed_products.append(finished)
                    elif proc.next_process is not None:
                        new_pending.append((finished, proc.next_process))
                else:
                    tasks[i + 1].receive(finished, self.current_cycle)

        # ── Paso 4: guardar pendientes inter-proceso para el siguiente ciclo ───
        self._pending_inter_transfers = new_pending

    # ══════════════════════════════════════════════════════════════════════════
    # Representación
    # ══════════════════════════════════════════════════════════════════════════

    def __repr__(self) -> str:
        state = "no iniciada"
        if self._started:
            if self.is_done:
                state = "terminada"
            elif self._paused:
                state = "pausada"
            else:
                state = "en ejecución"
        return (
            f"Simulator(ciclo={self.current_cycle}, "
            f"productos={len(self._completed_products)}/{self._n_products}, "
            f"{state})"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Bloque de prueba (ejecutar directamente: python3 linprod/simulator.py)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from linprod.model import Process, Task, ProductionLine

    print("═" * 70)
    print(" Prueba del Módulo 2 — Motor de Simulación LinProd")
    print("═" * 70)

    # ── Construir la línea de prueba sugerida por la guía ─────────────────────
    p1 = Process("Ensamblado", is_initial=True)
    p1.add_task(Task("Colocar chasis", process_time=3))
    p1.add_task(Task("Instalar motor", process_time=2))

    p2 = Process("Pintura")
    p2.add_task(Task("Aplicar pintura", process_time=4))

    p3 = Process("Control de calidad", is_final=True)
    p3.add_task(Task("Inspeccion visual", process_time=1))
    p3.add_task(Task("Prueba funcional", process_time=2))

    line = ProductionLine()
    line.add_process(p1)
    line.add_process(p2)
    line.add_process(p3)

    # ── Test 1: simulación completa ───────────────────────────────────────────
    print("\n── Test 1: simulación con 3 productos ──────────────────────────────")
    sim = Simulator(line, n_products=3)
    sim.start()
    sim.run(200)

    stats = sim.get_stats()
    print(f"  Ciclos totales:          {stats['total_cycles_run']}")
    print(f"  Primer producto termino: ciclo {stats['first_completion_cycle']}")
    print(f"  Ultimo producto termino: ciclo {stats['last_completion_cycle']}")
    print(f"  Tiempo promedio:         {stats['avg_completion_time']:.2f} ciclos")
    print(f"  Cuello de botella:       {stats['bottleneck_process']} / {stats['bottleneck_task']}")
    print()
    for p in stats["product_stats"]:
        print(f"  P{p['product_id']}: entró={p['entry_time']}  "
              f"salió={p['exit_time']}  total={p['total_time']}")

    # Verificar resultados esperados (pipeline real: cada ciclo vale 1 unidad)
    expected = {
        1: (0, 12, 12),
        2: (0, 16, 16),
        3: (0, 20, 20),
    }
    print("\n  ── Verificación contra resultado esperado ──")
    all_ok = True
    for p in stats["product_stats"]:
        pid = p["product_id"]
        exp = expected.get(pid)
        got = (p["entry_time"], p["exit_time"], p["total_time"])
        ok = got == exp
        all_ok &= ok
        mark = "✔" if ok else "✘"
        print(f"  {mark} P{pid}: esperado={exp}  obtenido={got}")
    print(f"\n  {'✔ TEST 1 PASA' if all_ok else '✘ TEST 1 FALLA'}")

    # ── Test 2: pause / resume ────────────────────────────────────────────────
    print("\n── Test 2: pause / resume ──────────────────────────────────────────")
    sim.reset()  # limpiar estado del Test 1 (la línea se reusa)
    sim2 = Simulator(line, n_products=2)
    sim2.start()
    sim2.run(5)
    snap = sim2.pause()
    print(f"  Pausado en ciclo: {snap['cycle']} (esperado: 5)")
    print(f"  Productos en progreso: {snap['products_in_progress']}")
    print(f"  is_paused: {sim2.is_paused}")
    sim2.resume()
    print(f"  Después de resume, is_paused: {sim2.is_paused}")
    sim2.run(200)
    print(f"  Completados: {sim2.is_done}  ({len(sim2.completed_products)}/2)")

    # ── Test 3: determinismo (reset + re-simulación) ──────────────────────────
    print("\n── Test 3: determinismo (reset + re-simulación) ────────────────────")
    last_first = sim2.get_stats()["last_completion_cycle"]
    sim2.reset()
    sim2.start()
    sim2.run(200)
    stats_b = sim2.get_stats()
    print(f"  Última terminación corrida 1: ciclo {last_first}")
    print(f"  Última terminación corrida 2: ciclo {stats_b['last_completion_cycle']}")
    deterministic = stats_b["last_completion_cycle"] == last_first
    print(f"  {'✔ DETERMINISTA' if deterministic else '✘ NO DETERMINISTA'}")

    # ── Test 4: validaciones ──────────────────────────────────────────────────
    print("\n── Test 4: validaciones de errores ─────────────────────────────────")
    try:
        Simulator(line, n_products=0)
        print("  ✘ Debería haber lanzado ValueError para n_products=0")
    except ValueError as e:
        print(f"  ✔ ValueError correcto para n_products=0")

    sim3 = Simulator(line, n_products=1)
    try:
        sim3.run(10)
        print("  ✘ Debería haber lanzado RuntimeError sin start()")
    except RuntimeError as e:
        print(f"  ✔ RuntimeError correcto sin start()")

    print("\n" + "═" * 70)
    print(" Pruebas completadas")
    print("═" * 70)