"""
tests/test_model.py — Pruebas unitarias para linprod/model.py
"""

import pytest
from collections import deque

from linprod.model import Product, Task, Process, ProductionLine


# ═══════════════════════════════════════════════════════════════════════════════
# Product
# ═══════════════════════════════════════════════════════════════════════════════

class TestProduct:
    def test_initial_state(self):
        p = Product(product_id=1, entry_cycle=0)
        assert p.product_id == 1
        assert p.entry_time == 0
        assert p.exit_time is None
        assert p.is_completed is False
        assert p.total_time is None
        assert p.task_history == []

    def test_record_task_start_and_end(self):
        p = Product(1, 0)
        p.record_task_start("T1", "Proc1", start_cycle=2, wait_cycles=1)
        assert len(p.task_history) == 1
        entry = p.task_history[0]
        assert entry["task_name"] == "T1"
        assert entry["process_name"] == "Proc1"
        assert entry["start_cycle"] == 2
        assert entry["wait_cycles"] == 1
        assert entry["end_cycle"] is None

        p.record_task_end(end_cycle=5)
        assert p.task_history[0]["end_cycle"] == 5

    def test_mark_completed(self):
        p = Product(1, 3)
        p.mark_completed(10)
        assert p.exit_time == 10
        assert p.is_completed is True
        assert p.total_time == 7

    def test_snapshot_keys(self):
        p = Product(2, 0)
        snap = p.snapshot()
        for key in ("product_id", "entry_time", "exit_time", "is_completed",
                    "total_time", "task_history"):
            assert key in snap


# ═══════════════════════════════════════════════════════════════════════════════
# Task
# ═══════════════════════════════════════════════════════════════════════════════

class TestTask:
    def test_invalid_process_time(self):
        with pytest.raises(ValueError):
            Task("T", process_time=0)
        with pytest.raises(ValueError):
            Task("T", process_time=-1)

    def test_receive_when_free(self):
        task = Task("T1", process_time=3)
        p = Product(1, 0)
        task.receive(p, current_cycle=1)
        assert task.busy is True
        assert task.current_product is p
        assert task.queue_size() == 0

    def test_receive_when_busy_goes_to_queue(self):
        task = Task("T1", process_time=3)
        p1 = Product(1, 0)
        p2 = Product(2, 0)
        task.receive(p1, 1)
        task.receive(p2, 1)
        assert task.queue_size() == 1

    def test_tick_counts_down_and_finishes(self):
        task = Task("T1", process_time=2)
        p = Product(1, 0)
        task.receive(p, current_cycle=1)

        result_c1 = task.tick(current_cycle=1)
        assert result_c1 is None         # still processing
        assert task.busy is True

        result_c2 = task.tick(current_cycle=2)
        assert result_c2 is p            # done
        assert task.busy is False
        assert p.task_history[-1]["end_cycle"] == 2

    def test_tick_starts_next_from_queue(self):
        task = Task("T1", process_time=1)
        p1 = Product(1, 0)
        p2 = Product(2, 0)
        task.receive(p1, 0)
        task.receive(p2, 0)
        task.tick(1)                     # p1 done → p2 starts
        assert task.busy is True
        assert task.current_product is p2

    def test_is_done(self):
        task = Task("T", process_time=1)
        assert task.is_done() is True
        p = Product(1, 0)
        task.receive(p, 0)
        assert task.is_done() is False
        task.tick(1)
        assert task.is_done() is True

    def test_reset_clears_state(self):
        task = Task("T", process_time=2)
        p = Product(1, 0)
        task.receive(p, 0)
        task.tick(1)
        task.reset()
        assert task.busy is False
        assert task.current_product is None
        assert task.queue_size() == 0

    def test_snapshot_keys(self):
        task = Task("T", process_time=3)
        snap = task.snapshot()
        for key in ("task_name", "process_time", "busy", "queue_size",
                    "products_processed", "avg_wait_cycles"):
            assert key in snap


# ═══════════════════════════════════════════════════════════════════════════════
# Process
# ═══════════════════════════════════════════════════════════════════════════════

class TestProcess:
    def _make_process(self):
        proc = Process("P1", is_initial=True)
        proc.add_task(Task("T1", 1))
        proc.add_task(Task("T2", 2))
        return proc

    def test_add_task_sets_parent(self):
        proc = Process("P")
        t = Task("T", 1)
        proc.add_task(t)
        assert t.process is proc

    def test_task_count(self):
        proc = self._make_process()
        assert proc.task_count == 2

    def test_receive_goes_to_first_task(self):
        proc = self._make_process()
        p = Product(1, 0)
        proc.receive(p, 0)
        assert proc.tasks[0].busy is True
        assert proc.tasks[0].current_product is p

    def test_receive_raises_if_no_tasks(self):
        proc = Process("Empty")
        p = Product(1, 0)
        with pytest.raises(RuntimeError):
            proc.receive(p, 0)

    def test_tick_moves_product_to_next_task(self):
        proc = Process("P", is_initial=True)
        proc.add_task(Task("T1", 1))
        proc.add_task(Task("T2", 2))

        p = Product(1, 0)
        proc.receive(p, 0)

        # Process.tick() iterates forward: when T1 finishes at cycle 1 and
        # delivers to T2, T2 is ticked in the same pass (consuming 1 of its 2
        # cycles). The simulator avoids this by ticking in reverse order, but
        # Process.tick() itself uses forward order.
        completed = proc.tick(1)        # T1 done → T2 receives + ticked once
        assert completed == []          # T2 still has 1 cycle remaining
        assert proc.tasks[1].busy is True

        completed = proc.tick(2)        # T2 tick 2 → p exits process
        assert p in completed

    def test_is_done_when_all_tasks_idle(self):
        proc = Process("P")
        proc.add_task(Task("T", 1))
        assert proc.is_done() is True

    def test_reset(self):
        proc = Process("P")
        proc.add_task(Task("T", 1))
        p = Product(1, 0)
        proc.receive(p, 0)
        proc.reset()
        assert proc.tasks[0].busy is False

    def test_snapshot_keys(self):
        proc = Process("P")
        proc.add_task(Task("T", 1))
        snap = proc.snapshot()
        for key in ("process_name", "is_initial", "is_final", "task_count",
                    "is_done", "tasks"):
            assert key in snap


# ═══════════════════════════════════════════════════════════════════════════════
# ProductionLine
# ═══════════════════════════════════════════════════════════════════════════════

class TestProductionLine:
    def _make_valid_line(self):
        p1 = Process("Inicio", is_initial=True)
        p1.add_task(Task("T1", 1))
        p2 = Process("Fin", is_final=True)
        p2.add_task(Task("T2", 2))
        line = ProductionLine()
        line.add_process(p1)
        line.add_process(p2)
        return line

    def test_add_process_links_next(self):
        line = self._make_valid_line()
        procs = line.processes
        assert procs[0].next_process is procs[1]
        assert procs[1].next_process is None

    def test_validate_ok(self):
        line = self._make_valid_line()
        line.validate()   # must not raise

    def test_validate_no_processes(self):
        line = ProductionLine()
        with pytest.raises(ValueError, match="no tiene procesos"):
            line.validate()

    def test_validate_no_initial(self):
        line = ProductionLine()
        p = Process("Solo", is_final=True)
        p.add_task(Task("T", 1))
        line.add_process(p)
        with pytest.raises(ValueError, match="inicial"):
            line.validate()

    def test_validate_no_final(self):
        line = ProductionLine()
        p = Process("Solo", is_initial=True)
        p.add_task(Task("T", 1))
        line.add_process(p)
        with pytest.raises(ValueError, match="final"):
            line.validate()

    def test_validate_process_without_tasks(self):
        line = ProductionLine()
        p1 = Process("I", is_initial=True)
        p1.add_task(Task("T", 1))
        p2 = Process("F", is_final=True)
        line.add_process(p1)
        line.add_process(p2)
        with pytest.raises(ValueError, match="no tiene tareas"):
            line.validate()

    def test_initial_and_final_properties(self):
        line = self._make_valid_line()
        assert line.initial_process.name == "Inicio"
        assert line.final_process.name == "Fin"

    def test_reset_propagates(self):
        line = self._make_valid_line()
        p = Product(1, 0)
        line.initial_process.receive(p, 0)
        line.reset()
        assert line.initial_process.tasks[0].busy is False

    def test_snapshot_keys(self):
        line = self._make_valid_line()
        snap = line.snapshot()
        assert "processes" in snap
        assert snap["process_count"] == 2
