"""
tests/test_reports.py — Pruebas unitarias para linprod/reports.py
"""

import os
import tempfile

import pytest

from linprod.model import Process, ProductionLine, Task
from linprod.simulator import Simulator
from linprod.reports import generate_report


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _run_demo_sim(n_products: int = 5) -> dict:
    """Línea de referencia con 3 procesos, n_products productos."""
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

    sim = Simulator(line, n_products=n_products)
    sim.start()
    sim.run()
    return sim.get_stats()


def _run_minimal_sim() -> dict:
    p1 = Process("P1", is_initial=True)
    p1.add_task(Task("T1", 1))
    p2 = Process("P2", is_final=True)
    p2.add_task(Task("T2", 2))
    line = ProductionLine()
    line.add_process(p1)
    line.add_process(p2)
    sim = Simulator(line, n_products=2)
    sim.start()
    sim.run()
    return sim.get_stats()


# ═══════════════════════════════════════════════════════════════════════════════
# Generación del archivo PDF
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateReport:
    def test_creates_pdf_file(self):
        stats = _run_minimal_sim()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "reporte.pdf")
            generate_report(stats, path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    def test_pdf_starts_with_pdf_magic_bytes(self):
        stats = _run_minimal_sim()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "reporte.pdf")
            generate_report(stats, path)
            with open(path, "rb") as f:
                header = f.read(4)
            assert header == b"%PDF"

    def test_demo_line_generates_pdf(self):
        stats = _run_demo_sim(3)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "demo.pdf")
            generate_report(stats, path)
            assert os.path.getsize(path) > 1024

    def test_many_products_generates_pdf(self):
        stats = _run_demo_sim(20)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "big.pdf")
            generate_report(stats, path)
            assert os.path.exists(path)

    def test_none_values_do_not_crash(self):
        """generate_report no debe fallar si stats tiene valores None opcionales."""
        stats = _run_minimal_sim()
        stats["bottleneck_task"] = None
        stats["bottleneck_process"] = None
        stats["worst_wait_task"] = None
        stats["worst_wait_process"] = None
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nones.pdf")
            generate_report(stats, path)
            assert os.path.exists(path)

    def test_bad_path_raises(self):
        stats = _run_minimal_sim()
        with pytest.raises(Exception):
            generate_report(stats, "/ruta/que/no/existe/reporte.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# Integridad de stats (los 7 ítems obligatorios del módulo 4)
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatsCompleteness:
    def setup_method(self, _):
        self.stats = _run_demo_sim(5)

    # Ítem 1
    def test_item1_first_completion_cycle(self):
        assert isinstance(self.stats["first_completion_cycle"], int)
        assert self.stats["first_completion_cycle"] > 0

    # Ítem 2
    def test_item2_last_completion_cycle(self):
        assert isinstance(self.stats["last_completion_cycle"], int)
        assert self.stats["last_completion_cycle"] >= self.stats["first_completion_cycle"]

    # Ítem 3
    def test_item3_avg_completion_time(self):
        avg = self.stats["avg_completion_time"]
        assert avg is not None
        assert avg > 0

    # Ítem 4
    def test_item4_bottleneck_identified(self):
        assert self.stats["bottleneck_task"] is not None
        assert self.stats["bottleneck_process"] is not None

    # Ítem 5
    def test_item5_avg_wait_to_start(self):
        assert self.stats["avg_wait_to_start"] is not None
        assert self.stats["avg_wait_to_start"] >= 0

    # Ítem 6
    def test_item6_worst_wait_task(self):
        assert self.stats["worst_wait_task"] is not None
        assert self.stats["worst_wait_process"] is not None
        assert self.stats["worst_wait_value"] >= 0

    # Ítem 7
    def test_item7_total_processing_time(self):
        assert isinstance(self.stats["total_processing_time"], (int, float))
        assert self.stats["total_processing_time"] > 0

    def test_task_stats_nonempty(self):
        assert isinstance(self.stats["task_stats"], list)
        assert len(self.stats["task_stats"]) > 0

    def test_product_stats_all_completed(self):
        for p in self.stats["product_stats"]:
            assert p["is_completed"] is True
            assert p["exit_time"] is not None

    def test_bottleneck_in_task_stats(self):
        task_names = [t["task_name"] for t in self.stats["task_stats"]]
        assert self.stats["bottleneck_task"] in task_names
