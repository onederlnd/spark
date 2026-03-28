# ⚡ SparK — Development Tracker

**Current Goal:** Ship a fully working in-classroom version for live alpha testing with a single trusted classroom.

---

## 🏁 Milestones

| Milestone | Version | Status |
|-----------|---------|--------|
| Core platform complete | v0.1 | ✅ Done |
| Safety core complete | v0.2 | 🔧 In Progress |
| Alpha classroom ready | v0.3 | 🔲 Blocked on v0.2 |
| Closed beta (single classroom live) | v1.0 | 🔲 Planned |
| Trust & verification | v1.1 | 🔲 Planned |
| Public launch | v1.2 | 🔲 Planned |
| Growth & engagement | v1.3 | 🔲 Planned |
| Ops & hardening | v2.0 | 🔲 Planned |

---

## ✅ v0.1 — Core Platform
> **Status: Complete**
> Everything needed for a functioning social + classroom platform.

### Social
- [x] User auth — register / login / logout
- [x] Posts, replies, voting
- [x] Topics
- [x] Bookmarks
- [x] User profiles
- [x] Post editing & deletion
- [x] Feed pagination
- [x] Full-text search (FTS5)
- [x] User following & personalized feed
- [x] Notifications (real-time via WebSockets)
- [x] Dark / light theme toggle
- [x] Mobile sidebar hamburger menu
- [x] BBCode preview while typing
- [x] Character counters on title, bio, topic name fields
- [x] Empty state illustrations

### Classroom System
- [x] Classroom DB models — `classrooms`, `classroom_members`, `lessons`, `assignments`, `submissions`
- [x] Classroom dashboard — teacher overview of all classes
- [x] Create / join classroom — teacher creates, students join via code
- [x] Lessons — rich BBCode content pages with auto-created discussion thread
- [x] Assignments — instructions + due date + submissions + auto-created discussion thread
- [x] Student submissions — one per student per assignment, editable
- [x] Grading UI — inline feedback per submission
- [x] Submission grid — teacher sees all students and status at a glance
- [x] Role gating — teacher / student / parent enforcement across all classroom routes
- [x] Global Resources - teachers can upload and add static resources to multiple assignments

### Security & Infrastructure
- [x] Input sanitization / XSS prevention
- [x] CSRF protection on all forms
- [x] Bcrypt password hashing
- [x] Brute force protection — lockout after repeated failures
- [x] Rate limiting on all routes
- [x] Session timeout — auto logout after inactivity
- [x] REST API
- [x] Docker & Docker Compose
- [x] GitHub Actions CI/CD pipeline
- [x] Admin CLI tool
- [x] Alembic migrations
- [x] Dev workflow scripts (`feature.sh`, `ship.sh`, `done.sh`)
- [x] Error pages (400, 401, 403, 404, 405, 429, 500)
- [x] User not found returns formatted error page

---

## 🔧 v0.2 — Safety Core
> **Status: In Progress**
> Hard floor before any real users touch the platform. Nothing ships to a classroom until this is done.

### COPPA & Access
- [x] Rate limiting on registration — prevent bot account creation
- [x] COPPA enforcement — age gate, teacher approval workflow, coppa_status gating
- [x] COPPA Terms of Service and Privacy Policy pages
- [x] `teacher_required()` decorator — clean role enforcement utility
- [x] User blocking — filter content from blocked users

### Content Safety
- [x] Report system — students flag posts for moderation review
- [x] Content moderation queue — teacher dashboard for flagged content
- [x] Auto-hide flagged content — 3+ reports hides post pending review
- [x] Age-appropriate content filtering — baseline keyword / content rules

---

## 🧪 v0.3 — Alpha Classroom Ready
> **Status: Blocked on v0.2**
> Everything required to hand the keys to a real teacher with real students.

### Teacher Experience
- [x] Teacher onboarding — first-login guide for classroom setup
- [x] Classroom invite flow polish — copy-to-clipboard join code
- [x] Assignment status dashboard — quick view of pending grades
- [x] Teacher provisioned student accounts (CSV + manual)
- [x] QR code login sheet

### Student Experience
- [x] Student onboarding — first-login guide for students
- [x] Submission confirmation — clear success state after submitting
- [x] Grade notification — student notified when teacher grades their work 

### Stability
- [x] Structured logging — replace all `print()` statements with proper log levels
- [x] Health check endpoint — `/health` returns app and DB status
- [x] Rate limit / lockout recovery UX 
- [ ] Smoke Test/Manual QA pass — full walkthrough as teacher, student, and parent


---

## 🎓 v1.0 — Closed Beta (Single Classroom Live)
> **Status: Planned**
> Real students. Real teacher. Real stakes. The alpha classroom milestone.

- [ ] Live classroom deployment — single trusted classroom running in production
- [ ] Teacher feedback loop — weekly check-in process with alpha teacher
- [ ] Bug tracking — structured log of issues found in live use
- [ ] Safety incident review — confirm moderation workflow holds under real usage
- [ ] Session stability — confirm WebSocket and session timeout work in production
- [ ] Database backups — scheduled backup with rotation before go-live

---

## 🔐 v1.1 — Trust & Verification
> **Status: Planned**
> Expands safety and visibility ahead of multi-classroom rollout.

- [ ] Email verification on register
- [ ] Admin dashboard — full moderation UI for platform-level oversight
- [ ] Parent dashboard — visibility into student activity via follow system
- [ ] Topic moderators — role-based permissions per topic
- [ ] Safety visibility modes — teacher toggles full view vs flagged-only
- [ ] School / district accounts — umbrella accounts managing multiple classrooms
- [ ] WebSocket update for COPPA pending screen — no re-login required (similar to Netflix /activate flow)
- [ ] Gatekeep different classrooms with different teachers. e.g. teacher A will get notified about students who join teacher B's classroom


## 🚀 v1.2 — Public Launch
> **Status: Planned**
> Open the doors beyond the alpha classroom.

- [x] Landing page — public marketing site
- [ ] Onboarding flow — guide new users on first login
- [ ] User mentions — `@username` triggers notification
- [ ] Direct messages — teacher ↔ student only initially
- [ ] Data export — users can download their own data
- [ ] Trending algorithm — weight by votes, replies, and time decay
- [ ] Upgrade COPPA — review and harden compliance for public launch
- [ ] Update REST API — review and expand for public access

---

## 🎮 v1.3 — Growth & Engagement
> **Status: Planned**
> Deepen engagement without dark patterns.

- [ ] Achievement badges — lightweight milestones for students
- [ ] Rubric grading — structured scoring within assignments
- [ ] Multiple choice / checkbox assignment types
- [ ] Homeschool mode — parent receives teacher notifications instead
- [ ] Penpals — cross-classroom connection feature
- [ ] PWA support — `manifest.json` + service worker

---

## ⚙️ v2.0 — Ops & Hardening
> **Status: Planned**
> Production-grade infrastructure for scale.

- [ ] Full audit log — track all data changes with who / when / what
- [ ] Dependency vulnerability scanning — `pip-audit` in CI pipeline
- [ ] Feature flags — toggle features without deploying
- [x] BBCode standalone install / package
- [ ] PostgreSQL migration — replace SQLite for multi-tenant scale

---

## 🗂️ Backlog (Unscheduled)

Items captured but not yet assigned to a version.

- [ ] Rubric grading UI improvements
- [ ] Admin CLI expansion — more management commands
- [ ] API documentation/update
- [ ] Rate limit tuning — review thresholds after alpha data

---

*Last updated: March 2026*
*Current focus: v0.2 Safety Core → v0.3 Alpha Ready → v1.0 Classroom Live*