import os
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from app.models import get_db

ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "txt",
    "csv",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file
MAX_ASSIGNMENT_TOTAL = 50 * 1024 * 1024  # 50MB per assignment
MAX_SUBMISSION_TOTAL = 20 * 1024 * 1024  # 20MB per submission


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_dir(app):
    path = os.path.join(app.root_path, "..", "uploads")
    os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)


def save_file(file, subfolder, app):
    """Save an uploaded file, return the stored filename. Raises ValueError if file is invalid or too large."""
    if not file or not file.filename:
        raise ValueError("No file provided")
    if not allowed_file(file.filename):
        raise ValueError(
            f"File type not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    if size == 0:
        raise ValueError("File is empty")

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"

    folder = os.path.join(get_upload_dir(app), subfolder)
    os.makedirs(folder, exist_ok=True)

    file.save(os.path.join(folder, stored_filename))

    mime_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"

    return stored_filename, original_filename, size, mime_type


def delete_file(filename, subfolder, app):
    path = os.path.join(get_upload_dir(app), subfolder, filename)
    if os.path.exists(path):
        os.remove(path)


# --- assignment attachments
def get_assignment_attachments(assignment_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM assignment_attachments WHERE assignment_id = ? ORDER BY created_at ASC",
        (assignment_id,),
    ).fetchall()


def add_assignment_attachment(assignment_id, file, uploaded_by, app):
    existing = get_assignment_attachments(assignment_id)
    total = sum(a["file_size"] for a in existing)
    if total >= MAX_ASSIGNMENT_TOTAL:
        raise ValueError("Assignment attachment list reached (50MB total)")

    stored, original, size, mime = save_file(file, f"assignments/{assignment_id}", app)

    db = get_db()
    db.execute(
        """
        INSERT INTO assignment_attachments
        (assignment_id, filename, original_filename, uploaded_by, file_size, mime_type)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (assignment_id, stored, original, uploaded_by, size, mime),
    )
    db.commit()
    return stored


def delete_assignment_attachment(attachment_id, app):
    db = get_db()
    row = db.execute(
        "SELECT * FROM assignment_attachments WHERE id = ?", (attachment_id,)
    ).fetchone()
    if not row:
        return False
    delete_file(row["filename"], f"assignments/{row['assignment_id']}", app)
    db.execute("DELETE FROM assignment_attachments WHERE id = ?", (attachment_id,))
    db.commit()
    return True


# --- submission attachments


def get_submission_attachments(submission_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM submission_attachments WHERE submission_id = ? ORDER BY created_at ASC",
        (submission_id,),
    ).fetchall()


def add_submission_attachment(submission_id, file, uploaded_by, app):
    existing = get_submission_attachments(submission_id)
    total = sum(a["file_size"] for a in existing)
    if total >= MAX_SUBMISSION_TOTAL:
        raise ValueError("Submission attachment limit reached (20MB total)")

    stored, original, size, mime = save_file(file, f"submissions/{submission_id}", app)

    db = get_db()
    db.execute(
        """
        INSERT INTO submission_attachments
        (submission_id, filename, original_filename, uploaded_by, file_size, mime_type)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (submission_id, stored, original, uploaded_by, size, mime),
    )
    db.commit()
    return stored


def delete_submission_attachment(attachment_id, app):
    db = get_db()
    row = db.execute(
        "SELECT * FROM submission_attachments WHERE id = ?", (attachment_id,)
    ).fetchone()
    if not row:
        return False
    delete_file(row["filename"], f"submissions/{row['submission_id']}", app)
    db.execute("DELETE FROM submission_attachments WHERE id = ?", (attachment_id,))
    db.commit()
    return True
