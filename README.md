
# ⚡ SparK

Where curiosity meets community. SparK is a safe, moderated platform for students, kids, and educators to learn, share, and grow together. Built with Flask, SQLite, and Docker.

> Built for the classroom. Designed for kids. Trusted by educators.

---

## Vision

Most social platforms are engineered for engagement at any cost. SparK is built around a different idea — that young people deserve a space where they can express themselves, ask questions, and connect with peers and teachers without being exposed to the dangers of the open internet.

Safety isn't a feature on SparK. It's the entire point.

---

## Current Status

**Phase 1 — Safety Core: in progress**

The core social platform is built and functional. The classroom system is in active development. SparK is not yet open to the public.

| Area | Status |
|------|--------|
| Core social loop | ✅ Complete |
| Authentication | ✅ Complete |
| Input sanitization / XSS prevention | ✅ Complete |
| Brute force protection | ✅ Complete |
| UX polish (theme, mobile, BBCode preview) | ✅ Complete |
| Session timeout | ✅ Complete |
| Report system | 🔲 Planned |
| Content moderation queue | 🔲 Planned |
| Classroom system (lessons + assignments + grading) | 🔲 In Development |
| Closed beta (single classroom) | 🔲 Blocked on above |

---

## What's Built

### Social Platform
- Post, reply, vote, and bookmark in topic channels
- Follow other users and get a personalized feed
- Full-text search across posts and topics
- Real-time notifications via WebSockets
- Trending posts widget
- Pagination
- Dark and light theme

### Classroom System *(in development)*
- Teacher-owned classrooms with student enrollment via join code
- Lesson pages with rich BBCode content
- Assignments with due dates and submission workflow
- Grading with inline feedback, rubric support, and batch tools
- Each lesson and assignment auto-creates a discussion post in the social feed
- Parent visibility through the existing follow system

### Safety & Security
- Input sanitization and XSS prevention on all user input
- BBCode rendering — safe formatting without raw HTML
- Brute force login protection with automatic lockout
- Rate limiting on all routes
- CSRF protection on all forms
- Bcrypt password hashing
- Role-based access (admin, teacher, student, parent)

### Platform
- REST API
- Docker + Docker Compose
- GitHub Actions CI pipeline
- Admin CLI for user, post, and topic management
- Pytest test suite

---

## Who It's For

- **Students** — a structured space to ask questions, share ideas, and learn from peers
- **Kids / minors** — a safer alternative to unmoderated social platforms
- **Teachers & educators** — visibility and moderation tools, fast grading, and organized classroom content
- **Parents** — a platform designed with their kids' safety as the first priority

---

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite with FTS5 full-text search
- **Frontend:** Jinja2, Vanilla JS
- **Real-time:** Flask-SocketIO (WebSockets)
- **DevOps:** Docker, GitHub Actions CI

---

## Getting Started

### Prerequisites
- Python 3.13+
- Docker & Docker Compose

### Local Setup
```bash
# clone the repo
git clone https://github.com/onederlnd/spark.git
cd spark

# create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements-dev.txt

# create .env file
cp .env.example .env

# run the app
python run.py
```

App runs at `http://localhost:5000`

### Running with Docker
```bash
sudo docker-compose up
```

### Seeding Test Data
```bash
python scripts/admin.py
# select option 15 — seed data
# choose dev seed or a grade-specific demo seed (3rd, 5th, 7th, 8th grade)
```

---

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Dev Scripts

| Command | Description |
|---------|-------------|
| `./scripts/feature.sh` | Start a new feature branch |
| `./scripts/ship.sh` | Run tests, lint, commit, and push |
| `./scripts/done.sh` | Clean up after a PR is merged |
| `./scripts/help.sh` | Print workflow reference |

### Branching Workflow
1. `./scripts/feature.sh` — create a feature branch
2. Write code and tests
3. `./scripts/ship.sh` — commit and push
4. Open a PR on GitHub
5. Review and merge
6. `./scripts/done.sh` — return to main and clean up

---

## Project Structure

```
spark/
├── app/
│   ├── __init__.py        # app factory
│   ├── models/            # database access
│   ├── routes/            # flask blueprints
│   ├── templates/         # jinja2 templates
│   ├── utils/             # sanitization, rate limiting, brute force protection
│   └── static/            # css, js
├── tests/                 # pytest test suite
├── scripts/               # dev workflow scripts and admin CLI
├── Dockerfile
├── docker-compose.yml
└── run.py
```

---

## CI

GitHub Actions runs tests and linting on every push. See `.github/workflows/ci.yml`.

---

## Roadmap

### 🏁 Milestone: Closed Beta (single trusted classroom)

The hard floor before any real users touch this platform.

# Spark Feature Tracker

## Completed

- [x] User auth (register/login/logout)
- [x] Posts, replies, voting
- [x] Topics
- [x] Bookmarks
- [x] User profiles
- [x] Post editing & deletion
- [x] Feed pagination
- [x] Full-text search (FTS5)
- [x] User following & personalized feed
- [x] Notifications
- [x] Docker & CI/CD
- [x] Dev workflow scripts
- [x] Rate limiting
- [x] Error pages
- [x] REST API
- [x] CSRF protection
- [x] Bcrypt password hashing
- [x] Admin CLI tool
- [x] Alembic migrations
- [x] User settings page
- [x] Dark/light theme toggle
- [x] Mobile sidebar hamburger menu
- [x] BBCode preview while typing
- [x] Character counters on title, bio, topic name fields
- [x] Empty state illustrations
- [x] Input sanitization / XSS prevention
- [x] Brute force protection
- [x] Session timeout — auto logout after inactivity

---

## Alpha / Closed Beta

### Phase 1 — Safety Core

- [x] Rate limiting on registration — prevent bot account creation
- [x] Report system — flag posts/users for moderation review
- [x] Content moderation queue — hold flagged content for teacher review
- [ ] User blocking — filter content from blocked users
- [ ] Age-appropriate content filtering — baseline keyword/content rules
- [ ] COPPA compliance — Terms of Service and Privacy Policy pages

---

### Phase 2 — Classroom System

- [x] Classroom DB models — `classrooms`, `classroom_students`, `lessons`, `assignments`, `submissions`
- [x] Classroom dashboard — teacher overview of all classes
- [x] Create/join classroom — teacher creates, students join via code
- [x] Lessons — rich BBCode content pages with auto-created discussion thread
- [x] Assignments — instructions + due date + submissions + auto-created discussion thread
- [x] Student submissions — submit work, one per student per assignment
- [x] Grading UI — teacher grades submissions with feedback
- [x] Submission grid — teacher sees all students and status at a glance
- [x] Role gating — teacher/student/parent enforcement across classroom routes

---

## Beta / Trust & Verification

### Phase 3 — Trust & Verification

- [ ] Email verification on register
- [ ] Admin dashboard — proper moderation UI
- [ ] Parent dashboard — visibility into student activity
- [ ] Topic moderators — role-based permissions per topic
- [ ] School/district accounts — umbrella accounts managing multiple classrooms
- [ ] Safety visibility modes — teacher can toggle full view vs flagged-only
- [ ] Auto-hide flagged content — hold for review and notify teacher

---

## Public Release / Growth & Engagement

### Phase 4 — Growth & Engagement

- [ ] Onboarding flow — guide new users on first login
- [ ] User mentions — `@username` triggers notification
- [ ] Achievement badges — lightweight engagement without dark patterns
- [ ] Direct messages — teacher ↔ student only initially
- [ ] Landing page — public marketing site
- [ ] Data export — users can download their own data
- [ ] Trending algorithm — weight by votes, replies, and time decay

---

## Ops & Hardening

### Phase 5 — Ops & Hardening

- [ ] Full audit log — track all data changes with who/when/what
- [ ] Structured logging — replace print statements with proper log levels
- [ ] Health check endpoint — `/health` returns app and DB status
- [ ] Database backups — scheduled backup script with rotation
- [ ] Dependency vulnerability scanning — `pip-audit` in CI pipeline
- [ ] Feature flags — toggle features without deploying

---

## Backlog

- [ ] Rubric grading — structured scoring within assignments
- [ ] Multiple choice / checkbox assignment types
- [ ] Homeschool mode — parent receives notifications instead of teacher
- [ ] BBCode install
- [ ] PWA support — manifest.json + service worker
- [ ] Penpals
- [x] User not found page returns formatted error instead of white page
- [ ] Upgrade COPPA
- [ ] Update API
- [ ] WebSocket update for "COPPA pending" screen instead of logout