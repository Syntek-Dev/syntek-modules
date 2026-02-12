---
name: user-story
description: NOT USED - This project uses implementation plans instead of user stories.
model: sonnet
---

# ⚠️ THIS AGENT IS NOT USED IN THIS PROJECT

**This project does NOT use user stories. We use implementation plans instead.**

## What You Should Do Instead

If you were asked to create user stories, **DO THIS INSTEAD:**

1. **Read CLAUDE.md** to confirm this project uses plans (not stories)

2. **Use the planning approach:**
   - Create or update plan files in `docs/PLANS/`
   - Use format: `PLAN-[MODULE]-[FEATURE].md`
   - Define technical requirements, not user stories
   - Focus on implementation phases and tasks

3. **Example plan vs story:**

   **❌ User Story Format (NOT USED):**

   ```
   As a user, I want to log in with email and password
   So that I can access my account securely

   Acceptance Criteria:
   - Given I have valid credentials...
   ```

   **✅ Implementation Plan Format (USE THIS):**

   ```markdown
   # Authentication Module Implementation Plan

   ## Phase 1: Backend Foundation

   - [ ] 1.1 Create User model with email/password fields
   - [ ] 1.2 Implement password hashing (Argon2id)
   - [ ] 1.3 Create login endpoint
   - [ ] 1.4 Implement session management
   - [ ] 1.5 Write unit tests

   ## Technical Requirements

   - Email validation (RFC 5322)
   - Password strength: min 12 chars, complexity rules
   - Rate limiting: 5 attempts per minute
   - Session timeout: 30 minutes idle
   ```

4. **Use EnterPlanMode** for complex planning:
   - The tool will help create detailed technical plans
   - Plans include architecture decisions
   - Security considerations documented
   - Testing strategy defined

## Why Not User Stories?

This project is a **modular library repository**, not a user-facing application:

- We build reusable modules for other projects
- Requirements are technical, not user-centric
- Each module needs implementation details, not user narratives
- No product owner or stakeholder acceptance criteria

## If User Explicitly Requests User Stories

**Response:**

```
This project uses implementation plans instead of user stories.

According to CLAUDE.md, we document requirements using:
- Technical implementation plans (docs/PLANS/)
- Phase-based task breakdowns
- Security and compliance requirements
- Testing and documentation requirements

Would you like me to create/update an implementation plan instead?
```

## Related Tools

- **EnterPlanMode** - Create detailed implementation plans
- **/syntek-dev-suite:planner** - High-level system architecture planning
- **/syntek-dev-suite:completion** - Track plan task completion
- **/syntek-dev-suite:docs** - Write technical documentation

## Converting Requirements to Plans

If you receive user requirements or feature requests:

1. **Analyze the requirement** - Understand what needs to be built
2. **Break down into modules** - Which modules are affected?
3. **Define phases** - Backend, Frontend, Mobile, Tests, Docs
4. **List tasks** - Specific, technical, actionable items
5. **Add technical details** - Security, performance, compliance
6. **Create the plan** - Write to `docs/PLANS/PLAN-[FEATURE].md`

**Example conversion:**

**Input:** "We need users to be able to reset their password"

**Output (Implementation Plan):**

```markdown
# Password Reset Implementation Plan

## Phase 1: Backend Services

- [ ] 1.1 Create PasswordResetToken model
- [ ] 1.2 Implement token generation (32-byte random)
- [ ] 1.3 Create requestPasswordReset mutation
- [ ] 1.4 Create resetPassword mutation
- [ ] 1.5 Implement email service for reset links
- [ ] 1.6 Add rate limiting (max 3 requests/hour)

## Phase 2: Frontend

- [ ] 2.1 Create "Forgot Password" form
- [ ] 2.2 Create password reset page
- [ ] 2.3 Add email confirmation message
- [ ] 2.4 Implement client-side validation

## Security Requirements

- Token expiry: 1 hour
- One-time use tokens
- HTTPS only for reset links
- CAPTCHA on request form

## Testing

- [ ] Unit tests for token generation
- [ ] Integration tests for email delivery
- [ ] E2E tests for full reset flow
```
