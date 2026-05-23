import time
import pytest
from unittest.mock import MagicMock, patch


def _add_billing_columns(app):
    with app.app_context():
        from app.models import get_db

        db = get_db()
        for table, col, definition in [
            ("users", "sub_status", "TEXT NOT NULL DEFAULT 'free'"),
            ("users", "sub_stripe_customer_id", "TEXT"),
            ("users", "sub_stripe_subscription_id", "TEXT"),
            ("users", "sub_price_id", "TEXT"),
            ("users", "sub_current_period_end", "INTEGER"),
            ("organizations", "sub_status", "TEXT NOT NULL DEFAULT 'free'"),
            ("organizations", "sub_stripe_customer_id", "TEXT"),
            ("organizations", "sub_stripe_subscription_id", "TEXT"),
            ("organizations", "sub_price_id", "TEXT"),
            ("organizations", "sub_current_period_end", "INTEGER"),
        ]:
            try:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
            except Exception:
                pass
        db.commit()


def _make_billing_teacher(app, client, suffix=""):
    import bcrypt

    username = f"teacher.test.teacher{suffix}"
    with app.app_context():
        from app.models import get_db

        pw = bcrypt.hashpw(b"pass123", bcrypt.gensalt(rounds=4)).decode()
        db = get_db()
        db.execute(
            """INSERT INTO users
               (username, password_hash, dob, bio, role, coppa_status, onboarded,
                display_name, email)
               VALUES (?, ?, '1985-01-01', '', 'teacher', 'approved', 1, ?, ?)""",
            (username, pw, "Test Teacher", f"teacher{suffix}@school.edu"),
        )
        db.commit()
        user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    resp = client.post(
        "/auth/login", data={"username": username, "password": "pass123"}
    )
    assert resp.status_code == 302, f"teacher login failed (status {resp.status_code})"
    return user_id


def _make_org_and_admin(app, client, suffix=""):
    import bcrypt

    username = f"orgadmin{suffix}"
    with app.app_context():
        from app.models import get_db

        pw = bcrypt.hashpw(b"pass123", bcrypt.gensalt(rounds=4)).decode()
        db = get_db()

        # 1. Insert user first (no org_id yet)
        db.execute(
            """INSERT INTO users
               (username, password_hash, dob, bio, role, coppa_status, onboarded,
                display_name, email)
               VALUES (?, ?, '1980-01-01', '', 'org_admin', 'approved', 1, ?, ?)""",
            (username, pw, f"Org Admin{suffix}", f"org{suffix}@school.edu"),
        )
        db.commit()
        user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 2. Now create org with a valid created_by
        db.execute(
            "INSERT INTO organizations (name, billing_email, created_by) VALUES (?, ?, ?)",
            (f"Test Org {suffix}", f"org{suffix}@school.edu", user_id),
        )
        db.commit()
        org_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 3. Link user back to org
        db.execute("UPDATE users SET org_id = ? WHERE id = ?", (org_id, user_id))
        db.commit()

    resp = client.post(
        "/auth/login", data={"username": username, "password": "pass123"}
    )
    print(resp.data[:500])
    assert resp.status_code == 302, (
        f"org_admin login failed (status {resp.status_code}). "
        "Check the INSERT matches all fields the login route requires."
    )
    return org_id


def _set_teacher_sub(
    app, user_id, status, customer_id=None, sub_id=None, period_end=None
):
    with app.app_context():
        from app.models import get_db

        db = get_db()
        db.execute(
            """UPDATE users SET sub_status=?, sub_stripe_customer_id=?,
               sub_stripe_subscription_id=?, sub_current_period_end=? WHERE id=?""",
            (status, customer_id, sub_id, period_end, user_id),
        )
        db.commit()


def _set_org_sub(app, org_id, status, customer_id=None, sub_id=None, period_end=None):
    with app.app_context():
        from app.models import get_db

        db = get_db()
        db.execute(
            """UPDATE organizations SET sub_status=?, sub_stripe_customer_id=?,
               sub_stripe_subscription_id=?, sub_current_period_end=? WHERE id=?""",
            (status, customer_id, sub_id, period_end, org_id),
        )
        db.commit()


def _post_webhook(client, event, sig="valid_sig"):
    import json

    return client.post(
        "/billing/webhook",
        data=json.dumps(event),
        content_type="application/json",
        headers={"Stripe-Signature": sig},
    )


def _stripe_event(event_type, data):
    return {"type": event_type, "data": {"object": data}}


@pytest.fixture()
def billing_app(app):
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["WTF_CSRF_CHECK_DEFAULT"] = False
    _add_billing_columns(app)
    return app


@pytest.fixture()
def billing_teacher_client(billing_app):
    import uuid

    client = billing_app.test_client()
    suffix = uuid.uuid4().hex[:8]
    user_id = _make_billing_teacher(billing_app, client, suffix=suffix)
    return client, user_id


@pytest.fixture()
def org_admin_client(billing_app):
    import uuid

    client = billing_app.test_client()
    suffix = uuid.uuid4().hex[:8]
    org_id = _make_org_and_admin(billing_app, client, suffix=suffix)
    return client, org_id


@pytest.fixture()
def student_only_client(billing_app):
    client = billing_app.test_client()
    client.post(
        "/auth/register",
        data={
            "username": "billing_student",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    client.post(
        "/auth/login", data={"username": "billing_student", "password": "pass123"}
    )
    return client


def test_get_teacher_sub_defaults_free(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    with billing_app.app_context():
        from app.models.billing import get_teacher_sub

        sub = get_teacher_sub(user_id)
        assert sub["sub_status"] == "free"
        assert sub["sub_stripe_customer_id"] is None


def test_set_teacher_sub_updates_all_fields(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    with billing_app.app_context():
        from app.models.billing import set_teacher_sub, get_teacher_sub

        set_teacher_sub(
            user_id,
            "active",
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            price_id="price_pro",
            current_period_end=9999999999,
        )
        sub = get_teacher_sub(user_id)
        assert sub["sub_status"] == "active"
        assert sub["sub_stripe_customer_id"] == "cus_123"
        assert sub["sub_stripe_subscription_id"] == "sub_123"
        assert sub["sub_price_id"] == "price_pro"
        assert sub["sub_current_period_end"] == 9999999999


def test_set_teacher_sub_coalesce_preserves_existing_customer_id(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    with billing_app.app_context():
        from app.models.billing import set_teacher_sub, get_teacher_sub

        set_teacher_sub(user_id, "active", stripe_customer_id="cus_original")
        set_teacher_sub(user_id, "past_due", stripe_customer_id=None)
        sub = get_teacher_sub(user_id)
        assert sub["sub_stripe_customer_id"] == "cus_original"


def test_cancel_teacher_sub_clears_sub_fields(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    with billing_app.app_context():
        from app.models.billing import (
            set_teacher_sub,
            cancel_teacher_sub,
            get_teacher_sub,
        )

        set_teacher_sub(
            user_id,
            "active",
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )
        cancel_teacher_sub(user_id)
        sub = get_teacher_sub(user_id)
        assert sub["sub_status"] == "canceled"
        assert sub["sub_stripe_subscription_id"] is None
        assert sub["sub_price_id"] is None


def test_get_org_sub_defaults_free(billing_app, org_admin_client):
    client, org_id = org_admin_client
    with billing_app.app_context():
        from app.models.billing import get_org_sub

        sub = get_org_sub(org_id)
        assert sub["sub_status"] == "free"


def test_set_org_sub_updates_all_fields(billing_app, org_admin_client):
    client, org_id = org_admin_client
    with billing_app.app_context():
        from app.models.billing import set_org_sub, get_org_sub

        set_org_sub(
            org_id,
            "active",
            stripe_customer_id="cus_org",
            stripe_subscription_id="sub_org",
            price_id="price_org",
            current_period_end=9999999999,
        )
        sub = get_org_sub(org_id)
        assert sub["sub_status"] == "active"
        assert sub["sub_stripe_customer_id"] == "cus_org"
        assert sub["sub_stripe_subscription_id"] == "sub_org"
        assert sub["sub_price_id"] == "price_org"


def test_cancel_org_sub_clears_sub_fields(billing_app, org_admin_client):
    client, org_id = org_admin_client
    with billing_app.app_context():
        from app.models.billing import set_org_sub, cancel_org_sub, get_org_sub

        set_org_sub(
            org_id,
            "active",
            stripe_customer_id="cus_org",
            stripe_subscription_id="sub_org",
        )
        cancel_org_sub(org_id)
        sub = get_org_sub(org_id)
        assert sub["sub_status"] == "canceled"
        assert sub["sub_stripe_subscription_id"] is None


def test_get_user_by_stripe_customer_returns_correct_user(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    _set_teacher_sub(billing_app, user_id, "active", customer_id="cus_lookup")
    with billing_app.app_context():
        from app.models.billing import get_user_by_stripe_customer

        user = get_user_by_stripe_customer("cus_lookup")
        assert user is not None
        assert user["id"] == user_id


def test_get_user_by_stripe_customer_returns_none_when_not_found(billing_app):
    with billing_app.app_context():
        from app.models.billing import get_user_by_stripe_customer

        assert get_user_by_stripe_customer("cus_nobody") is None


def test_get_org_by_stripe_customer_returns_correct_org(billing_app, org_admin_client):
    client, org_id = org_admin_client
    _set_org_sub(billing_app, org_id, "active", customer_id="cus_org_lookup")
    with billing_app.app_context():
        from app.models.billing import get_org_by_stripe_customer

        org = get_org_by_stripe_customer("cus_org_lookup")
        assert org is not None
        assert org["id"] == org_id


def test_get_org_by_stripe_customer_returns_none_when_not_found(billing_app):
    with billing_app.app_context():
        from app.models.billing import get_org_by_stripe_customer

        assert get_org_by_stripe_customer("cus_nobody") is None


def test_has_access_freemium_on_allows_free_teacher(billing_app):
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {"sub_status": "free", "sub_current_period_end": None, "org_id": None}
        assert teacher_has_access(user, freemium_enabled=True) is True


def test_has_access_freemium_on_allows_canceled_teacher(billing_app):
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {
            "sub_status": "canceled",
            "sub_current_period_end": None,
            "org_id": None,
        }
        assert teacher_has_access(user, freemium_enabled=True) is True


def test_has_access_freemium_off_free_denied(billing_app):
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {"sub_status": "free", "sub_current_period_end": None, "org_id": None}
        assert teacher_has_access(user, freemium_enabled=False) is False


def test_has_access_freemium_off_canceled_denied(billing_app):
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {
            "sub_status": "canceled",
            "sub_current_period_end": None,
            "org_id": None,
        }
        assert teacher_has_access(user, freemium_enabled=False) is False


def test_has_access_freemium_off_active_sub_granted(billing_app):
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {
            "sub_status": "active",
            "sub_current_period_end": int(time.time()) + 86400,
            "org_id": None,
        }
        assert teacher_has_access(user, freemium_enabled=False) is True


def test_has_access_freemium_off_trialing_granted(billing_app):
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {
            "sub_status": "trialing",
            "sub_current_period_end": int(time.time()) + 86400,
            "org_id": None,
        }
        assert teacher_has_access(user, freemium_enabled=False) is True


def test_has_access_freemium_off_past_due_granted(billing_app):
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {
            "sub_status": "past_due",
            "sub_current_period_end": int(time.time()) + 86400,
            "org_id": None,
        }
        assert teacher_has_access(user, freemium_enabled=False) is True


def test_has_access_freemium_off_expired_period_end_denied(billing_app):
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {
            "sub_status": "active",
            "sub_current_period_end": int(time.time()) - 1,
            "org_id": None,
        }
        assert teacher_has_access(user, freemium_enabled=False) is False


def test_has_access_freemium_off_active_org_sub_grants_teacher(
    billing_app, org_admin_client
):
    client, org_id = org_admin_client
    _set_org_sub(billing_app, org_id, "active", period_end=int(time.time()) + 86400)
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {"sub_status": "free", "sub_current_period_end": None, "org_id": org_id}
        assert teacher_has_access(user, freemium_enabled=False) is True


def test_has_access_freemium_off_expired_org_sub_denies_teacher(
    billing_app, org_admin_client
):
    client, org_id = org_admin_client
    _set_org_sub(billing_app, org_id, "active", period_end=int(time.time()) - 1)
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {"sub_status": "free", "sub_current_period_end": None, "org_id": org_id}
        assert teacher_has_access(user, freemium_enabled=False) is False


def test_has_access_freemium_off_free_org_denies_teacher(billing_app, org_admin_client):
    client, org_id = org_admin_client
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {"sub_status": "free", "sub_current_period_end": None, "org_id": org_id}
        assert teacher_has_access(user, freemium_enabled=False) is False


def test_has_access_active_personal_sub_beats_free_org(billing_app, org_admin_client):
    client, org_id = org_admin_client
    with billing_app.app_context():
        from app.models.billing import teacher_has_access

        user = {
            "sub_status": "active",
            "sub_current_period_end": int(time.time()) + 86400,
            "org_id": org_id,
        }
        assert teacher_has_access(user, freemium_enabled=False) is True


def test_subscription_required_passes_when_freemium_on(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    with billing_app.app_context():
        from app.models.billing import teacher_has_access
        from app.models.user import get_user_by_id

        user = get_user_by_id(user_id)
        assert teacher_has_access(user, freemium_enabled=True) is True


def test_subscription_required_blocks_when_freemium_off_no_sub(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    with billing_app.app_context():
        from app.models.billing import teacher_has_access
        from app.models.user import get_user_by_id

        user = get_user_by_id(user_id)
        assert teacher_has_access(user, freemium_enabled=False) is False


def test_subscription_required_passes_when_freemium_off_active_sub(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    _set_teacher_sub(
        billing_app,
        user_id,
        "active",
        customer_id="cus_x",
        sub_id="sub_x",
        period_end=int(time.time()) + 86400,
    )
    with billing_app.app_context():
        from app.models.billing import teacher_has_access
        from app.models.user import get_user_by_id

        user = get_user_by_id(user_id)
        assert teacher_has_access(user, freemium_enabled=False) is True


def test_freemium_false_blocks_free_teacher_via_model(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    with billing_app.app_context():
        from app.models.billing import teacher_has_access
        from app.models.user import get_user_by_id

        user = get_user_by_id(user_id)
        assert teacher_has_access(user, freemium_enabled=False) is False


def test_freemium_true_allows_free_teacher_via_model(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    with billing_app.app_context():
        from app.models.billing import teacher_has_access
        from app.models.user import get_user_by_id

        user = get_user_by_id(user_id)
        assert teacher_has_access(user, freemium_enabled=True) is True


def test_freemium_false_allows_paid_teacher_via_model(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    _set_teacher_sub(
        billing_app,
        user_id,
        "active",
        customer_id="cus_paid",
        sub_id="sub_paid",
        period_end=int(time.time()) + 86400,
    )
    with billing_app.app_context():
        from app.models.billing import teacher_has_access
        from app.models.user import get_user_by_id

        user = get_user_by_id(user_id)
        assert teacher_has_access(user, freemium_enabled=False) is True


def test_freemium_enabled_true_by_default(billing_app):
    assert billing_app.config.get("FREEMIUM_ENABLED", True) is True


def test_freemium_can_be_set_false(billing_app):
    billing_app.config["FREEMIUM_ENABLED"] = False
    assert billing_app.config["FREEMIUM_ENABLED"] is False


def test_plan_page_requires_login(billing_app):
    c = billing_app.test_client()
    response = c.get("/billing/plan", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_plan_page_blocked_for_non_teacher(billing_app, student_only_client):
    response = student_only_client.get("/billing/plan")
    assert response.status_code in (302, 403)


def test_plan_page_loads_for_teacher(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    response = client.get("/billing/plan")
    assert response.status_code == 200
    assert b"Subscription" in response.data


def test_plan_page_shows_free_status(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    response = client.get("/billing/plan")
    assert b"Free" in response.data


def test_plan_page_shows_active_status(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    _set_teacher_sub(
        billing_app,
        user_id,
        "active",
        customer_id="cus_1",
        sub_id="sub_1",
        period_end=int(time.time()) + 86400,
    )
    response = client.get("/billing/plan")
    assert b"Active" in response.data


def test_plan_page_shows_past_due_status(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    _set_teacher_sub(billing_app, user_id, "past_due", customer_id="cus_1")
    response = client.get("/billing/plan")
    assert b"Past Due" in response.data


def test_plan_page_shows_portal_link_when_customer_exists(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    _set_teacher_sub(billing_app, user_id, "active", customer_id="cus_1")
    response = client.get("/billing/plan")
    assert b"/billing/portal" in response.data


def test_plan_page_hides_portal_link_when_no_customer(
    billing_app, billing_teacher_client
):
    client, _ = billing_teacher_client
    response = client.get("/billing/plan")
    assert b"/billing/portal" not in response.data


def test_plan_page_shows_upgrade_button_when_free(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    response = client.get("/billing/plan")
    assert b"Upgrade to Pro" in response.data


def test_plan_page_shows_current_plan_when_active(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    _set_teacher_sub(
        billing_app,
        user_id,
        "active",
        customer_id="cus_1",
        sub_id="sub_1",
        period_end=int(time.time()) + 86400,
    )
    response = client.get("/billing/plan")
    assert b"Current plan" in response.data


def test_checkout_requires_login(billing_app):
    c = billing_app.test_client()
    response = c.get("/billing/checkout/pro", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_checkout_blocked_for_non_teacher(billing_app, student_only_client):
    response = student_only_client.get("/billing/checkout/pro")
    assert response.status_code in (302, 403)


def test_checkout_invalid_plan_redirects_to_plan(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    billing_app.config["STRIPE_PRICE_PRO"] = "price_pro_test"
    response = client.get("/billing/checkout/nonexistent", follow_redirects=False)
    assert response.status_code == 302
    assert "/billing/plan" in response.headers["Location"]


def test_checkout_missing_price_id_redirects_to_plan(
    billing_app, billing_teacher_client
):
    client, _ = billing_teacher_client
    billing_app.config["STRIPE_PRICE_PRO"] = ""
    response = client.get("/billing/checkout/pro", follow_redirects=False)
    assert response.status_code == 302
    assert "/billing/plan" in response.headers["Location"]


def test_checkout_pro_redirects_to_stripe(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    billing_app.config["STRIPE_PRICE_PRO"] = "price_pro_test"
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test"
    with patch("app.routes.billing.create_checkout_session", return_value=mock_session):
        response = client.get("/billing/checkout/pro", follow_redirects=False)
        assert response.status_code == 303
        assert "stripe.com" in response.headers["Location"]


def test_checkout_org_redirects_to_stripe(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    billing_app.config["STRIPE_PRICE_ORG"] = "price_org_test"
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test_org"
    with patch("app.routes.billing.create_checkout_session", return_value=mock_session):
        response = client.get("/billing/checkout/org", follow_redirects=False)
        assert response.status_code == 303


def test_checkout_passes_correct_user_metadata(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    billing_app.config["STRIPE_PRICE_PRO"] = "price_pro_test"
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test"
    with patch(
        "app.routes.billing.create_checkout_session", return_value=mock_session
    ) as mock_checkout:
        client.get("/billing/checkout/pro")
        call_kwargs = mock_checkout.call_args.kwargs
        assert call_kwargs["metadata"]["user_id"] == str(user_id)
        assert call_kwargs["metadata"]["plan"] == "pro"


def test_checkout_reuses_existing_stripe_customer_id(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    billing_app.config["STRIPE_PRICE_PRO"] = "price_pro_test"
    _set_teacher_sub(billing_app, user_id, "canceled", customer_id="cus_returning")
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test"
    with patch(
        "app.routes.billing.create_checkout_session", return_value=mock_session
    ) as mock_checkout:
        client.get("/billing/checkout/pro")
        call_kwargs = mock_checkout.call_args.kwargs
        assert call_kwargs["existing_customer_id"] == "cus_returning"


def test_checkout_stripe_error_redirects_with_flash(
    billing_app, billing_teacher_client
):
    client, _ = billing_teacher_client
    billing_app.config["STRIPE_PRICE_PRO"] = "price_pro_test"
    with patch(
        "app.routes.billing.create_checkout_session",
        side_effect=Exception("Stripe down"),
    ):
        response = client.get("/billing/checkout/pro", follow_redirects=True)
        assert b"wrong" in response.data.lower() or b"error" in response.data.lower()


def test_portal_requires_login(billing_app):
    c = billing_app.test_client()
    response = c.get("/billing/portal", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_portal_no_customer_redirects_with_flash(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    response = client.get("/billing/portal", follow_redirects=True)
    assert b"No active subscription" in response.data


def test_portal_redirects_to_stripe(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    _set_teacher_sub(billing_app, user_id, "active", customer_id="cus_portal")
    mock_portal = MagicMock()
    mock_portal.url = "https://billing.stripe.com/portal/test"
    with patch(
        "app.routes.billing.create_billing_portal_session", return_value=mock_portal
    ):
        response = client.get("/billing/portal", follow_redirects=False)
        assert response.status_code == 303
        assert "stripe.com" in response.headers["Location"]


def test_portal_stripe_error_redirects_with_flash(billing_app, billing_teacher_client):
    client, user_id = billing_teacher_client
    _set_teacher_sub(billing_app, user_id, "active", customer_id="cus_portal")
    with patch(
        "app.routes.billing.create_billing_portal_session",
        side_effect=Exception("Stripe error"),
    ):
        response = client.get("/billing/portal", follow_redirects=True)
        assert (
            b"error" in response.data.lower() or b"try again" in response.data.lower()
        )


def test_success_page_requires_login(billing_app):
    c = billing_app.test_client()
    response = c.get("/billing/success", follow_redirects=False)
    assert response.status_code == 302


def test_success_page_loads_for_teacher(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    response = client.get("/billing/success")
    assert response.status_code == 200
    assert b"set" in response.data.lower() or b"active" in response.data.lower()


def test_canceled_page_requires_login(billing_app):
    c = billing_app.test_client()
    response = c.get("/billing/canceled", follow_redirects=False)
    assert response.status_code == 302


def test_canceled_page_loads_for_teacher(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    response = client.get("/billing/canceled")
    assert response.status_code == 200
    assert b"charged" in response.data.lower() or b"changes" in response.data.lower()


def test_webhook_bad_signature_returns_400(billing_app):
    import stripe

    c = billing_app.test_client()
    with patch(
        "app.routes.billing.construct_webhook_event",
        side_effect=stripe.error.SignatureVerificationError("bad sig", "sig"),
    ):
        response = _post_webhook(c, {})
        assert response.status_code == 400


def test_webhook_unknown_event_type_ignored(billing_app):
    c = billing_app.test_client()
    event = _stripe_event("payment_intent.created", {"customer": "cus_x"})
    with patch("app.routes.billing.construct_webhook_event", return_value=event):
        response = _post_webhook(c, event)
        assert response.status_code == 200


def test_webhook_unknown_customer_returns_200(billing_app):
    c = billing_app.test_client()
    event = _stripe_event("customer.subscription.deleted", {"customer": "cus_nobody"})
    with patch("app.routes.billing.construct_webhook_event", return_value=event):
        response = _post_webhook(c, event)
        assert response.status_code == 200


def test_webhook_checkout_completed_sets_customer_id(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    mock_sub = MagicMock()
    mock_sub.__getitem__ = lambda self, k: {
        "status": "active",
        "current_period_end": 9999999999,
        "items": {"data": [{"price": {"id": "price_pro"}}]},
    }[k]
    event = _stripe_event(
        "checkout.session.completed",
        {
            "metadata": {"user_id": str(user_id), "plan": "pro"},
            "customer": "cus_new",
            "subscription": "sub_new",
        },
    )
    with (
        patch("app.routes.billing.construct_webhook_event", return_value=event),
        patch("app.routes.billing.retrieve_subscription", return_value=mock_sub),
    ):
        response = _post_webhook(client, event)
        assert response.status_code == 200
    with billing_app.app_context():
        from app.models.billing import get_teacher_sub

        assert get_teacher_sub(user_id)["sub_stripe_customer_id"] == "cus_new"


def test_webhook_subscription_updated_sets_past_due_on_teacher(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    _set_teacher_sub(billing_app, user_id, "active", customer_id="cus_upd")
    event = _stripe_event(
        "customer.subscription.updated",
        {
            "customer": "cus_upd",
            "status": "past_due",
            "current_period_end": 9999999999,
            "id": "sub_upd",
            "items": {"data": [{"price": {"id": "price_pro"}}]},
        },
    )
    with patch("app.routes.billing.construct_webhook_event", return_value=event):
        print(billing_app.config["DATABASE_URL"])
        assert _post_webhook(client, event).status_code == 200

    with billing_app.app_context():
        from app.models.billing import get_teacher_sub

        assert get_teacher_sub(user_id)["sub_status"] == "past_due"


def test_webhook_subscription_updated_sets_past_due_on_org(
    billing_app, org_admin_client
):
    client, org_id = org_admin_client
    _set_org_sub(billing_app, org_id, "active", customer_id="cus_org_upd")
    event = _stripe_event(
        "customer.subscription.updated",
        {
            "customer": "cus_org_upd",
            "status": "past_due",
            "current_period_end": 9999999999,
            "id": "sub_org_upd",
            "items": {"data": [{"price": {"id": "price_org"}}]},
        },
    )
    with patch("app.routes.billing.construct_webhook_event", return_value=event):
        assert _post_webhook(client, event).status_code == 200
    with billing_app.app_context():
        from app.models.billing import get_org_sub

        assert get_org_sub(org_id)["sub_status"] == "past_due"


def test_webhook_subscription_deleted_cancels_teacher(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    _set_teacher_sub(
        billing_app, user_id, "active", customer_id="cus_del", sub_id="sub_del"
    )
    event = _stripe_event("customer.subscription.deleted", {"customer": "cus_del"})
    with patch("app.routes.billing.construct_webhook_event", return_value=event):
        _post_webhook(client, event)
    with billing_app.app_context():
        from app.models.billing import get_teacher_sub

        sub = get_teacher_sub(user_id)
        assert sub["sub_status"] == "canceled"
        assert sub["sub_stripe_subscription_id"] is None


def test_webhook_subscription_deleted_cancels_org(billing_app, org_admin_client):
    client, org_id = org_admin_client
    _set_org_sub(
        billing_app, org_id, "active", customer_id="cus_org_del", sub_id="sub_org_del"
    )
    event = _stripe_event("customer.subscription.deleted", {"customer": "cus_org_del"})
    with patch("app.routes.billing.construct_webhook_event", return_value=event):
        _post_webhook(client, event)
    with billing_app.app_context():
        from app.models.billing import get_org_sub

        assert get_org_sub(org_id)["sub_status"] == "canceled"


def test_webhook_invoice_payment_failed_marks_teacher_past_due(
    billing_app, billing_teacher_client
):
    client, user_id = billing_teacher_client
    _set_teacher_sub(billing_app, user_id, "active", customer_id="cus_fail")
    event = _stripe_event("invoice.payment_failed", {"customer": "cus_fail"})
    with patch("app.routes.billing.construct_webhook_event", return_value=event):
        _post_webhook(client, event)
    with billing_app.app_context():
        from app.models.billing import get_teacher_sub

        assert get_teacher_sub(user_id)["sub_status"] == "past_due"


def test_webhook_invoice_payment_failed_marks_org_past_due(
    billing_app, org_admin_client
):
    client, org_id = org_admin_client
    _set_org_sub(billing_app, org_id, "active", customer_id="cus_org_fail")
    event = _stripe_event("invoice.payment_failed", {"customer": "cus_org_fail"})
    with patch("app.routes.billing.construct_webhook_event", return_value=event):
        _post_webhook(client, event)
    with billing_app.app_context():
        from app.models.billing import get_org_sub

        assert get_org_sub(org_id)["sub_status"] == "past_due"


def test_org_billing_page_requires_login(billing_app):
    c = billing_app.test_client()
    response = c.get("/org/billing", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_org_billing_page_blocked_for_teacher(billing_app, billing_teacher_client):
    client, _ = billing_teacher_client
    response = client.get("/org/billing")
    assert response.status_code == 403


def test_org_billing_page_loads_for_org_admin(billing_app, org_admin_client):
    client, _ = org_admin_client
    response = client.get("/org/billing")
    assert response.status_code == 200
    assert b"Billing" in response.data


def test_org_billing_page_shows_free_status(billing_app, org_admin_client):
    client, _ = org_admin_client
    response = client.get("/org/billing")
    assert b"Free" in response.data or b"Upgrade" in response.data


def test_org_billing_page_shows_active_status(billing_app, org_admin_client):
    client, org_id = org_admin_client
    _set_org_sub(
        billing_app,
        org_id,
        "active",
        customer_id="cus_view",
        period_end=int(time.time()) + 86400,
    )
    response = client.get("/org/billing")
    assert b"Active" in response.data


def test_org_billing_page_shows_past_due(billing_app, org_admin_client):
    client, org_id = org_admin_client
    _set_org_sub(billing_app, org_id, "past_due", customer_id="cus_overdue")
    response = client.get("/org/billing")
    assert b"Past Due" in response.data or b"payment" in response.data.lower()


def test_org_checkout_missing_price_id_redirects(billing_app, org_admin_client):
    client, _ = org_admin_client
    billing_app.config["STRIPE_PRICE_ORG"] = ""
    response = client.get("/org/billing/checkout", follow_redirects=True)
    assert b"configured" in response.data or b"error" in response.data.lower()


def test_org_checkout_redirects_to_stripe(billing_app, org_admin_client):
    client, _ = org_admin_client
    billing_app.config["STRIPE_PRICE_ORG"] = "price_org_test"
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/org_test"
    with patch(
        "app.routes.org_admin.create_checkout_session", return_value=mock_session
    ):
        response = client.get("/org/billing/checkout", follow_redirects=False)
        assert response.status_code == 303
        assert "stripe.com" in response.headers["Location"]


def test_org_checkout_passes_org_id_in_metadata(billing_app, org_admin_client):
    client, org_id = org_admin_client
    billing_app.config["STRIPE_PRICE_ORG"] = "price_org_test"
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/org_test"
    with patch(
        "app.routes.org_admin.create_checkout_session", return_value=mock_session
    ) as mock_checkout:
        client.get("/org/billing/checkout")
        call_kwargs = mock_checkout.call_args.kwargs
        assert call_kwargs["metadata"]["org_id"] == str(org_id)


def test_org_checkout_stripe_error_flashes(billing_app, org_admin_client):
    client, _ = org_admin_client
    billing_app.config["STRIPE_PRICE_ORG"] = "price_org_test"
    with patch(
        "app.routes.org_admin.create_checkout_session",
        side_effect=Exception("Stripe down"),
    ):
        response = client.get("/org/billing/checkout", follow_redirects=True)
        assert (
            b"error" in response.data.lower() or b"try again" in response.data.lower()
        )


def test_org_portal_no_customer_redirects_with_flash(billing_app, org_admin_client):
    client, _ = org_admin_client
    response = client.get("/org/billing/portal", follow_redirects=True)
    assert b"No active subscription" in response.data


def test_org_portal_redirects_to_stripe(billing_app, org_admin_client):
    client, org_id = org_admin_client
    _set_org_sub(billing_app, org_id, "active", customer_id="cus_org_portal")
    mock_portal = MagicMock()
    mock_portal.url = "https://billing.stripe.com/portal/org"
    with patch(
        "app.routes.org_admin.create_billing_portal_session", return_value=mock_portal
    ):
        response = client.get("/org/billing/portal", follow_redirects=False)
        assert response.status_code == 303
        assert "stripe.com" in response.headers["Location"]


def test_org_portal_stripe_error_flashes(billing_app, org_admin_client):
    client, org_id = org_admin_client
    _set_org_sub(billing_app, org_id, "active", customer_id="cus_org_portal")
    with patch(
        "app.routes.org_admin.create_billing_portal_session",
        side_effect=Exception("Stripe error"),
    ):
        response = client.get("/org/billing/portal", follow_redirects=True)
        assert (
            b"error" in response.data.lower() or b"try again" in response.data.lower()
        )


def test_pricing_page_loads(billing_app):
    c = billing_app.test_client()
    response = c.get("/pricing")
    assert response.status_code == 200


def test_pricing_page_shows_all_three_tiers(billing_app):
    c = billing_app.test_client()
    response = c.get("/pricing")
    assert b"Starter" in response.data
    assert b"Instructor" in response.data
    assert b"Organization" in response.data


def test_pricing_page_ctas_point_to_register(billing_app):
    c = billing_app.test_client()
    response = c.get("/pricing")
    assert b"/auth/register" in response.data


def test_pricing_page_org_cta_has_org_plan_param(billing_app):
    c = billing_app.test_client()
    response = c.get("/pricing")
    assert b"plan=org" in response.data


def test_pricing_page_logged_in_teacher_redirects_to_plan(
    billing_app, billing_teacher_client
):
    client, _ = billing_teacher_client
    response = client.get("/pricing", follow_redirects=False)
    assert response.status_code == 302
    assert "/billing/plan" in response.headers["Location"]


def test_landing_page_has_pricing_section(billing_app):
    c = billing_app.test_client()
    response = c.get("/")
    assert b"Starter" in response.data or b"pricing" in response.data.lower()


def test_landing_page_free_cta_points_to_register(billing_app):
    c = billing_app.test_client()
    response = c.get("/")
    assert b"/auth/register" in response.data
