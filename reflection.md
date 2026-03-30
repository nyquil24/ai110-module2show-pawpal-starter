# PawPal+ Project Reflection

## 1. System Design

1. Add/Edit a Pet & Owner Profile - Enter the pet's name, type, and 
owner's available time per day. 

2. Add a Care Task - Create tasks like walks, feeding, meds, or grooming with a duration and priority level. 

3. Generate Today's Schedule - trigger the planner to produce a prioritized daily plan based on available time and task priorities, with a brief explanation of why each task was included or skipped. 

**Owner** 

Attributes 

        * name - owner's name 
        * available_time - total minutes available per day for pet care 
        * preferences - optional notes (e.g., prefers morning walks)

Methods: 

        * get_available_time() - returns daily time budget


**Pet** 

    Attributes: 

        * name - pet's name 
        * species - dog, cat, etc. 
        * age - affects care needs 
    
    Methods: 

        * get_info() - returns a summary string for display 

**Tasks** 

    Attributes: 

        * name - e.g., "Morning Walk" 
        * category - walk, feeding, meds, grooming, enrichment 
        * duration - time in minutes 
        * priority - high / medium / low 
        * completed - boolean 

    Methods: 

        * mark_complete() - sets completed to True 
        * is_high_priority() - returns True if priority is high 

**Scheduler** 

    Attributes: 

        * pet - the Pet being cared for 
        * owner - the Owner with time constraints 
        * tasks - list of Task objects 

    Methods: 

        * generate_plan() - selects tasks that fit within available time, sorted by priority 

        * explain_reasoning() - returns a human-readable explanation of what was included/skipped and why

**DailyPlan** 

    Attributes: 

        * scheduled_tasks - list of tasks that fit 
        * skipped_tasks - tasks that were cut due to time 
        * total_time_used - sum of scheduled task durations 
        * reasoning - explanation string from the Scheduler 

    Methods: 

        * display() - formats the plan for the UI 
        * summarize() - short summary (e.g., "4 tasks, 75 min planned")


https://mermaid.ai/play?utm_source=mermaid_live_editor&utm_medium=share#pako:eNqNVMlu2zAQ_RWCpy62oMWbeMilORZogPRUCBAYaSwRlkiBpNI4hvPtHS12KcFNowNBzvr43ognmqkcKKNZxY25F7zQvE4kwa-3kB-_JWhyGkzd9_XRaiELInkNjlVIS_gzFxV_qiC1YuIcUxoNe9AgMzCOswCbTjM_fSZYbgg5J9KF8wD2A2BGq2kgE5NePcoCZt2F3CvsOWTdbPuTm8PH-2bcQqH0cdY4bzW3QslbxAilhXUTnpSqSKbqpgILueOouT6kFweiflbCdQuTlqIo00tJjOhK3bzVY1ZC3lYzfTuKG7COZZgB1a2O9bsw9q0j5o1YXKeSYiiSkDYVl4jgHtU9PuDeiYEXdAqZauBGSWThfQWuJSZYHQxmvEyeztG4QQfRNDdCOnmssrzq5y9tzYTyUaUrUseVC4PXOM6w9y7T1qiVeIV_XWygNaFBQslyeTfuOvpZR_aIrzu7Mb7nfcFDP5GMlHwM-6vlvODQhhG81H9jh-YXKg3ZK_1eyhSLgQoyi0la1fMsz7tzJGQ48Spv-3eALmihRU6Z1S0saA265t2R9jon1JaA_xhluM1x9BOayDPmNFz-Uqq-pGnVFiVle14ZPLVNjtM3vmZXK748OehvqpWWsiAI4r4KZSf6Qtkm8Na-v_L93Xq1jra7YEGPlC2jjbcOV3G4DqMwiuJwe17Q175v4MVRHEXb2A99P9gEu835D8pmmQA


**a. Initial design**

- Briefly describe your initial UML design.

    My initial UML design includes an Owner, Pet, Task, Scheduler, and DailyPlan. They all have public methods and attributes that helps with the structuring of the class. 

- What classes did you include, and what responsibilities did you assign to each?


    Pet - pet being cared for 
    Task - care activity with its duration, priority, and completion state
    Scheduler - allows a user to schedule tasks 
    DailyPlan - holds the scheduler's actions. 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

    I asked Copilot if it noticed any missing relationships or potential logic bottlenecks to my "skeleton" and it gave my recommendations that I included in my classes. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

    The scheduler considers three constraints: **owner availability** (a fixed daily minute budget), **task priority** (high / medium / low mapped to numeric weights), and **preferred time window** (morning, afternoon, or evening). It also respects **task completion state** — skipping non-recurring tasks already marked done — and **recurrence** — always re-queuing daily or weekly tasks regardless of prior completion.

    Preferred time window was ranked first in the sort order because it reflects the real-world structure of a pet owner's day: a morning walk has to happen in the morning or it loses its purpose. Priority was ranked second because, within a given window, a feeding should always come before optional enrichment. Owner availability acts as the hard cap — no matter how high a task's priority, it cannot be scheduled if there is no time left.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

    The scheduler uses a **greedy first-fit** strategy: it works through the sorted task list in one pass and skips any task whose duration exceeds the remaining available time, even if a shorter task later in the list could still fit. For example, if 15 minutes remain and the next task needs 20 minutes, that task is skipped — but a 10-minute task further down the list is also never reached for that slot.

    This tradeoff is reasonable for pet care because the tasks that matter most — feedings, medication, walks — are already sorted to the front by priority and time window. Missing a low-priority task (like a grooming session) because a medium-priority one couldn't fit is an acceptable outcome; the owner can reschedule it tomorrow. The greedy approach keeps the code simple and fast (O(n log n)), which is appropriate for a daily planner with a small, predictable number of tasks per pet.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
