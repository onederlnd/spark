from app.utils.sanitize import sanitize_plain, sanitize_bbcode, sanitize_username


def test_sanitize_plain_strips_html():
    result = sanitize_plain("<script>alert(1)</script>hello")
    assert "hello" in result
    assert "&lt;script&gt;" in result


def test_sanitize_plain_max_length():
    """Tests whether or not the plain was cut down to 10 characters"""
    result = sanitize_plain("a" * 300, max_length=10)
    assert len(result) == 10


def test_sanitize_plain_empty():
    result = sanitize_plain("")
    assert result == ""


def test_sanitize_plain_whitespace_only():
    result = sanitize_plain("    ")
    assert result == ""


def test_sanitize_bbcode_strips_html():
    result = sanitize_plain("<b>bold</b>hello")
    assert "hello" in result
    assert "<b>" not in result


def test_sanitize_bbcode_preserves_bbcode():
    result = sanitize_bbcode("[b]bold[/b]")
    assert result == "[b]bold[/b]"


def test_sanitize_bbcode_empty():
    result = sanitize_bbcode("")
    assert result == ""


def test_sanitize_username_strips_special_chars():
    result = sanitize_username("user<script>name)")
    assert result == "userscriptname"


def test_sanitize_username_strips_spaces():
    result = sanitize_username("user name")
    assert "username" in result


def test_sanitize_username_max_length():
    result = sanitize_username("a" * 50)
    assert len(result) == 32


def test_sanitize_username_empty():
    result = sanitize_username("")
    assert result == ""
