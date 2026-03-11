# app/utils/bbcode.py

import re
import html


def render_bbcode(text):
    """Convert stored BBCode to safe HTML for display."""
    if not text:
        return ""

    text = html.unescape(text)
    text = html.escape(text, quote=True)
    text = text.replace("\n", "<br>\n")

    text = re.sub(
        r"\[b\](.*?)\[/b\]",
        r"<strong>\1</strong>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"\[i\](.*?)\[/i\]", r"<em>\1</em>", text, flags=re.IGNORECASE | re.DOTALL
    )

    text = re.sub(
        r"\[u\](.*?)\[/u\]",
        r'<span style="text-decoration:underline">\1</span>',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"\[s\](.*?)\[/s\]", r"<del>\1</del>", text, flags=re.IGNORECASE | re.DOTALL
    )

    text = re.sub(
        r"\[code\](.*?)\[/code\]",
        r"<pre><code>\1</code></pre>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"\[quote\](.*?)\[/quote\]",
        r"<blockquote>\1</blockquote>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"\[quote=([^\]]{1,60})\](.*?)\[/quote\]",
        lambda m: (
            f"<blockquote><cite>{html.escape(m.group(1))}</cite>{m.group(2)}</blockquote>"
        ),
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"\[url\](https?://[^\[]{1,500})\[/url\]",
        r'<a href="\1" rel="noopener noreferrer" target="_blank">\1</a>',
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\[url=(https?://[^\]]{1,500})\](.*?)\[/url\]",
        r'<a href="\1" rel="noopener noreferrer" target="_blank">\2</a>',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    def render_list(m):
        items = re.split(r"\[\*\]", m.group(1))
        lis = "".join(f"<li>{i.strip()}</li>" for i in items if i.strip())
        return f"<ul>{lis}</ul>"

    text = re.sub(
        r"\[list\](.*?)\[/list\]", render_list, text, flags=re.IGNORECASE | re.DOTALL
    )

    return text
