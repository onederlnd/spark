# app/utils/stripe_client.py

import stripe
from flask import current_app


def get_stripe():
    """Return configured Stripe module. Call inside request context."""
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    return stripe


def create_checkout_session(
    customer_email,
    price_id,
    success_url,
    cancel_url,
    metadata=None,
    existing_customer_id=None,
):
    """
    Create a Stripe Checkout Session.

    Args:
        customer_email:       pre-fill email on the Stripe page
        price_id:             Stripe Price ID for the chosen plan
        success_url:          redirect after successful payment
        cancel_url:           redirect if user abandons checkout
        metadata:             dict attached to the session (e.g. user_id, org_id)
        existing_customer_id: Stripe customer ID if one already exists

    Returns:
        Stripe CheckoutSession object
    """
    s = get_stripe()

    params = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": metadata or {},
        "allow_promotion_codes": True,
    }

    if existing_customer_id:
        params["customer"] = existing_customer_id
    else:
        params["customer_email"] = customer_email

    return s.checkout.sessions.create(**params)


def create_billing_portal_session(stripe_customer_id, return_url):
    """
    Create a Stripe Billing Portal session so the user can manage
    their subscription (update card, cancel, view invoices) without
    us building that UI ourselves.
    """
    s = get_stripe()
    return s.billing_portal.sessions.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )


def construct_webhook_event(payload, sig_header):
    """
    Verify and construct a Stripe webhook event.
    Raises stripe.error.SignatureVerificationError on bad signature.
    """
    s = get_stripe()
    return s.Webhook.construct_event(
        payload,
        sig_header,
        current_app.config["STRIPE_WEBHOOK_SECRET"],
    )


def retrieve_subscription(subscription_id):
    s = get_stripe()
    return s.Subscription.retrieve(subscription_id)
