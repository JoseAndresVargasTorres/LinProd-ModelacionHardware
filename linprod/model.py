"""
model.py — Módulo 1: Modelo de Datos OOP
Proyecto LinProd | CE-5507 Modelación Hardware/Software Orientado a Objetos
Instituto Tecnológico de Costa Rica | I Semestre 2026

Este módulo contiene las clases centrales del dominio. No depende de ningún
otro módulo; los demás (simulador, GUI, reportería) importan desde aquí.
"""

from __future__ import annotations

from collections import deque
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Clase Product
# ═══════════════════════════════════════════════════════════════════════════════

class Product:
    """
    Representa un producto que recorre la línea de producción.

    Atributos
    ---------
    product_id : int
        Identificador único del producto.
    entry_time : int
        Ciclo en que el producto entra a la línea de producción.
    exit_time : int | None
        Ciclo en que el producto sale completamente de la línea (None si aún
        no ha terminado).
    task_history : list[dict]
        Historial de tiempos por tarea. Cada entrada es un diccionario con:
            - "task_name": str
            - "process_name": str
            - "start_cycle": int      (ciclo en que empezó a ser procesado)
            - "end_cycle": int        (ciclo en que terminó de ser procesado)
            - "wait_cycles": int      (ciclos que esperó en cola antes de entrar)
    """

    def __init__(self, product_id: int, entry_cycle: int):
        self.product_id: int = product_id
        self.entry_time: int = entry_cycle
        self.exit_time: Optional[int] = None
        self.task_history: list[dict] = []

    # ── Registro de eventos ────────────────────────────────────────────────────

    def record_task_start(self, task_name: str, process_name: str,
                          start_cycle: int, wait_cycles: int) -> None:
        """Registra que el producto comenzó a ser procesado en una tarea."""
        self.task_history.append({
            "task_name": task_name,
            "process_name": process_name,
            "start_cycle": start_cycle,
            "end_cycle": None,
            "wait_cycles": wait_cycles,
        })

    def record_task_end(self, end_cycle: int) -> None:
        """Registra que el producto terminó de ser procesado en la última tarea."""
        if self.task_history:
            self.task_history[-1]["end_cycle"] = end_cycle

    def mark_completed(self, exit_cycle: int) -> None:
        """Marca el producto como completamente procesado."""
        self.exit_time = exit_cycle

    # ── Propiedades calculadas ─────────────────────────────────────────────────

    @property
    def is_completed(self) -> bool:
        return self.exit_time is not None

    @property
    def total_time(self) -> Optional[int]:
        """Ciclos totales desde la entrada hasta la salida (None si no terminó)."""
        if self.exit_time is None:
            return None
        return self.exit_time - self.entry_time

    # ── Representación ─────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        status = f"salió en ciclo {self.exit_time}" if self.is_completed else "en proceso"
        return f"Product(id={self.product_id}, entrada={self.entry_time}, {status})"

    def snapshot(self) -> dict:
        """Retorna un diccionario con el estado actual del producto."""
        return {
            "product_id": self.product_id,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "is_completed": self.is_completed,
            "total_time": self.total_time,
            "task_history": list(self.task_history),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Clase Task
# ═══════════════════════════════════════════════════════════════════════════════

class Task:
    """
    Representa una máquina/tarea dentro de un proceso.

    Cada tarea puede procesar UN producto a la vez. Los productos que llegan
    mientras la tarea está ocupada se almacenan en una cola FIFO.

    Atributos
    ---------
    name : str
        Nombre descriptivo de la tarea.
    process_time : int
        Duración del procesamiento en ciclos (tiempo que tarda en atender
        un producto).
    busy : bool
        Indica si la tarea está actualmente procesando un producto.
    """

    def __init__(self, name: str, process_time: int):
        if process_time <= 0:
            raise ValueError(f"process_time debe ser > 0, se recibió {process_time!r}")
        self.name: str = name
        self.process_time: int = process_time

        # ── Estado interno ─────────────────────────────────────────────────────
        self.busy: bool = False
        self._current_product: Optional[Product] = None
        self._remaining_cycles: int = 0          # ciclos que le quedan al producto actual
        self._queue: deque[Product] = deque()    # cola FIFO de productos en espera
        self._queue_arrival_cycles: deque[int] = deque()  # ciclo de llegada de cada prod en cola

        # Referencia al proceso padre (se asigna cuando se añade a un Process)
        self.process: Optional["Process"] = None

        # Estadísticas internas (usadas por Módulo 4 vía Módulo 2)
        self._total_wait_cycles: int = 0
        self._products_processed: int = 0

    # ── Interfaz pública ───────────────────────────────────────────────────────

    def receive(self, product: Product, current_cycle: int) -> None:
        """
        Recibe un producto. Si la tarea está libre, lo procesa de inmediato;
        si está ocupada, lo encola.

        Parámetros
        ----------
        product : Product
            El producto que llega a esta tarea.
        current_cycle : int
            El ciclo actual de la simulación.
        """
        if not self.busy:
            self._start_processing(product, current_cycle)
        else:
            self._queue.append(product)
            self._queue_arrival_cycles.append(current_cycle)

    def tick(self, current_cycle: int) -> Optional[Product]:
        """
        Avanza UN ciclo de tiempo en esta tarea.

        Retorna el producto que terminó de ser procesado en este ciclo,
        o None si no terminó ningún producto.

        Parámetros
        ----------
        current_cycle : int
            El ciclo actual (usado para registrar tiempos en el producto).
        """
        if not self.busy:
            return None

        self._remaining_cycles -= 1

        if self._remaining_cycles == 0:
            # El producto terminó
            finished = self._current_product
            finished.record_task_end(current_cycle)
            self._products_processed += 1

            # Reiniciar estado
            self._current_product = None
            self.busy = False

            # Si hay productos esperando, tomar el siguiente
            if self._queue:
                next_product = self._queue.popleft()
                arrival_cycle = self._queue_arrival_cycles.popleft()
                wait = current_cycle - arrival_cycle
                self._total_wait_cycles += wait
                self._start_processing(next_product, current_cycle)

            return finished

        return None

    def is_done(self) -> bool:
        """True si no hay producto siendo procesado ni productos en cola."""
        return not self.busy and len(self._queue) == 0

    def queue_size(self) -> int:
        """Cantidad de productos esperando en la cola FIFO."""
        return len(self._queue)

    @property
    def current_product(self) -> Optional[Product]:
        """Producto que se está procesando actualmente (None si está libre)."""
        return self._current_product

    def reset(self) -> None:
        """
        Limpia completamente el estado de la tarea para poder reutilizarla
        en una nueva simulación sin recrear el objeto.
        """
        self.busy = False
        self._current_product = None
        self._remaining_cycles = 0
        self._queue.clear()
        self._queue_arrival_cycles.clear()
        self._total_wait_cycles = 0
        self._products_processed = 0

    def snapshot(self) -> dict:
        """
        Retorna un diccionario con el estado actual de la tarea.
        Usado por la pausa/foto del sistema (Módulos 2 y 3).
        """
        return {
            "task_name": self.name,
            "process_name": self.process.name if self.process else None,
            "process_time": self.process_time,
            "busy": self.busy,
            "current_product_id": (
                self._current_product.product_id if self._current_product else None
            ),
            "remaining_cycles": self._remaining_cycles,
            "queue_size": self.queue_size(),
            "queue_product_ids": [p.product_id for p in self._queue],
            "products_processed": self._products_processed,
            "avg_wait_cycles": (
                self._total_wait_cycles / self._products_processed
                if self._products_processed > 0 else 0.0
            ),
        }

    # ── Métodos privados ───────────────────────────────────────────────────────

    def _start_processing(self, product: Product, current_cycle: int) -> None:
        """Inicia el procesamiento de un producto (solo para uso interno)."""
        self.busy = True
        self._current_product = product
        self._remaining_cycles = self.process_time
        product.record_task_start(
            task_name=self.name,
            process_name=self.process.name if self.process else "?",
            start_cycle=current_cycle,
            wait_cycles=0,   # 0 porque entró directo (sin cola)
        )

    # ── Representación ─────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        q = self.queue_size()
        status = (
            f"procesando P{self._current_product.product_id} "
            f"({self._remaining_cycles} ciclos restantes)"
            if self.busy else "libre"
        )
        return f"Task({self.name!r}, t={self.process_time}, {status}, cola={q})"


# ═══════════════════════════════════════════════════════════════════════════════
# Clase Process
# ═══════════════════════════════════════════════════════════════════════════════

class Process:
    """
    Representa un proceso dentro de la línea de producción.

    Un proceso es un conjunto ORDENADO de tareas. Un producto recorre todas
    las tareas del proceso en orden antes de pasar al siguiente proceso.

    Atributos
    ---------
    name : str
        Nombre descriptivo del proceso.
    is_initial : bool
        True si es el proceso de entrada de la línea.
    is_final : bool
        True si es el proceso de salida de la línea.
    next_process : Process | None
        Referencia al proceso siguiente en la línea (None si es el final).
    """

    def __init__(self, name: str, is_initial: bool = False, is_final: bool = False):
        self.name: str = name
        self.is_initial: bool = is_initial
        self.is_final: bool = is_final
        self.next_process: Optional["Process"] = None

        self._tasks: list[Task] = []  # lista ordenada de tareas

    # ── Gestión de tareas ──────────────────────────────────────────────────────

    def add_task(self, task: Task) -> None:
        """
        Agrega una tarea al final de la lista de tareas del proceso.

        Parámetros
        ----------
        task : Task
            La tarea a agregar.
        """
        task.process = self   # establecer referencia al proceso padre
        self._tasks.append(task)

    @property
    def tasks(self) -> list[Task]:
        """Lista de tareas en orden de ejecución (solo lectura)."""
        return list(self._tasks)

    @property
    def task_count(self) -> int:
        return len(self._tasks)

    # ── Interfaz de simulación ─────────────────────────────────────────────────

    def receive(self, product: Product, current_cycle: int) -> None:
        """
        Recibe un producto en este proceso: lo envía a la primera tarea.

        Parámetros
        ----------
        product : Product
            El producto que entra al proceso.
        current_cycle : int
            El ciclo actual de la simulación.
        """
        if not self._tasks:
            raise RuntimeError(f"El proceso '{self.name}' no tiene tareas definidas.")
        self._tasks[0].receive(product, current_cycle)

    def tick(self, current_cycle: int) -> list[Product]:
        """
        Avanza UN ciclo en todas las tareas del proceso.

        Gestiona el movimiento interno de productos entre tareas cuando una
        tarea finaliza. Retorna la lista de productos que terminaron TODA la
        secuencia de tareas del proceso (listos para pasar al siguiente proceso).

        Parámetros
        ----------
        current_cycle : int
            El ciclo actual de la simulación.

        Retorna
        -------
        list[Product]
            Productos que terminaron el proceso completo en este ciclo.
        """
        completed_products: list[Product] = []

        for i, task in enumerate(self._tasks):
            finished = task.tick(current_cycle)
            if finished is not None:
                is_last_task = (i == len(self._tasks) - 1)
                if is_last_task:
                    # El producto terminó todo el proceso
                    completed_products.append(finished)
                else:
                    # Pasa a la siguiente tarea dentro del mismo proceso
                    self._tasks[i + 1].receive(finished, current_cycle)

        return completed_products

    def is_done(self) -> bool:
        """True si todas las tareas del proceso están inactivas y sin cola."""
        return all(task.is_done() for task in self._tasks)

    def reset(self) -> None:
        """Reinicia todas las tareas del proceso para una nueva simulación."""
        for task in self._tasks:
            task.reset()

    def snapshot(self) -> dict:
        """
        Retorna un diccionario con el estado completo del proceso y sus tareas.
        """
        return {
            "process_name": self.name,
            "is_initial": self.is_initial,
            "is_final": self.is_final,
            "task_count": self.task_count,
            "is_done": self.is_done(),
            "next_process": self.next_process.name if self.next_process else None,
            "tasks": [task.snapshot() for task in self._tasks],
        }

    # ── Representación ─────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        flags = []
        if self.is_initial:
            flags.append("INICIAL")
        if self.is_final:
            flags.append("FINAL")
        tag = f" [{', '.join(flags)}]" if flags else ""
        return f"Process({self.name!r}{tag}, tareas={self.task_count})"


# ═══════════════════════════════════════════════════════════════════════════════
# Clase ProductionLine
# ═══════════════════════════════════════════════════════════════════════════════

class ProductionLine:
    """
    Representa la línea de producción completa: una cadena ordenada de procesos.

    Garantiza que exista exactamente un proceso inicial y uno final, y que la
    cadena de procesos sea contigua (sin huecos).
    """

    def __init__(self):
        self._processes: list[Process] = []

    # ── Gestión de procesos ────────────────────────────────────────────────────

    def add_process(self, process: Process) -> None:
        """
        Agrega un proceso al final de la línea.

        El proceso se encadena automáticamente al anterior mediante la
        referencia next_process.

        Parámetros
        ----------
        process : Process
            El proceso a agregar.
        """
        if self._processes:
            self._processes[-1].next_process = process
        self._processes.append(process)

    @property
    def processes(self) -> list[Process]:
        """Lista de procesos en orden (solo lectura)."""
        return list(self._processes)

    @property
    def process_count(self) -> int:
        return len(self._processes)

    @property
    def initial_process(self) -> Optional[Process]:
        """Retorna el proceso marcado como inicial, o None si no existe."""
        for p in self._processes:
            if p.is_initial:
                return p
        return None

    @property
    def final_process(self) -> Optional[Process]:
        """Retorna el proceso marcado como final, o None si no existe."""
        for p in self._processes:
            if p.is_final:
                return p
        return None

    # ── Validación ─────────────────────────────────────────────────────────────

    def validate(self) -> None:
        """
        Valida la integridad de la línea de producción.

        Lanza ValueError si:
        - No hay procesos definidos.
        - No existe exactamente un proceso inicial.
        - No existe exactamente un proceso final.
        - Algún proceso no tiene tareas.
        - Alguna tarea tiene process_time <= 0 (ya se valida en Task.__init__,
          pero se verifica aquí también por completitud).

        Si no lanza excepción, la línea es válida para ser simulada.
        """
        if not self._processes:
            raise ValueError("La línea de producción no tiene procesos definidos.")

        initials = [p for p in self._processes if p.is_initial]
        finals   = [p for p in self._processes if p.is_final]

        if len(initials) != 1:
            raise ValueError(
                f"Debe existir exactamente 1 proceso inicial, "
                f"se encontraron {len(initials)}: {[p.name for p in initials]}"
            )

        if len(finals) != 1:
            raise ValueError(
                f"Debe existir exactamente 1 proceso final, "
                f"se encontraron {len(finals)}: {[p.name for p in finals]}"
            )

        for process in self._processes:
            if process.task_count == 0:
                raise ValueError(
                    f"El proceso '{process.name}' no tiene tareas. "
                    "Cada proceso debe tener al menos una tarea."
                )

    def reset(self) -> None:
        """Reinicia todos los procesos para una nueva simulación."""
        for process in self._processes:
            process.reset()

    def snapshot(self) -> dict:
        """Retorna el estado completo de la línea de producción."""
        return {
            "process_count": self.process_count,
            "initial_process": self.initial_process.name if self.initial_process else None,
            "final_process": self.final_process.name if self.final_process else None,
            "processes": [p.snapshot() for p in self._processes],
        }

    def __repr__(self) -> str:
        names = " → ".join(p.name for p in self._processes)
        return f"ProductionLine([{names}])"


# ═══════════════════════════════════════════════════════════════════════════════
# Prueba de aislamiento (ejecutar directamente: python model.py)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ── Construir una línea de ejemplo ─────────────────────────────────────────
    # Proceso 1 (inicial): 2 tareas
    p1 = Process("Ensamblado", is_initial=True)
    p1.add_task(Task("Colocar chasis",    process_time=3))
    p1.add_task(Task("Instalar motor",    process_time=2))

    # Proceso 2: 1 tarea
    p2 = Process("Pintura")
    p2.add_task(Task("Aplicar pintura",   process_time=4))

    # Proceso 3 (final): 2 tareas
    p3 = Process("Control de calidad", is_final=True)
    p3.add_task(Task("Inspección visual", process_time=1))
    p3.add_task(Task("Prueba funcional",  process_time=2))

    # ── Construir la línea ──────────────────────────────────────────────────────
    line = ProductionLine()
    line.add_process(p1)
    line.add_process(p2)
    line.add_process(p3)

    # ── Validar ────────────────────────────────────────────────────────────────
    try:
        line.validate()
        print("✔ Línea de producción válida")
    except ValueError as e:
        print(f"✘ Error de validación: {e}")

    # ── Mostrar estructura ──────────────────────────────────────────────────────
    print("\n── Estructura de la línea ─────────────────────────────────────")
    for proc in line.processes:
        print(f"  {proc}")
        for task in proc.tasks:
            print(f"      └─ {task}")

    # ── Simular manualmente 2 ciclos (prueba de aislamiento básica) ────────────
    print("\n── Simulación manual (2 productos, 10 ciclos) ─────────────────")
    products = [Product(i, entry_cycle=0) for i in range(1, 3)]
    for prod in products:
        line.initial_process.receive(prod, current_cycle=0)

    for cycle in range(1, 11):
        for i, proc in enumerate(line.processes):
            finished = proc.tick(current_cycle=cycle)
            for prod in finished:
                if proc.is_final:
                    prod.mark_completed(cycle)
                    print(f"  Ciclo {cycle:>2}: Producto {prod.product_id} ✔ completado "
                          f"(tiempo total: {prod.total_time} ciclos)")
                elif proc.next_process:
                    proc.next_process.receive(prod, cycle)

    print("\n── Snapshot final de la línea ─────────────────────────────────")
    import json
    print(json.dumps(line.snapshot(), indent=2, ensure_ascii=False))