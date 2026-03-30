from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, PawPalScheduler, detect_conflicts


def test_filter_tasks_by_completed_status():
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    scheduler = PawPalScheduler(owner=owner, pet=pet)

    incomplete_task = Task("Feed dog", duration_minutes=10, completed=False)
    complete_task = Task("Walk dog", duration_minutes=20, completed=True)
    scheduler.add_task(incomplete_task)
    scheduler.add_task(complete_task)

    assert scheduler.filter_tasks(completed=False) == [incomplete_task]
    assert scheduler.filter_tasks(completed=True) == [complete_task]

def test_filter_tasks_by_pet_name():
    owner = Owner(name="Alex")
    buddy = Pet(name="Buddy", species="Dog")
    luna = Pet(name="Luna", species="Cat")
    owner.add_pet(buddy)
    owner.add_pet(luna)

    buddy_scheduler = PawPalScheduler(owner=owner, pet=buddy)
    luna_scheduler = PawPalScheduler(owner=owner, pet=luna)

    buddy_task = Task("Feed Buddy", duration_minutes=10, pet_name="Buddy")
    luna_task = Task("Feed Luna", duration_minutes=10, pet_name="Luna")
    buddy_scheduler.add_task(buddy_task)
    luna_scheduler.add_task(luna_task)

    assert buddy_scheduler.filter_tasks(pet_name="Buddy") == [buddy_task]
    assert luna_scheduler.filter_tasks(pet_name="Luna") == [luna_task]

def test_filter_tasks_by_completion_or_pet_wrapper():
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    scheduler = PawPalScheduler(owner=owner, pet=pet)

    task1 = Task("Feed dog", duration_minutes=10, pet_name="Buddy", completed=False)
    task2 = Task("Groom dog", duration_minutes=15, pet_name="Buddy", completed=True)
    scheduler.add_task(task1)
    scheduler.add_task(task2)

    assert scheduler.filter_tasks_by_completion_or_pet(completed=False) == [task1]
    assert scheduler.filter_tasks_by_completion_or_pet(pet_name="Buddy") == [task1, task2]


def test_mark_complete_creates_next_daily_task():
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    scheduler = PawPalScheduler(owner=owner, pet=pet)

    today = date(2026, 3, 30)
    task = Task(
        "Feeding",
        duration_minutes=10,
        pet_name="Buddy",
        priority="high",
        preferred_time="morning",
        recurrence="daily",
        due_date=today,
    )
    scheduler.add_task(task)

    next_task = scheduler.mark_task_complete(task, today=today)

    assert task.completed is True
    assert next_task is not None
    assert next_task.recurrence == "daily"
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task in scheduler.tasks


def test_detect_conflicts_returns_warning_for_overlapping_plans():
    owner = Owner(name="Alex")
    buddy = Pet(name="Buddy", species="Dog")
    luna = Pet(name="Luna", species="Cat")
    buddy_scheduler = PawPalScheduler(owner=owner, pet=buddy)
    luna_scheduler = PawPalScheduler(owner=owner, pet=luna)

    buddy_scheduler.add_task(Task("Buddy Feed", duration_minutes=15, priority="high", preferred_time="morning"))
    luna_scheduler.add_task(Task("Luna Feed", duration_minutes=15, priority="high", preferred_time="morning"))

    buddy_plan = buddy_scheduler.build_daily_schedule(today=date(2026, 3, 30))
    luna_plan = luna_scheduler.build_daily_schedule(today=date(2026, 3, 30))

    warnings = detect_conflicts([buddy_plan, luna_plan])
    assert any("WARNING" in w for w in warnings)
    assert any("Buddy Feed" in w for w in warnings)
    assert any("Luna Feed" in w for w in warnings)


def test_build_schedule_excludes_next_day_task():
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    scheduler = PawPalScheduler(owner=owner, pet=pet)

    today = date(2026, 3, 30)
    task_today = Task("Feed", duration_minutes=10, pet_name="Buddy", due_date=today)
    task_tomorrow = Task(
        "Feed tomorrow",
        duration_minutes=10,
        pet_name="Buddy",
        due_date=today + timedelta(days=1),
    )
    scheduler.add_task(task_today)
    scheduler.add_task(task_tomorrow)

    plan = scheduler.build_daily_schedule(today=today)
    assert task_today in [st.task for st in plan.scheduled_tasks]
    assert task_tomorrow not in [st.task for st in plan.scheduled_tasks]
