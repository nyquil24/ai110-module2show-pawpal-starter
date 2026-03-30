from pawpal_system import Owner, Pet, Task, PawPalScheduler, detect_conflicts

# --- Setup Owner (single shared pool of time for both pets) ---
owner = Owner(name="Alex", availability_minutes=90)

# --- Setup Pets ---
buddy = Pet(name="Buddy", species="Dog", age_years=3)
luna = Pet(name="Luna", species="Cat", age_years=5)

owner.add_pet(buddy)
owner.add_pet(luna)

# --- Scheduler for Buddy (tasks added OUT OF ORDER intentionally) ---
buddy_scheduler = PawPalScheduler(owner=owner, pet=buddy)
buddy_scheduler.add_task(Task(title="Flea Medicine",   duration_minutes=5,  priority="medium", preferred_time="evening"))
buddy_scheduler.add_task(Task(title="Playtime",        duration_minutes=20, priority="low",    preferred_time="afternoon"))
buddy_scheduler.add_task(Task(title="Morning Walk",    duration_minutes=30, priority="high",   preferred_time="morning"))
buddy_scheduler.add_task(Task(title="Feeding",         duration_minutes=10, priority="high",   preferred_time="morning", recurrence="daily"))

# Mark Morning Walk done — not recurring, so scheduler will skip it
buddy_scheduler.tasks[2].completed = True

# --- Scheduler for Luna (tasks added OUT OF ORDER intentionally) ---
luna_scheduler = PawPalScheduler(owner=owner, pet=luna)
luna_scheduler.add_task(Task(title="Evening Play",     duration_minutes=15, priority="low",    preferred_time="evening"))
luna_scheduler.add_task(Task(title="Litter Box Clean", duration_minutes=10, priority="high",   preferred_time="afternoon"))
luna_scheduler.add_task(Task(title="Feeding",          duration_minutes=10, priority="high",   preferred_time="morning", recurrence="daily"))
luna_scheduler.add_task(Task(title="Brush Coat",       duration_minutes=15, priority="medium", preferred_time="morning"))

# --- Show raw (unsorted) task order as added ---
print("=" * 55)
print("   RAW TASK ORDER (as added — intentionally out of order)")
print("=" * 55)
for label, scheduler in [("Buddy", buddy_scheduler), ("Luna", luna_scheduler)]:
    print(f"\n  {label}:")
    for t in scheduler.tasks:
        done = " [completed]" if t.completed else ""
        print(f"    - {t.title:<22} [{t.priority}]  {t.preferred_time or 'no time'}{done}")

# --- Show sorted order using sort_tasks_by_time ---
print("\n" + "=" * 55)
print("   SORTED ORDER (morning → afternoon → evening, then priority)")
print("=" * 55)
for label, scheduler in [("Buddy", buddy_scheduler), ("Luna", luna_scheduler)]:
    sorted_tasks = scheduler.sort_tasks_by_time()
    print(f"\n  {label}:")
    for t in sorted_tasks:
        done = " [completed]" if t.completed else ""
        print(f"    - {t.title:<22} [{t.priority}]  {t.preferred_time or 'no time'}{done}")

# --- Filter: pending (not completed) tasks ---
print("\n" + "=" * 55)
print("   FILTER: pending tasks only (completed=False)")
print("=" * 55)
for label, scheduler in [("Buddy", buddy_scheduler), ("Luna", luna_scheduler)]:
    pending = scheduler.filter_tasks(completed=False)
    print(f"\n  {label} pending ({len(pending)}):")
    for t in pending:
        print(f"    - {t.title:<22} [{t.priority}]")

# --- Filter: recurring tasks only ---
print("\n" + "=" * 55)
print("   FILTER: recurring tasks only (recurrence='daily')")
print("=" * 55)
for label, scheduler in [("Buddy", buddy_scheduler), ("Luna", luna_scheduler)]:
    recurring = scheduler.filter_tasks(recurrence="daily")
    print(f"\n  {label} daily recurring ({len(recurring)}):")
    for t in recurring:
        print(f"    - {t.title:<22} [{t.priority}]")

# --- Filter: completed tasks ---
print("\n" + "=" * 55)
print("   FILTER: completed tasks only (completed=True)")
print("=" * 55)
for label, scheduler in [("Buddy", buddy_scheduler), ("Luna", luna_scheduler)]:
    done_tasks = scheduler.filter_tasks(completed=True)
    print(f"\n  {label} completed ({len(done_tasks)}):")
    for t in done_tasks:
        print(f"    - {t.title:<22} [{t.priority}]")

# --- Build and print daily schedule (sorted, recurring respected) ---
buddy_plan = buddy_scheduler.build_daily_schedule()
luna_plan  = luna_scheduler.build_daily_schedule()

print("\n" + "=" * 55)
print("   TODAY'S SCHEDULE (sorted, recurring re-scheduled)")
print("=" * 55)
for plan in [buddy_plan, luna_plan]:
    print(f"\n  [ {plan.pet.name} the {plan.pet.species} ]")
    print("  " + "-" * 45)
    for st in plan.scheduled_tasks:
        tags = []
        if st.task.preferred_time:
            tags.append(st.task.preferred_time)
        if st.task.recurrence:
            tags.append("recurring")
        tag_str = "  " + ", ".join(f"[{x}]" for x in tags) if tags else ""
        print(f"    {st.task.title:<22} {st.task.duration_minutes:>3} min  [{st.task.priority}]{tag_str}")
    print(f"    {'Total:':<22} {plan.total_duration_minutes:>3} min")
    if plan.unassigned_tasks:
        print("    Skipped:")
        for t in plan.unassigned_tasks:
            print(f"      - {t.title} ({t.duration_minutes} min)")

# --- Scheduling warnings ---
print("\n" + "=" * 55)
print("   SCHEDULING WARNINGS")
print("=" * 55)
warnings = detect_conflicts([buddy_plan, luna_plan])
if warnings:
    for msg in warnings:
        print(f"  {msg}")
else:
    print("  No scheduling warnings found.")

print("\n" + "=" * 55)