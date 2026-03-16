def is_coppa_approved(user):
    """
    Returns True if user's status is approved, False otherwise.
    Expects a dict-like user object with 'coppa_status
    """
    if not user:
        return False
    return user["coppa_status"] == "approved"
