# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

LinProd is a discrete-event production-line simulator (Proyecto 2, CE-5507 — Modelación Hardware/Software OO, TEC, I Semestre 2026). It models products flowing through a series of ordered processes, each composed of sequential tasks with FIFO queues.

## Running the code

```bash
# Run the built-in self-test for the data model (Module 1)
python3 linprod/model.py

# Run the built-in self-test for the simulator (Module 2)
python3 linprod/simulator.py

# Run the GUI (Module 3)
python3 -m linprod.app

# Run tests
python3 -m pytest tests/
python3 -m pytest tests/test_model.py   # single test file
```

Dependencies: `reportlab` (only non-stdlib dependency, confirmed installed). `python3-tk` required for the GUI (`sudo apt-get install python3-tk`).

## Architecture

The project is divided into four modules with a strict one-way dependency chain:

```
model.py  ←  simulator.py  ←  app.py
                          ←  reports.py
```

**Module 1 — `linprod/model.py`** (complete)  
Core OOP domain: `Product` → `Task` → `Process` → `ProductionLine`.  
- A `ProductionLine` is an ordered chain of `Process` objects linked via `next_process`.  
- A `Process` holds an ordered list of `Task` objects; products traverse them sequentially.  
- A `Task` processes one product at a time; arrivals during processing queue in a FIFO `deque`. Two parallel deques track products and their arrival cycles (`_queue` / `_queue_arrival_cycles`).  
- `ProductionLine.validate()` enforces exactly one `is_initial` and one `is_final` process, with at least one task each.  
- Every object exposes a `snapshot() → dict` for state inspection and a `reset()` to reuse without reconstruction.

**Module 2 — `linprod/simulator.py`** (complete)  
`Simulator` wraps a `ProductionLine` and drives discrete-event time.  
- `start()` injects all `n_products` into the initial process at cycle 0.  
- `run(n)` / `step()` advance time; `pause()` / `resume()` control flow.  
- `get_stats()` returns final metrics consumed by Module 4 (see interface below).  
- `get_stats()` returns final metrics consumed by Module 4 (see interface below).
- Critical invariant: **real pipeline semantics** at two levels:
  - *Between processes*: a product finishing process N in cycle K is deferred via `_pending_inter_transfers` and enters process N+1 at the start of cycle K+1.
  - *Within a process*: tasks are ticked in **reverse order** (last → first) so a product received by an earlier task doesn't consume simulator time in the same cycle it was handed off.
- Reference values for 3 products on the standard line: P1=12, P2=16, P3=20.

**Module 3 — `linprod/app.py`** (complete)  
Tkinter GUI with dark theme (`LinProdApp` subclasses `tk.Tk`). Two-column layout: config panel (left) + live simulation view (right). Custom widgets: `ModernButton` (Label-based), `ModernEntry`, `Card`.

Task widget keys follow the pattern `"{process_name}::{task_name}"` stored in `self._task_widgets`. These are built once at sim start via `_build_sim_view()` and updated each tick via `_refresh_ui(snapshot)`.

Task addition targets are resolved in priority order: `_pending_process` > `_edit_target` > last confirmed process in `_line`.

The GUI timer loop uses `self.after(ms, self._tick)` in auto mode; step mode calls `sim.step()` directly on button click.

**Module 4 — `linprod/reports.py`** (stub — to implement)  
PDF report via `reportlab`. Sole input is `Simulator.get_stats()`. Must not import `app.py` or `tkinter`. Implementation guide is in `docs/guia_modulo4_reportes.tex` / `.pdf`.

### `get_stats()` return dict (Module 4 interface contract)

```python
{
    "total_cycles_run": int,
    "products_total": int,
    "products_completed": int,
    "first_completion_cycle": int | None,
    "last_completion_cycle": int | None,
    "avg_completion_time": float,
    "total_processing_time": int,
    "bottleneck_task": str | None,
    "bottleneck_process": str | None,
    "task_stats": [               # one entry per task, in process order
        {
            "task_name": str,
            "process_name": str,
            "process_time": int,
            "busy": bool,
            "current_product_id": int | None,
            "remaining_cycles": int,
            "queue_size": int,
            "queue_product_ids": list[int],
            "products_processed": int,
            "avg_wait_cycles": float,
        },
        ...
    ],
    "product_stats": [            # one entry per product (Product.snapshot())
        {
            "product_id": int,
            "entry_time": int,
            "exit_time": int | None,
            "is_completed": bool,
            "total_time": int | None,
            "task_history": [
                {
                    "task_name": str,
                    "process_name": str,
                    "start_cycle": int,
                    "end_cycle": int | None,
                    "wait_cycles": int,
                },
                ...
            ],
        },
        ...
    ],
    "avg_wait_to_start": float,
    "worst_wait_task": str | None,
    "worst_wait_process": str | None,
    "worst_wait_value": float,
}
```

## Key invariants to preserve

- `Task.process_time` must be `> 0`; enforced in `__init__`.
- Exactly one `is_initial` and one `is_final` process per `ProductionLine`.
- `Simulator.reset()` must restore deterministic behavior: same line + same `n_products` must produce identical results on repeated runs.
- The reverse-tick order inside `_advance_one_cycle` is intentional — do not change it without understanding pipeline semantics.
- `reports.py` must only consume `get_stats()` — it must not reach into model or simulator internals directly.

## Current status

| File | Status |
|------|--------|
| `linprod/model.py` | Complete |
| `linprod/simulator.py` | Complete |
| `linprod/app.py` | Complete |
| `linprod/reports.py` | Stub (1 line) — to implement |
| `tests/test_model.py` | Empty stub |
| `tests/test_simulator.py` | Empty stub |
| `tests/test_reports.py` | Empty stub |

## Docs folder

- `docs/guia_modulo4_reportes.tex` / `.pdf` — implementation guide for Module 4 (required PDF sections, reportlab API examples, `get_stats()` schema).
- `docs/guia_modulo3_GUI.tex` — implementation guide for Module 3 (already complete).
- `docs/diagrama_clases.drawio` — class diagram source.
- `docs/Proyecto2_LinProd.tex` — full project spec.
