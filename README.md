# ⬡ Devstack

A safe, moderated social and community platform for students, kids, and educators.
Built with Flask, SQLite, and Docker.

> This started as a developer forum and is evolving into something more meaningful —
> a space where young people can connect, learn, and participate online safely.

## Vision

Most social platforms are built for engagement, not safety. Devstack is being rebuilt
around the opposite priority: a community where students and kids can post, discuss,
and interact — and where educators and parents can trust the environment they're in.

Safety and moderation aren't afterthoughts here. They're the foundation.

## Features
- Post, reply, vote, and bookmark in topic channels
- Follow other users and get a personalized feed
- Full-text search across posts and topics
- Real-time notifications via WebSockets
- Role-based access (admins, moderators, users)
- Rate limiting and CSRF protection built in
- Bcrypt password hashing
- REST API

## Who It's For
- **Students** — a structured space to discuss, ask questions, and share
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
git clone https://github.com/onederlnd/devstack.git
cd devstack

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
devstack/
├── app/
│   ├── __init__.py        # app factory
│   ├── models/            # database access
│   ├── routes/            # flask blueprints
│   ├── templates/         # jinja2 templates
│   └── static/            # css and js
├── tests/                 # pytest test suite
├── scripts/               # dev workflow scripts
├── Dockerfile
├── docker-compose.yml
└── run.py
```

## CI
GitHub Actions runs tests and linting on every push. See `.github/workflows/ci.yml`.

## Roadmap
- [ ] Report system — flag posts/users for moderation review
- [ ] Feature flags — toggle features on/off without deploying
- [ ] Full audit log — track all data changes with who/when/what
- [ ] User mentions — @username triggers a notification
- [ ] User blocking — filter content from blocked users
- [ ] Brute force protection — lockout after failed login attempts
- [ ] Input sanitization / XSS prevention
- [ ] Email verification on register
- [ ] Data export — users can download their own data
- [ ] Topic moderators — role-based permissions per topic