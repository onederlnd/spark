# ⚡ SparK

Where curiosity meets community. SparK is a safe, moderated platform for students, kids, and educators to learn, share, and grow together. Built with Flask, SQLite, and Docker.

> Built for the classroom. Designed for kids. Trusted by educators.

---

## Vision

Most social platforms are engineered for engagement at any cost. SparK is built around a different idea — that young people deserve a space where they can express themselves, ask questions, and connect with peers and teachers without being exposed to the dangers of the open internet.

Safety isn't a feature on SparK. It's the entire point.

---

## Current Status

**Phase 2 — Alpha Classroom Ready: in progress**

The core social platform and classroom system are complete. SparK is preparing for closed beta with a single trusted classroom.

| Area | Status |
|------|--------|
| Core social loop | ✅ Complete |
| Authentication & COPPA enforcement | ✅ Complete |
| Input sanitization / XSS prevention | ✅ Complete |
| Brute force protection | ✅ Complete |
| Rate limiting | ✅ Complete |
| CSRF protection | ✅ Complete |
| Session timeout | ✅ Complete |
| Report system | ✅ Complete |
| Content moderation queue | ✅ Complete |
| Age-appropriate content filtering | ✅ Complete |
| Classroom system (assignments + grading) | ✅ Complete |
| Teacher onboarding | ✅ Complete |
| Teacher-provisioned student accounts | ✅ Complete |
| QR code login sheets | ✅ Complete |
| Student onboarding | 🔲 Planned |
| Closed beta (single classroom) | 🔲 Planned |

---

## What's Built

### Social Platform
- Post, reply, react, and bookmark in topic channels
- Four emoji reactions per post (🔥 💡 🤔 ❤️) — low-lift engagement designed for kids
- Follow other users and get a personalized feed
- Full-text search across posts and topics
- Real-time notifications via WebSockets
- Trending posts widget
- Pagination
- Dark and light theme
- Mobile-responsive with hamburger drawer

### Classroom System
- Teacher-owned classrooms with student enrollment via join code
- Copy-to-clipboard join code sharing
- Assignment status dashboard — pending grades visible at a glance
- Assignments with due dates and student submission workflow
- Grading with inline feedback and submission grid
- Role gating — teacher / student enforcement across all classroom routes
- Teacher onboarding modal on first login
- Custom content filter — teachers add words to the moderation queue

### Student Provisioning
- Teachers provision student accounts by CSV upload or manual entry
- Usernames auto-generated as `firstname.lastname` with collision resolution
- Temporary passwords generated as two words + two digits (e.g. `sunnybird42`)
- Students optionally auto-enrolled in classrooms via join codes at provisioning
- Printable credentials sheet with Print and CSV download
- QR code login sheet — one card per student with a scannable login QR code
- QR codes encode a secure persistent token — no password in the URL
- "Scan QR Code" button on login page opens device camera via jsQR
- Teachers can regenerate a student's QR token if their sheet is lost

### COPPA Compliance
- Age gate on registration — students under 13 require teacher approval
- Teacher COPPA approval dashboard
- Provisioned students set to `approved` under the school official exception — no parent consent flow required for teacher-created accounts
- Self-registered students under 13 go through the standard pending approval flow
- Provisional flag distinguishes teacher-created accounts from self-registered ones
- Terms of Service and Privacy Policy pages

### Safety & Security
- Input sanitization and XSS prevention on all user input
- BBCode rendering — safe rich formatting without raw HTML
- Brute force login protection with automatic lockout
- Rate limiting on all routes including QR login
- CSRF protection on all forms
- Bcrypt password hashing
- Role-based access (teacher, student)
- Report system — students flag posts for moderation review
- Content moderation queue — teacher reviews flagged content
- Auto-hide after 3+ reports pending teacher review
- Age-appropriate keyword content filter

### Platform
- REST API
- Docker + Docker Compose
- GitHub Actions CI pipeline
- Admin CLI for user, post, and topic management
- Pytest test suite (300+ tests)

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
python seed_demo.py
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
├── tests/                 # pytest test suite (300+ tests)
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

### 🏁 Next: Closed Beta (single trusted classroom)

| Milestone | Version | Status |
|-----------|---------|--------|
| Core platform complete | v0.1 | ✅ Done |
| Safety core complete | v0.2 | ✅ Done |
| Alpha classroom ready | v0.3 | ✅ Done |
| Closed beta (single classroom live) | v1.0 | 🔲 Planned |
| Trust & verification | v1.1 | 🔲 Planned |
| Public launch | v1.2 | 🔲 Planned |
| Growth & engagement | v1.3 | 🔲 Planned |
| Ops & hardening | v2.0 | 🔲 Planned |

[🔧 In Progress]
### v0.3 — Alpha Classroom Ready (current)
- [x] Teacher onboarding modal
- [x] Copy-to-clipboard join code
- [x] Assignment status dashboard
- [x] Teacher-provisioned student accounts (CSV + manual)
- [x] QR code login sheets
- [x] Student onboarding
- [x] Submission confirmation
- [x] Grade notification
- [x] Structured logging
- [x] Health check endpoint
- [x] Rate limit / lockout recovery UX 
- [x] Manual QA pass

### v1.0 — Closed Beta
- [ ] Live classroom deployment
- [x] Teacher feedback loop
- [ ] Safety incident review
- [ ] Database backups

### v1.1 — Trust & Verification
- [x] Email verification
- [x] Admin dashboard
- [x] Parent dashboard
- [ ] School / district accounts

### v1.2 — Public Launch
- [x] Landing page
- [x] Co-Teachers
- [x] User mentions
- [ ] Direct messages (teacher ↔ student)
- [ ] Data export
- [ ] Trending algorithm

### v1.3 — Growth & Engagement
- [x] Spark reactions (replaces votes)
- [ ] Achievement badges
- [ ] Rubric grading
- [ ] Multiple choice assignment types
- [ ] Homeschool mode
- [ ] Penpals
- [ ] PWA support

### v2.0 — Ops & Hardening
- [ ] Full audit log
- [ ] Dependency vulnerability scanning
- [ ] Feature flags
- [ ] PostgreSQL migration

---

*Last updated: March 2026*
*Current focus: v0.3 Alpha Classroom Ready → v1.0 Closed Beta*

