from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Task, PawPalScheduler, detect_conflicts

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Daily pet care scheduler — sort, filter, and detect conflicts.")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "schedulers" not in st.session_state:
    st.session_state.schedulers = {}   # pet_name -> PawPalScheduler
if "plans" not in st.session_state:
    st.session_state.plans = {}        # pet_name -> SchedulePlan

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Alex")
with col2:
    availability = st.number_input(
        "Daily availability (minutes)", min_value=10, max_value=480, value=90, step=5
    )

if st.button("Save owner"):
    st.session_state.owner = Owner(name=owner_name, availability_minutes=int(availability))
    st.session_state.schedulers = {}
    st.session_state.plans = {}
    st.success(f"Owner **{owner_name}** saved with **{availability} min** available.")

if st.session_state.owner is None:
    st.info("Save an owner above to continue.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 2 — Add pets
# ---------------------------------------------------------------------------
st.header("2. Pets")
col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Buddy")
with col2:
    species = st.selectbox("Species", ["Dog", "Cat", "Rabbit", "Bird", "Other"])
with col3:
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)

if st.button("Add pet"):
    if pet_name in st.session_state.schedulers:
        st.warning(f"**{pet_name}** is already added.")
    else:
        pet = Pet(name=pet_name, species=species, age_years=int(age))
        owner.add_pet(pet)
        st.session_state.schedulers[pet_name] = PawPalScheduler(owner=owner, pet=pet)
        st.success(f"Added **{pet_name}** the {species}.")

if not st.session_state.schedulers:
    st.info("Add at least one pet above to continue.")
    st.stop()

st.write("**Registered pets:**", ", ".join(st.session_state.schedulers.keys()))

# ---------------------------------------------------------------------------
# Section 3 — Add tasks
# ---------------------------------------------------------------------------
st.header("3. Add tasks")

col1, col2 = st.columns(2)
with col1:
    task_pet = st.selectbox("Assign to pet", list(st.session_state.schedulers.keys()))
with col2:
    task_title = st.text_input("Task title", value="Morning Walk")

col1, col2, col3, col4 = st.columns(4)
with col1:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col2:
    priority = st.selectbox("Priority", ["high", "medium", "low"])
with col3:
    preferred_time = st.selectbox("Time window", ["morning", "afternoon", "evening", "(none)"])
with col4:
    recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"])

if st.button("Add task"):
    scheduler: PawPalScheduler = st.session_state.schedulers[task_pet]
    scheduler.add_task(
        Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            preferred_time=None if preferred_time == "(none)" else preferred_time,
            recurrence=None if recurrence == "none" else recurrence,
            due_date=date.today(),
        )
    )
    st.success(f"Task **{task_title}** added for {task_pet}.")

# ---------------------------------------------------------------------------
# Section 4 — Filter & sort view
# ---------------------------------------------------------------------------
st.header("4. Filter & sort tasks")

filter_pet = st.selectbox("View tasks for", list(st.session_state.schedulers.keys()), key="filter_pet")
filter_status = st.radio("Status", ["All", "Pending", "Completed"], horizontal=True)
filter_recurrence = st.radio("Recurrence", ["All", "daily", "weekly", "none"], horizontal=True)

scheduler: PawPalScheduler = st.session_state.schedulers[filter_pet]

completed_filter = None if filter_status == "All" else (filter_status == "Completed")
recurrence_filter = None if filter_recurrence == "All" else (None if filter_recurrence == "none" else filter_recurrence)
if filter_recurrence == "none":
    filtered = [t for t in scheduler.filter_tasks(completed=completed_filter) if t.recurrence is None]
else:
    filtered = scheduler.filter_tasks(completed=completed_filter, recurrence=recurrence_filter)

sorted_tasks = scheduler.sort_tasks_by_time(filtered)

if sorted_tasks:
    rows = [
        {
            "Title": t.title,
            "Priority": t.priority,
            "Time window": t.preferred_time or "—",
            "Duration (min)": t.duration_minutes,
            "Recurrence": t.recurrence or "—",
            "Done": "✓" if t.completed else "",
        }
        for t in sorted_tasks
    ]
    st.table(rows)
else:
    st.info("No tasks match the current filters.")

# ---------------------------------------------------------------------------
# Section 5 — Generate schedule
# ---------------------------------------------------------------------------
st.header("5. Generate today's schedule")

if st.button("Build schedule for all pets"):
    st.session_state.plans = {}
    for pname, sched in st.session_state.schedulers.items():
        st.session_state.plans[pname] = sched.build_daily_schedule(today=date.today())

if st.session_state.plans:
    for pname, plan in st.session_state.plans.items():
        st.subheader(f"{pname} the {plan.pet.species}")

        if plan.scheduled_tasks:
            rows = [
                {
                    "Task": item.task.title,
                    "Priority": item.task.priority,
                    "Time window": item.task.preferred_time or "—",
                    "Duration (min)": item.task.duration_minutes,
                    "Recurrence": item.task.recurrence or "—",
                    "Slot (min)": f"{item.start_minute}–{item.end_minute}",
                }
                for item in plan.scheduled_tasks
            ]
            st.table(rows)
            st.success(
                f"Scheduled **{len(plan.scheduled_tasks)} tasks** "
                f"using **{plan.total_duration_minutes} / {owner.availability_minutes} min**."
            )
        else:
            st.warning(f"No tasks could be scheduled for {pname}.")

        if plan.unassigned_tasks:
            with st.expander(f"Skipped tasks ({len(plan.unassigned_tasks)})"):
                for t in plan.unassigned_tasks:
                    st.write(f"- **{t.title}** ({t.duration_minutes} min, {t.priority})")

    # --- Conflict detection across all pets --------------------------------
    st.subheader("Conflict report")
    all_plans = list(st.session_state.plans.values())
    conflicts = detect_conflicts(all_plans)
    if conflicts:
        for msg in conflicts:
            st.warning(msg)
    else:
        st.success("No scheduling conflicts detected.")