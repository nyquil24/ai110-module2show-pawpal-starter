# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

This version adds smarter scheduling features to PawPal+:

- Recurring tasks marked `daily` or `weekly` now automatically create a new task instance for the next occurrence when completed.
- The scheduler is due-date aware: only tasks due today or earlier are included in the current plan.
- Tasks are ordered by preferred time window, priority, and duration for better daily flow.
- Lightweight conflict warnings are generated when tasks overlap for the same pet or the same owner.
- Task filtering supports both completion status and pet-specific views.

## Testing PawPal+

### Run the tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Test | What it verifies |
|---|---|
| `test_filter_tasks_by_completed_status` | `filter_tasks(completed=...)` returns only tasks matching that status |
| `test_filter_tasks_by_pet_name` | `filter_tasks(pet_name=...)` isolates tasks belonging to a specific pet |
| `test_filter_tasks_by_completion_or_pet_wrapper` | The convenience wrapper `filter_tasks_by_completion_or_pet` delegates correctly |
| `test_mark_complete_creates_next_daily_task` | Completing a `recurrence="daily"` task spawns a new task due the next day |
| `test_build_daily_schedule_orders_tasks_by_time` | Tasks added out of order are scheduled morning → afternoon → no-pref → evening |
| `test_detect_conflicts_returns_warning_for_overlapping_plans` | Overlapping tasks across two pets sharing an owner produce a `WARNING` message |
| `test_build_schedule_excludes_next_day_task` | A task with a future `due_date` is not included in today's schedule |

### Confidence level

**★★★★☆ (4 / 5)**

The core behaviors — filtering, time-window sorting, recurring task generation, due-date gating, and conflict detection — are each covered by a dedicated test and all 7 pass. The gap keeping it from 5 stars: edge cases like back-to-back task packing (greedy skip behavior), tasks with no `pet_name`, and owner availability exhaustion are not yet tested.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
