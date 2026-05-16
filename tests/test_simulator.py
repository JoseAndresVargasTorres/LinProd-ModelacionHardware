"""
tests/test_simulator.py — Pruebas unitarias para linprod/simulator.py
"""

import pytest

from linprod.model import Process, ProductionLine, Task
from linprod.simulator import Simulator


# ─── Helpers de construcción ─────────────────────────────────────────────────

def _make_reference_line():
    """Línea de referencia del enunciado (guía Módulo 2):
    Ensamblado(Colocar chasis t=3, Instalar motor t=2) →
    Pintura(Aplicar pintura t=4) →
    Control de calidad(Inspección visual t=1, Prueba funcional t=2)
    """
    p1 = Process("Ensamblado", is_initial=True)
    p1.add_task(Task("Colocar chasis", 3))
    p1.add_task(Task("Instalar motor", 2))

    p2 = Process("Pintura")
    p2.add_task(Task("Aplicar pintura", 4))

    p3 = Process("Control de calidad", is_final=True)
    p3.add_task(Task("Inspeccion visual", 1))
    p3.add_task(Task("Prueba funcional", 2))

    line = ProductionLine()
    line.add_process(p1)
    line.add_process(p2)
    line.add_process(p3)
    return line


def _make_simple_line():
    """Línea simple de 2 procesos para pruebas rápidas."""
    p1 = Process("P1", is_initial=True)
    p1.add_task(Task("T1", 2))
    p2 = Process("P2", is_final=True)
    p2.add_task(Task("T2", 3))
    line = ProductionLine()
    line.add_process(p1)
    line.add_process(p2)
    return line


# ═══════════════════════════════════════════════════════════════════════════════
# Validaciones de construcción
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimulatorConstruction:
    def test_n_products_must_be_positive(self):
        line = _make_simple_line()
        with pytest.raises(ValueError):
            Simulator(line, n_products=0)
        with pytest.raises(ValueError):
            Simulator(line, n_products=-1)

    def test_run_before_start_raises(self):
        sim = Simulator(_make_simple_line(), n_products=2)
        with pytest.raises(RuntimeError):
            sim.run(10)

    def test_step_before_start_raises(self):
        sim = Simulator(_make_simple_line(), n_products=2)
        with pytest.raises(RuntimeError):
            sim.step()

    def test_resume_when_not_paused_raises(self):
        sim = Simulator(_make_simple_line(), n_products=1)
        sim.start()
        with pytest.raises(RuntimeError):
            sim.resume()

    def test_invalid_line_raises_on_start(self):
        line = ProductionLine()
        p = Process("Solo")
        p.add_task(Task("T", 1))
        line.add_process(p)
        sim = Simulator(line, n_products=1)
        with pytest.raises(ValueError):
            sim.start()


# ═══════════════════════════════════════════════════════════════════════════════
# Resultado de referencia del enunciado (Módulo 2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestReferenceResults:
    def test_3_products_reference_values(self):
        """Pipeline real: cada ciclo de procesamiento cuesta exactamente 1 ciclo."""
        line = _make_reference_line()
        sim = Simulator(line, n_products=3)
        sim.start()
        sim.run()   # sin args — debe terminar solo

        stats = sim.get_stats()
        by_id = {p["product_id"]: p for p in stats["product_stats"]}

        assert by_id[1]["exit_time"] == 12
        assert by_id[2]["exit_time"] == 16
        assert by_id[3]["exit_time"] == 20

        assert by_id[1]["total_time"] == 12
        assert by_id[2]["total_time"] == 16
        assert by_id[3]["total_time"] == 20

    def test_all_products_completed(self):
        line = _make_reference_line()
        sim = Simulator(line, n_products=3)
        sim.start()
        sim.run()
        assert sim.is_done is True
        assert len(sim.completed_products) == 3

    def test_stats_keys_present(self):
        line = _make_reference_line()
        sim = Simulator(line, n_products=2)
        sim.start()
        sim.run()
        stats = sim.get_stats()
        required = [
            "total_cycles_run", "products_total", "products_completed",
            "first_completion_cycle", "last_completion_cycle",
            "avg_completion_time", "total_processing_time",
            "bottleneck_task", "bottleneck_process",
            "avg_wait_to_start", "worst_wait_task", "worst_wait_process",
            "worst_wait_value", "task_stats", "product_stats",
        ]
        for key in required:
            assert key in stats, f"Falta clave: {key}"

    def test_first_completion_before_last(self):
        line = _make_reference_line()
        sim = Simulator(line, n_products=3)
        sim.start()
        sim.run()
        stats = sim.get_stats()
        assert stats["first_completion_cycle"] <= stats["last_completion_cycle"]


# ═══════════════════════════════════════════════════════════════════════════════
# Control de flujo: pause / resume / step / reset
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimulatorControl:
    def test_pause_and_resume(self):
        sim = Simulator(_make_simple_line(), n_products=2)
        sim.start()
        sim.run(5)
        snap = sim.pause()
        assert sim.is_paused is True
        assert snap["cycle"] == 5
        sim.resume()
        assert sim.is_paused is False

    def test_step_advances_one_cycle(self):
        sim = Simulator(_make_simple_line(), n_products=1)
        sim.start()
        assert sim.current_cycle == 0
        sim.step()
        assert sim.current_cycle == 1
        sim.step()
        assert sim.current_cycle == 2

    def test_step_paused_raises(self):
        sim = Simulator(_make_simple_line(), n_products=2)
        sim.start()
        sim.run(3)
        sim.pause()
        with pytest.raises(RuntimeError):
            sim.step()

    def test_reset_restores_initial_state(self):
        sim = Simulator(_make_reference_line(), n_products=2)
        sim.start()
        sim.run()
        sim.reset()
        assert sim.current_cycle == 0
        assert sim.is_started is False
        assert sim.is_done is False
        assert len(sim.completed_products) == 0

    def test_run_without_args_completes(self):
        sim = Simulator(_make_simple_line(), n_products=1)
        sim.start()
        sim.run()   # sin n_cycles
        assert sim.is_done is True

    def test_is_done_only_when_all_complete(self):
        sim = Simulator(_make_simple_line(), n_products=3)
        sim.start()
        assert sim.is_done is False
        sim.run()
        assert sim.is_done is True


# ═══════════════════════════════════════════════════════════════════════════════
# Determinismo
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeterminism:
    def test_same_results_after_reset(self):
        line = _make_reference_line()
        sim = Simulator(line, n_products=3)

        sim.start()
        sim.run()
        stats_a = sim.get_stats()

        sim.reset()
        sim.start()
        sim.run()
        stats_b = sim.get_stats()

        assert stats_a["last_completion_cycle"] == stats_b["last_completion_cycle"]
        assert stats_a["total_cycles_run"] == stats_b["total_cycles_run"]

        for a, b in zip(stats_a["product_stats"], stats_b["product_stats"]):
            assert a["exit_time"] == b["exit_time"]


# ═══════════════════════════════════════════════════════════════════════════════
# Semántica de pipeline (invariantes críticos)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPipelineSemantics:
    def test_inter_process_transfer_deferred_one_cycle(self):
        """
        Un producto que termina el proceso N en el ciclo K debe entrar
        al proceso N+1 en el ciclo K+1, NO en K.
        """
        p1 = Process("P1", is_initial=True)
        p1.add_task(Task("T1", 1))   # termina en ciclo 1

        p2 = Process("P2", is_final=True)
        p2.add_task(Task("T2", 1))   # debe empezar en ciclo 2 como mínimo

        line = ProductionLine()
        line.add_process(p1)
        line.add_process(p2)

        sim = Simulator(line, n_products=1)
        sim.start()
        sim.run()

        stats = sim.get_stats()
        # T1 termina ciclo 1, transferencia diferida → T2 empieza ciclo 2 → sale ciclo 2
        assert stats["product_stats"][0]["exit_time"] >= 2

    def test_reverse_tick_order_within_process(self):
        """
        Un producto que pasa de T1 a T2 en el mismo ciclo no debe
        ser ticked nuevamente por T2 en ese mismo ciclo.
        """
        p1 = Process("P1", is_initial=True)
        p1.add_task(Task("T1", 1))  # termina ciclo 1 → entrega a T2
        p1.add_task(Task("T2", 1))  # debe completar en ciclo 2 (no ciclo 1)

        p2 = Process("P2", is_final=True)
        p2.add_task(Task("T3", 1))

        line = ProductionLine()
        line.add_process(p1)
        line.add_process(p2)

        sim = Simulator(line, n_products=1)
        sim.start()
        sim.run()

        stats = sim.get_stats()
        p = stats["product_stats"][0]
        t1_end = next(e["end_cycle"] for e in p["task_history"]
                      if e["task_name"] == "T1")
        t2_end = next(e["end_cycle"] for e in p["task_history"]
                      if e["task_name"] == "T2")
        # T2 debe terminar DESPUÉS de T1 (al menos 1 ciclo más)
        assert t2_end > t1_end

    def test_snapshot_cycle_matches_current_cycle(self):
        sim = Simulator(_make_simple_line(), n_products=2)
        sim.start()
        sim.run(7)
        snap = sim.snapshot()
        assert snap["cycle"] == sim.current_cycle

    def test_on_pause_callback_called(self):
        received = []
        sim = Simulator(_make_simple_line(), n_products=2,
                        on_pause=lambda s: received.append(s))
        sim.start()
        sim.run(3)
        sim.pause()
        assert len(received) == 1
        assert received[0]["cycle"] == 3
