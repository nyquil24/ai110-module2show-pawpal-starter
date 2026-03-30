from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

PRIORITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3}

# Maps preferred_time strings to a sort order (earlier = scheduled first).
# Tasks with no preferred_time return 2 (between afternoon=1 and evening=3)
# so explicitly windowed tasks always group before unanchored ones.
TIME_WINDOW_ORDER = {"morning": 0, "afternoon": 1, "evening": 3}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"
    pet_name: Optional[str] = None
    preferred_time: Optional[str] = None   # "morning" | "afternoon" | "evening"
    deadline_minutes: Optional[int] = None
    due_date: Optional[date] = None
    notes: str = ""
    completed: bool = False
    recurrence: Optional[str] = None       # "daily" | "weekly" | None

    def __post_init__(self) -> None:
        self.priority = self.priority.lower()
        if self.priority not in PRIORITY_WEIGHTS:
            self.priority = "medium"
        if self.preferred_time is not None:
            self.preferred_time = self.preferred_time.lower()
            if self.preferred_time not in TIME_WINDOW_ORDER:
                self.preferred_time = None

    @property
    def priority_weight(self) -> int:
        return PRIORITY_WEIGHTS[self.priority]

    @property
    def time_order(self) -> int:
        """Numeric sort key for preferred_time; no preference (2) sorts after afternoon (1) but before evening (3)."""
        return TIME_WINDOW_ORDER.get(self.preferred_time, 2)

    def is_due(self, today: Optional[date] = None) -> bool:
        """Return True if the task is due today or earlier."""
        today = today or date.today()
        return self.due_date is None or self.due_date <= today

    def mark_complete(self, today: Optional[date] = None) -> Optional["Task"]:
        """Mark the task complete and create the next recurring occurrence.

        If the task is recurring, this returns a fresh Task instance scheduled
        for the next due date. Non-recurring tasks simply return None.
        """
        self.completed = True
        today = today or date.today()

        if self.recurrence == "daily":
            next_due = today + timedelta(days=1)
        elif self.recurrence == "weekly":
            next_due = today + timedelta(days=7)
        else:
            return None

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            pet_name=self.pet_name,
            preferred_time=self.preferred_time,
            deadline_minutes=self.deadline_minutes,
            due_date=next_due,
            notes=self.notes,
            completed=False,
            recurrence=self.recurrence,
        )


@dataclass
class Pet:
    name: str
    species: str
    age_years: Optional[int] = None
    size: Optional[str] = None
    preferences: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)


@dataclass
class Owner:
    name: str
    availability_minutes: int = 120
    pets: List[Pet] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    preferred_pet_types: List[str] = field(default_factory=list)
    notes: str = ""

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)


@dataclass
class ScheduledTask:
    task: Task
    start_minute: int
    end_minute: int
    reason: str = ""


@dataclass
class SchedulePlan:
    owner: Owner
    pet: Pet
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)
    unassigned_tasks: List[Task] = field(default_factory=list)
    total_duration_minutes: int = 0
    explanation: str = ""
    warnings: List[str] = field(default_factory=list)

    def add_task(self, scheduled_task: ScheduledTask) -> None:
        self.scheduled_tasks.append(scheduled_task)
        self.total_duration_minutes += scheduled_task.task.duration_minutes

    def add_unassigned_task(self, task: Task) -> None:
        self.unassigned_tasks.append(task)

    def add_warning(self, warning: str) -> None:
        """Record a schedule-warning message for this plan."""
        self.warnings.append(warning)


@dataclass
class PawPalScheduler:
    owner: Owner
    pet: Pet
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        if task.pet_name is None:
            task.pet_name = self.pet.name
        self.tasks.append(task)
        self.owner.add_task(task)

    def mark_task_complete(self, task: Task, today: Optional[date] = None) -> Optional[Task]:
        """Mark a task complete and schedule the next recurrence if applicable.

        If the completed task is recurring, automatically add its next instance
        to the scheduler so it appears in future plans.
        """
        next_task = task.mark_complete(today=today)
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        recurrence: Optional[str] = None,
    ) -> List[Task]:
        """Return tasks matching all supplied filters (None = no filter on that field)."""
        result = self.tasks
        if pet_name is not None:
            result = [t for t in result if t.pet_name == pet_name]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if recurrence is not None:
            result = [t for t in result if t.recurrence == recurrence]
        return result

    def filter_tasks_by_completion_or_pet(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Return tasks filtered by completion status or pet name."""
        return self.filter_tasks(pet_name=pet_name, completed=completed)

    def sort_tasks_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Return tasks sorted by preferred time, then priority, then duration.

        Tasks with no preferred_time are treated as afternoon.
        """
        tasks_to_sort = tasks if tasks is not None else list(self.tasks)
        return sorted(
            tasks_to_sort,
            key=lambda t: (t.time_order, -t.priority_weight, t.duration_minutes),
        )

    @staticmethod
    def detect_conflicts(plans: List[SchedulePlan]) -> List[str]:
        """Return warning messages for overlapping scheduled tasks.

        This is a lightweight conflict detector: it does not raise an error,
        it only returns readable warnings for same-pet or cross-pet overlaps.
        """
        warnings: List[str] = []

        for i, plan_a in enumerate(plans):
            for plan_b in plans[i:]:
                same_plan = plan_a is plan_b
                if not same_plan and plan_a.owner.name != plan_b.owner.name:
                    continue

                for idx_a, st_a in enumerate(plan_a.scheduled_tasks):
                    for idx_b, st_b in enumerate(plan_b.scheduled_tasks):
                        if same_plan and idx_b <= idx_a:
                            continue

                        overlaps = (
                            st_a.start_minute < st_b.end_minute
                            and st_a.end_minute > st_b.start_minute
                        )
                        if not overlaps:
                            continue

                        if same_plan:
                            warnings.append(
                                f"WARNING: same pet '{plan_a.pet.name}' has overlapping tasks "
                                f"'{st_a.task.title}' and '{st_b.task.title}' at "
                                f"min {st_a.start_minute}-{st_a.end_minute} and "
                                f"min {st_b.start_minute}-{st_b.end_minute}."
                            )
                        else:
                            warnings.append(
                                f"WARNING: owner '{plan_a.owner.name}' has overlapping tasks "
                                f"'{st_a.task.title}' ({plan_a.pet.name}) and '{st_b.task.title}' "
                                f"({plan_b.pet.name}) at min {st_a.start_minute}-{st_a.end_minute} "
                                f"and min {st_b.start_minute}-{st_b.end_minute}."
                            )

        return warnings

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    def build_daily_schedule(self, today: Optional[date] = None) -> SchedulePlan:
        """Build a daily schedule sorted by preferred time window, then priority.

        Completed tasks are skipped. Recurring tasks generate a new future task
        when marked complete, so only incomplete tasks due today or earlier are
        considered for the current day's schedule.
        """
        plan = SchedulePlan(owner=self.owner, pet=self.pet)

        today = today or date.today()
        candidate_tasks = self.sort_tasks_by_time(
            [
                t for t in self.tasks
                if (not t.completed) and t.is_due(today)
            ]
        )

        available_minutes = self.owner.availability_minutes
        current_minute = 0
        scheduled_set: set[int] = set()

        for task in candidate_tasks:
            if task.pet_name and task.pet_name != self.pet.name:
                continue

            if task.duration_minutes > available_minutes:
                plan.add_unassigned_task(task)
                continue

            scheduled_task = ScheduledTask(
                task=task,
                start_minute=current_minute,
                end_minute=current_minute + task.duration_minutes,
                reason=f"Priority {task.priority} task for {self.pet.name}"
                + (f" [{task.preferred_time}]" if task.preferred_time else "")
                + (" [recurring]" if task.recurrence else ""),
            )
            plan.add_task(scheduled_task)
            scheduled_set.add(id(task))
            current_minute += task.duration_minutes
            available_minutes -= task.duration_minutes

        # Anything not scheduled and not already in unassigned goes to unassigned
        for task in candidate_tasks:
            if id(task) not in scheduled_set and task not in plan.unassigned_tasks:
                plan.add_unassigned_task(task)

        plan.explanation = self.explain_plan(plan)
        return plan

    def explain_plan(self, plan: SchedulePlan) -> str:
        if not plan.scheduled_tasks:
            return "No tasks could be scheduled within the owner's available time."

        lines: List[str] = [
            f"Plan for {plan.pet.name} with {plan.owner.name}:",
            f"Total scheduled duration: {plan.total_duration_minutes} minutes.",
        ]
        for st in plan.scheduled_tasks:
            lines.append(
                f"  {st.task.title} ({st.task.priority}) "
                f"min {st.start_minute}-{st.end_minute}: {st.reason}"
            )
        if plan.unassigned_tasks:
            lines.append("Unassigned tasks:")
            for t in plan.unassigned_tasks:
                lines.append(f"  - {t.title} ({t.priority}, {t.duration_minutes} min)")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Conflict detection (shared owner, overlapping time windows)
# ------------------------------------------------------------------

def detect_conflicts(plans: List[SchedulePlan]) -> List[str]:
    """Return human-readable warning messages for overlapping tasks."""
    return PawPalScheduler.detect_conflicts(plans)
