# ⚡ SparK

Where curiosity meets community. SparK is a safe, moderated platform for students,
kids, and educators to learn, share, and grow together.
Built with Flask, SQLite, and Docker.

> Built for the classroom. Designed for kids. Trusted by educators.

## Vision

Most social platforms are engineered for engagement at any cost. SparK is built
around a different idea — that young people deserve a space where they can express
themselves, ask questions, and connect with peers and teachers without being exposed
to the dangers of the open internet.

Safety isn't a feature on SparK. It's the entire point.

## Current Status

**Phase 1 — Safety Core: in progress**

The core social platform is built and functional. We are currently hardening the
platform for real classroom use. SparK is not yet open to the public.

| Area | Status |
|------|--------|
| Core social loop | ✅ Complete |
| Authentication | ✅ Complete |
| Input sanitization / XSS prevention | ✅ Complete |
| Brute force protection | ✅ Complete |
| Session timeout | ⬜ In Progress |
| Report system | ⬜ Planned |
| Content moderation queue | ⬜ Planned |
| Closed beta (single classroom) | ⬜ Blocked on above |

## What's Built

### Social Platform
- Post, reply, vote, and bookmark in topic channels
- Follow other users and get a personalized feed
- Full-text search across posts and users
- Real-time notifications via WebSockets
- Trending posts widget
- Pagination

### Safety & Security
- Input sanitization and XSS prevention on all user input
- BBCode rendering — safe formatting without raw HTML
- Brute force login protection with automatic lockout
- Rate limiting on all routes
- CSRF protection on all forms
- Bcrypt password hashing
- Role-based access (admins, moderators, teachers, students)

### Platform
- REST API
- Docker + Docker Compose
- GitHub Actions CI pipeline
- Admin CLI for user, post, and topic management
- Pytest test suite

## Who It's For
- **Students** — a structured space to ask questions, share ideas, and learn from peers
- **Kids / minors** — a safer alternative to unmoderated social platforms
- **Teachers & educators** — visibility and moderation tools to manage communities
- **Parents** — a platform designed with their kids' safety as the first priority

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite with FTS5 full-text search
- **Frontend:** Jinja2, Vanilla JS
- **Real-time:** Flask-SocketIO (WebSockets)
- **DevOps:** Docker, GitHub Actions CI

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
# select option 15 — auto-seed
```

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

## CI
GitHub Actions runs tests and linting on every push. See `.github/workflows/ci.yml`.

## Roadmap

### 🏁 Milestone: Closed Beta (single trusted classroom)
The hard floor before any real users touch this platform.
- [x] Core social loop — post, reply, vote, follow, feed, search, notifications
- [x] Input sanitization / XSS prevention
- [x] Brute force protection
- [ ] Session timeout — auto-logout after inactivity for shared school computers
- [ ] Report system — kids need a way to flag content
- [ ] Content moderation queue — flagged content held for review

### Phase 1 — Safety Core
- [x] Input sanitization / XSS prevention
- [x] Brute force protection — lockout after failed login attempts
- [ ] Rate limiting on registration — prevent bot account creation
- [ ] Session timeout — auto-logout after inactivity for shared school computers
- [ ] Report system — flag posts/users for moderation review
- [ ] Content moderation queue — hold flagged content for review before visible
- [ ] User blocking — filter content from blocked users
- [ ] Age-appropriate content filtering — baseline keyword/content rules
- [ ] COPPA compliance — Terms of Service and Privacy Policy pages (legally required for minors)

### Phase 2 — Trust & Verification
- [ ] Email verification on register
- [ ] Admin dashboard — proper moderation UI, not just CLI tools
- [ ] Parent dashboard — visibility into student activity
- [ ] Teacher pages — dedicated hosted pages for educators
- [ ] Class/group channels — private spaces for classrooms
- [ ] Topic moderators — role-based permissions per topic
- [ ] School/district accounts — umbrella accounts managing multiple teacher pages

### Phase 3 — Growth & Engagement
- [ ] Onboarding flow — guide new users to follow topics and people on first login
- [ ] User mentions — @username triggers a notification
- [ ] Achievement badges — lightweight engagement without dark patterns
- [ ] Direct messages — teacher↔student only initially, not peer-to-peer
- [ ] Landing page — public-facing marketing site
- [ ] Data export — users can download their own data
- [ ] Trending algorithm — weight posts by votes, reply count, and time decay

### Phase 4 — Ops & Hardening
- [ ] Full audit log — track all data changes with who/when/what
- [ ] Structured logging — replace print statements with proper log levels
- [ ] Health check endpoint — /health returns app and DB status
- [ ] Database backups — scheduled backup script with rotation
- [ ] Dependency vulnerability scanning — pip-audit in CI pipeline
- [ ] Feature flags — toggle features on/off without deploying