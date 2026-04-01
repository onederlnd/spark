import click
from app.models import get_db


def register_commands(app):
    @app.cli.command("set-role")
    @click.argument("username")
    @click.argument("role")
    def set_role(username, role):
        if role not in ("teacher", "student", "admin"):
            click.echo("Invalid role")
            return
        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user:
            click.echo("User not found")
            return
        db.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        db.commit()
        click.echo(f"Updated {username} to {role}")
