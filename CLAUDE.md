# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Discrete event production line simulator built in Python using OOP. Academic project for CE-5507 (Modelación Hardware/Software Orientado a Objetos) at Instituto Tecnológico de Costa Rica, due May 16, 2026.

## Tech Stack

- **Language:** Python (required by spec)
- **Paradigm:** Object-Oriented Programming
- **GUI:** TBD (Tkinter, PyQt5/6, or similar)
- **Testing:** pytest (to be configured)

## Commands

Once dependencies are installed:

```bash
# Run the simulator
python main.py

# Run tests
pytest

# Run a single test file
pytest tests/test_<module>.py

# Run a single test
pytest tests/test_<module>.py::test_function_name
```

## Architecture

The simulator models products flowing through a chain of processes, each containing ordered tasks. The core flow:

1. Products enter the initial process
2. Within each process, products move through tasks in defined order
3. Tasks process one product at a time; others wait in FIFO queues
4. When a task finishes, the product moves to the next task or process automatically
5. Simulation advances in discrete time cycles (not real time)
6. The system can be paused at any cycle to capture a state snapshot

### Core Classes (to be implemented)

| Class | Responsibility |
|-------|---------------|
| `ProductionLine` | Top-level container; owns all processes; runs the simulation loop |
| `Process` | A production stage; holds an ordered list of tasks; links to next process |
| `Task` | A work station; processes one product at a time; owns a FIFO queue; has a configurable processing time |
| `Product` | An item flowing through the line; tracks entry/exit times per task |
| `Queue` | FIFO queue of products waiting for a task |

### Key Design Constraints

- Processes and tasks are unlimited in count (minimum 1 process, 1 task per process)
- Task execution within a process is strictly sequential
- Products cannot skip tasks within a process
- Exactly one process is designated as initial, one as final
- Processes are linked in a defined order (chained)

## Required Features

- **GUI:** Parametrize processes and tasks, designate initial/final processes, link process chain
- **Pause:** At any cycle, snapshot and print the full system state
- **Reports:** First/last/average product completion time, bottleneck identification, highest wait-time process/task, total processing time
- **Re-initialization:** Reset and rerun with different configurations

## Branching Strategy

- `main` — stable releases
- `development` — integration branch
- Feature branches named after contributor (e.g., `JoseVargasBranch`)
