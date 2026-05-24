# ⚡ SparK

A safe, moderated learning platform for students and educators of all kinds — homeschool families, K-12 districts, universities, and nonprofits. Built with Flask, SQLite, and Docker.

> Built for learners. Designed for educators. Works for everyone.

---

## Vision

Most learning platforms are engineered for engagement at any cost. Recommendation algorithms, infinite scroll, notification floods — all designed to keep eyes on screens, not to support learning. The result is a generation of students who have grown up online but have nowhere to go that's genuinely built for them.

SparK is built around a different idea: that learners of all ages deserve a space to ask questions, explore ideas, and connect with teachers without the noise and manipulation of traditional social platforms.

The problems with existing platforms aren't incidental — they're structural. Ad-driven products need to maximize time-on-site. That goal is fundamentally incompatible with what education actually requires: focus, reflection, and safety. You can't bolt those values onto an engagement-first architecture. You have to start from them.

So that's what SparK does. Safety and privacy aren't features here — they're the entire foundation. There is no algorithm optimizing for clicks. There is no data harvesting. There's just a well-moderated space where kids can learn, teachers can teach, and parents can trust that their children are somewhere designed with their interests as the first priority.

This also means SparK isn't trying to replace every tool in an educator's toolkit. It's designed to be a focused, purposeful environment: structured social learning, classroom management, and AI-assisted study — nothing else. The scope is intentional.

---

## Current Status

**Phase 2 — Alpha Classroom Ready: in progress**
The core social environment and classroom system are complete. SparK is preparing for closed beta with a single trusted classroom.

| Area | Status |
| --- | --- |
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
| Curiosity AI study buddy | ✅ Complete |
| Student onboarding | 🔲 Planned |
| Closed beta (single classroom) | 🔲 Planned |

---

## What's Built

### Social Platform

The core of SparK is a structured social environment organized around topic channels. Students can post, reply, react, and bookmark content. There are four emoji reactions per post (🔥 💡 🤔 ❤️) — low-lift, age-appropriate engagement that doesn't gamify attention the way like counts do.

Users can follow each other to get a personalized feed, search full-text across posts and topics, and receive real-time notifications via WebSockets. The interface is mobile-responsive with a hamburger drawer, supports both dark and light themes, and includes a trending posts widget and pagination.

### Classroom System

Teachers own their classrooms. Students join via a shareable join code. From there, teachers get a complete assignment and grading workflow: create assignments with due dates, review student submissions, grade with inline feedback, and track pending grades from a status dashboard at a glance.

Role gating enforces teacher/student permissions across all classroom routes. Teachers can add custom words to the content filter — anything that needs to go into the moderation queue for their specific context. Teacher onboarding is handled by a modal on first login.

### Curiosity

Curiosity is SparK's AI-powered study buddy, built on Claude. It's designed for students, study groups, and learners of any age.

The key design decision: Curiosity doesn't hand students answers. It uses a guided Socratic approach — asking questions, prompting reflection, helping students arrive at understanding rather than just handing it over. Subject and topic context is passed into every conversation so responses stay focused and relevant. Conversation history is persistent, so students can pick up where they left off per topic.

### Student Provisioning

Teachers can provision student accounts in bulk via CSV upload or individually via manual entry. Usernames are auto-generated as `firstname.lastname` with collision resolution. Temporary passwords are generated as two words plus two digits (e.g. `sunnybird42`) — memorable enough for kids, random enough to be secure.

Students can optionally be auto-enrolled in classrooms at provisioning. Once accounts are created, teachers get a printable credentials sheet with a Print button and CSV download. There's also a QR code login sheet — one card per student with a scannable QR code that encodes a secure persistent token (no password in the URL). The login page has a "Scan QR Code" button that opens the device camera via jsQR. If a sheet is lost, teachers can regenerate any student's token.

### COPPA Compliance

SparK enforces COPPA compliance at the registration level. Self-registered students under 13 go through a standard pending approval flow and require teacher approval before they can access the platform. Teacher-provisioned accounts are set to `approved` under the school official exception, bypassing the parent consent flow for accounts the teacher has created directly.

A provisional flag distinguishes teacher-created accounts from self-registered ones. The platform includes Terms of Service and Privacy Policy pages.

### Safety & Security

- Input sanitization and XSS prevention on all user content
- BBCode rendering — safe rich formatting without raw HTML
- Brute force login protection with automatic lockout
- Rate limiting on all routes including QR login
- CSRF protection on all forms
- Bcrypt password hashing
- Role-based access (teacher, student)
- Report system — students flag posts for moderation review
- Content moderation queue — teachers review flagged content
- Auto-hide after 3+ reports pending teacher review
- Age-appropriate keyword content filter

### Platform

- REST API
- Docker + Docker Compose
- GitHub Actions CI pipeline
- Admin CLI for user, post, and topic management
- Pytest test suite (1,000+ tests)

---

## Who It's For

SparK is designed for four distinct groups with different needs:

**Students** want a structured space to ask questions, share ideas, and learn from peers without the pressure and chaos of public social platforms.

**Kids and minors** deserve a safer alternative to unmoderated spaces online — a place designed with their wellbeing as the constraint, not their engagement.

**Teachers and educators** need visibility and control: moderation tools, fast grading, organized classroom content, and the ability to provision and manage student accounts without depending on students to self-register correctly.

**Parents** want to know their kids are somewhere that's actually designed for them — where the platform's incentives align with their child's safety, not against it.

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, Flask |
| Database | SQLite with FTS5 full-text search |
| Frontend | Jinja2, Vanilla JS |
| Real-time | Flask-SocketIO (WebSockets) |
| AI | Anthropic Claude (Curiosity) |
| DevOps | Docker, GitHub Actions CI |

---

## Getting Started

### Prerequisites

- Python 3.13+
- Docker & Docker Compose

### Environment Variables

Copy `.env.example` to `.env` before running. Required variables:

| Variable | Description |
| --- | --- |
| `SECRET_KEY` | Flask session secret key |
| `ANTHROPIC_API_KEY` | Anthropic API key for Curiosity |
| `DATABASE_URL` | SQLite database path (default: `sqlite:///spark.db`) |
| `FLASK_ENV` | `development` or `production` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting (`true`/`false`) |

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
# edit .env and add your keys

# run the app
python run.py
```

App runs at `http://localhost:5000`.

### Running with Docker

```bash
sudo docker-compose up
```

### Seeding Test Data

```bash
python seed_demo.py
```

---

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Dev Scripts

| Command | Description |
| --- | --- |
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

```python

spark/
├── app/
│   ├── __init__.py        # app factory
│   ├── models/            # database access
│   ├── routes/            # flask blueprints
│   ├── templates/         # jinja2 templates
│   ├── utils/             # sanitization, rate limiting, brute force protection
│   └── static/            # css, js
├── tests/                 # pytest test suite (1,000+ tests)
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
| --- | --- | --- |
| Core platform complete | v0.1 | ✅ Done |
| Safety core complete | v0.2 | ✅ Done |
| Alpha classroom ready | v0.3 | ✅ Done |
| Closed beta (single classroom live) | v1.0 | 🔲 Planned |
| Trust & verification | v1.1 | 🔲 Planned |
| Public launch | v1.2 | 🔲 Planned |
| Growth & engagement | v1.3 | 🔲 Planned |
| Ops & hardening | v2.0 | 🔲 Planned |

### v0.3 — Alpha Classroom Ready

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
- [i] School / district accounts — mostly implemented, not yet linked

### v1.2 — Public Launch

- [x] Landing page
- [x] Co-teachers
- [x] User mentions
- [x] Direct messages (teacher ↔ student)
- [ ] Data export
- [ ] Trending algorithm

### v1.3 — Growth & Engagement

- [x] Spark reactions (replaces votes)
- [ ] Achievement badges
- [ ] Rubric grading
- [x] Multiple choice assignment types
- [ ] Homeschool mode
- [ ] Penpals
- [ ] PWA support

### v1.4 Curiosity

- [x] Core chat — Claude integration + subject/topic context
- [x] Persistent conversations — DB model (save & resume)
- [x] Subject / topic browser UI
- [x] Streaming responses
- [x] Conversation history UI
- [ ] Multi-subject session switching
- [x] Response caching — topic_key + question_hash, 30-day TTL
- [x] Cache feedback — anonymous thumbs up/down, COPPA-clean
- [x] Topic prompt overrides — teacher-customisable per topic
- [x] Social suggestions — trending questions, discussion starters, classmate counts
- [x] Teacher review dashboard
- [x] Discussion starter UI
- [x] Cache hit counter

### v2.0 — Ops & Hardening

- [ ] Full audit log
- [x] Dependency vulnerability scanning
- [ ] Feature flags
- [ ] PostgreSQL migration

---

## Contributing

SparK is in closed beta. Contributions aren't open yet, but if you're an educator, developer, or researcher interested in the project, reach out.

---

## License

All rights reserved. SparK is not open source at this time.

---

> SparK is being developed with future separation in mind — the core platform, classroom system, and Curiosity AI are designed as distinct modules that will eventually live with independent development.

*Last updated: May 2026*  
*Current focus: v0.3 Alpha Classroom Ready → v1.0 Closed Beta*
