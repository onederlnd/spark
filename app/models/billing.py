# app/models/billing.py

import time
from app.models import get_db


# ── Status values ──────────────────────────────────────────────────────────────
# 'free'      — on the free tier (or freemium disabled = gated)
# 'trialing'  — in a Stripe trial period
# 'active'    — paid and current
# 'past_due'  — payment failed, grace period
# 'canceled'  — subscription ended


ACTIVE_STATUSES = {"trialing", "active", "past_due"}


# ── Teacher subscription ───────────────────────────────────────────────────────


def get_teacher_sub(user_id):
    db = get_db()
    return db.execute(
        """
        SELECT sub_status, sub_stripe_customer_id, sub_stripe_subscription_id,
               sub_price_id, sub_current_period_end
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()


def set_teacher_sub(
    user_id,
    status,
    stripe_customer_id=None,
    stripe_subscription_id=None,
    price_id=None,
    current_period_end=None,
):
    db = get_db()
    db.execute(
        """
        UPDATE users
        SET sub_status = ?,
            sub_stripe_customer_id = COALESCE(?, sub_stripe_customer_id),
            sub_stripe_subscription_id = COALESCE(?, sub_stripe_subscription_id),
            sub_price_id = COALESCE(?, sub_price_id),
            sub_current_period_end = COALESCE(?, sub_current_period_end)
        WHERE id = ?
        """,
        (
            status,
            stripe_customer_id,
            stripe_subscription_id,
            price_id,
            current_period_end,
            user_id,
        ),
    )
    db.commit()


def cancel_teacher_sub(user_id):
    db = get_db()
    db.execute(
        """
        UPDATE users
        SET sub_status = 'canceled',
            sub_stripe_subscription_id = NULL,
            sub_price_id = NULL,
            sub_current_period_end = NULL
        WHERE id = ?
        """,
        (user_id,),
    )
    db.commit()


# ── Org subscription ───────────────────────────────────────────────────────────


def get_org_sub(org_id):
    db = get_db()
    return db.execute(
        """
        SELECT sub_status, sub_stripe_customer_id, sub_stripe_subscription_id,
               sub_price_id, sub_current_period_end
        FROM organizations
        WHERE id = ?
        """,
        (org_id,),
    ).fetchone()


def set_org_sub(
    org_id,
    status,
    stripe_customer_id=None,
    stripe_subscription_id=None,
    price_id=None,
    current_period_end=None,
):
    db = get_db()
    db.execute(
        """
        UPDATE organizations
        SET sub_status = ?,
            sub_stripe_customer_id = COALESCE(?, sub_stripe_customer_id),
            sub_stripe_subscription_id = COALESCE(?, sub_stripe_subscription_id),
            sub_price_id = COALESCE(?, sub_price_id),
            sub_current_period_end = COALESCE(?, sub_current_period_end)
        WHERE id = ?
        """,
        (
            status,
            stripe_customer_id,
            stripe_subscription_id,
            price_id,
            current_period_end,
            org_id,
        ),
    )
    db.commit()


def cancel_org_sub(org_id):
    db = get_db()
    db.execute(
        """
        UPDATE organizations
        SET sub_status = 'canceled',
            sub_stripe_subscription_id = NULL,
            sub_price_id = NULL,
            sub_current_period_end = NULL
        WHERE id = ?
        """,
        (org_id,),
    )
    db.commit()


# ── Lookup by Stripe IDs (used in webhooks) ────────────────────────────────────


def get_user_by_stripe_customer(stripe_customer_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM users WHERE sub_stripe_customer_id = ?",
        (stripe_customer_id,),
    ).fetchone()


def get_org_by_stripe_customer(stripe_customer_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM organizations WHERE sub_stripe_customer_id = ?",
        (stripe_customer_id,),
    ).fetchone()


# ── Access check (single source of truth) ─────────────────────────────────────


def teacher_has_access(user, freemium_enabled=True):
    """
    Returns True if the teacher should have full platform access.

    Priority order:
      1. Freemium is enabled — everyone gets access (kill switch off)
      2. Teacher's own subscription is active
      3. Teacher's org subscription is active

    Pass freemium_enabled from app.config['FREEMIUM_ENABLED'].
    """
    if freemium_enabled:
        return True

    # personal sub active?
    if user["sub_status"] in ACTIVE_STATUSES:
        # check period hasn't expired
        period_end = user["sub_current_period_end"]
        if period_end and time.time() > period_end:
            return False
        return True

    # org sub active?
    org_id = user["org_id"]
    if org_id:
        org_sub = get_org_sub(org_id)
        if org_sub and org_sub["sub_status"] in ACTIVE_STATUSES:
            period_end = org_sub["sub_current_period_end"]
            if period_end and time.time() > period_end:
                return False
            return True

    return False
