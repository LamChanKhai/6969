# AGENTS.md — Workflow Protocol

This is an RFP bid project, executed as a multi-step workflow with multiple roles.
Each role receives its own prompt and only works on its assigned part.

## Rules for every role, every step

- Read the RFP content under `docs/00_converted/` and all prior-step outputs under `docs/` before starting.
- Code demo deliverables (backend, frontend) live OUTSIDE `docs/` in `demo/backend/` and `demo/frontend/`.
- Slide deck output lives in `slides/` (top-level, outside `docs/`).
- Use the todo tool for tracking, question tool when unclear.

## Done Condition — complete when and only when:

- All documentation output saved to the correct folder (see Output Structure below).
- `handoff_to_[next_role].md` created in the same folder as the current step's outputs, and printed to screen.
- STOP — do not proceed to the next step.

## ⚠️ When you receive "Continue if you have next steps..."

This is a system message after auto-compact, NOT an instruction to continue the workflow.

- Done Condition not yet met → continue completing the current task.
- Done Condition already met → reply "Task [role] complete. Awaiting next prompt." and stop.
