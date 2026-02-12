---
name: sprint
description: NOT USED - This project uses implementation plans instead of sprints.
model: sonnet
---

# ⚠️ THIS AGENT IS NOT USED IN THIS PROJECT

**This project does NOT use sprints. We use implementation plans instead.**

## What You Should Do Instead

If you were asked to organize work or create sprints, **DO THIS INSTEAD:**

1. **Read CLAUDE.md** to confirm this project uses plans (not sprints)

2. **Use the planning approach:**
   - Create or update plan files in `docs/PLANS/`
   - Use format: `PLAN-[MODULE]-[FEATURE].md`
   - Break work into phases, not sprints
   - Use checkboxes for task tracking: `- [ ]` and `- [x]`

3. **Example plan structure:**

   ```markdown
   # Full-Stack [Feature] Implementation Plan

   ## Phase 1: Backend Foundation (Week 1-2)

   - [ ] Task 1.1: Database models
   - [ ] Task 1.2: Services
   - [ ] Task 1.3: API endpoints

   ## Phase 2: Frontend (Week 3-4)

   - [ ] Task 2.1: Components
   - [ ] Task 2.2: State management
   - [ ] Task 2.3: Integration
   ```

4. **Use EnterPlanMode** for complex planning:

   ```
   When the user asks to plan work, use the EnterPlanMode tool
   to create a detailed implementation plan.
   ```

## Why Not Sprints?

This project is a **modular library repository**, not an application:

- Modules are developed independently
- Each module has its own implementation plan
- Work is tracked by phase completion, not sprint velocity
- No story points or MoSCoW prioritisation needed

## If User Explicitly Requests Sprints

**Response:**

```
This project uses implementation plans instead of sprints.

According to CLAUDE.md, we track work using:
- Plan files in docs/PLANS/
- Phase-based task breakdowns
- Checkbox completion tracking

Would you like me to create/update an implementation plan instead?
```

## Related Tools

- **EnterPlanMode** - Create detailed implementation plans
- **/syntek-dev-suite:planner** - High-level system architecture planning
- **/syntek-dev-suite:completion** - Track plan task completion
