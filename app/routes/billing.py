# app/routes/billing.py

from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
    flash,
    current_app,
)
from app.utils.auth import login_required, teacher_required, current_user
from app.models.billing import (
    get_teacher_sub,
    set_teacher_sub,
    cancel_teacher_sub,
    teacher_has_access,
)
from app.utils.stripe_client import (
    create_checkout_session,
    create_billing_portal_session,
    construct_webhook_event,
    retrieve_subscription,
)
from app import csrf

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.route("/plan")
@login_required
@teacher_required
def plan():
    user = current_user()
    sub = get_teacher_sub(user["id"])

    freemium_enabled = current_app.config.get("FREEMIUM_ENABLED", True)
    has_access = teacher_has_access(user, freemium_enabled)

    pro_price_id = current_app.config.get("STRIPE_PRICE_PRO")
    org_price_id = current_app.config.get("STRIPE_PRICE_ORG")

    return render_template(
        "billing/plan.html",
        user=user,
        sub=sub,
        has_access=has_access,
        freemium_enabled=freemium_enabled,
        pro_price_id=pro_price_id,
        org_price_id=org_price_id,
    )


@billing_bp.route("/checkout/<plan>")
@login_required
@teacher_required
def checkout(plan):
    user = current_user()

    price_map = {
        "pro": current_app.config.get("STRIPE_PRICE_PRO"),
        "org": current_app.config.get("STRIPE_PRICE_ORG"),
    }

    price_id = price_map.get(plan)
    if not price_id:
        flash("Invalid plan selected.", "error")
        return redirect(url_for("billing.plan"))

    sub = get_teacher_sub(user["id"])
    existing_customer_id = sub["sub_stripe_customer_id"] if sub else None

    try:
        checkout_session = create_checkout_session(
            customer_email=user["email"],
            price_id=price_id,
            success_url=url_for("billing.success", _external=True)
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("billing.canceled", _external=True),
            metadata={
                "user_id": str(user["id"]),
                "plan": plan,
            },
            existing_customer_id=existing_customer_id,
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        current_app.logger.error(f"Stripe checkout error: {e}")
        flash("Something went wrong starting checkout. Please try again.", "error")
        return redirect(url_for("billing.plan"))


@billing_bp.route("/success")
@login_required
def success():
    return render_template("billing/success.html")


@billing_bp.route("/canceled")
@login_required
def canceled():
    return render_template("billing/canceled.html")


@billing_bp.route("/portal")
@login_required
@teacher_required
def portal():
    user = current_user()
    sub = get_teacher_sub(user["id"])

    if not sub or not sub["sub_stripe_customer_id"]:
        flash("No active subscription found.", "error")
        return redirect(url_for("billing.plan"))

    try:
        portal_session = create_billing_portal_session(
            stripe_customer_id=sub["sub_stripe_customer_id"],
            return_url=url_for("billing.plan", _external=True),
        )
        return redirect(portal_session.url, code=303)
    except Exception as e:
        current_app.logger.error(f"Stripe portal error: {e}")
        flash("Could not open billing portal. Please try again.", "error")
        return redirect(url_for("billing.plan"))


@billing_bp.route("/webhook", methods=["POST"])
@csrf.exempt
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = construct_webhook_event(payload, sig_header)
    except Exception as e:
        current_app.logger.warning(f"Stripe webhook signature failed: {e}")
        return "Bad signature", 400

    _handle_event(event)
    return "", 200


def _handle_event(event):
    from app.models.billing import (
        get_user_by_stripe_customer,
        get_org_by_stripe_customer,
        set_org_sub,
        cancel_org_sub,
    )

    event_type = event["type"]
    data = event["data"]["object"]

    current_app.logger.info(f"Stripe event: {event_type}")

    if event_type == "checkout.session.completed":
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")

        if user_id:
            sub = retrieve_subscription(subscription_id)
            set_teacher_sub(
                user_id=int(user_id),
                status=sub["status"],
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                price_id=sub["items"]["data"][0]["price"]["id"],
                current_period_end=sub["current_period_end"],
            )

    elif event_type == "customer.subscription.updated":
        customer_id = data.get("customer")
        new_status = data.get("status")
        period_end = data.get("current_period_end")
        price_id = data["items"]["data"][0]["price"]["id"]
        subscription_id = data.get("id")

        user = get_user_by_stripe_customer(customer_id)
        if user:
            set_teacher_sub(
                user_id=user["id"],
                status=new_status,
                stripe_subscription_id=subscription_id,
                price_id=price_id,
                current_period_end=period_end,
            )
            return

        org = get_org_by_stripe_customer(customer_id)
        if org:
            set_org_sub(
                org_id=org["id"],
                status=new_status,
                stripe_subscription_id=subscription_id,
                price_id=price_id,
                current_period_end=period_end,
            )

    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")

        user = get_user_by_stripe_customer(customer_id)
        if user:
            cancel_teacher_sub(user["id"])
            return

        org = get_org_by_stripe_customer(customer_id)
        if org:
            cancel_org_sub(org["id"])

    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")

        user = get_user_by_stripe_customer(customer_id)
        if user:
            set_teacher_sub(user_id=user["id"], status="past_due")
            return

        org = get_org_by_stripe_customer(customer_id)
        if org:
            set_org_sub(org_id=org["id"], status="past_due")
