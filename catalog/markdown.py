"""Markdown rendering shared across the platform.

Designed to degrade gracefully so the app runs even before optional packages
are installed:

* If the third-party ``markdown`` package is available, it is used (with code
  highlighting via Pygments/codehilite when Pygments is also installed).
* Otherwise a small built-in fallback renderer handles the common cases
  (headings, code fences, inline code, bold/italic, lists, paragraphs) so
  lessons stay readable. Install ``markdown`` for full fidelity.
"""
import html
import re

try:  # Prefer the real Markdown library when present.
    import markdown as _markdown

    _HAS_MARKDOWN = True
except ImportError:  # pragma: no cover - exercised only without the dep
    _HAS_MARKDOWN = False

try:
    import pygments  # noqa: F401

    _HAS_PYGMENTS = True
except ImportError:
    _HAS_PYGMENTS = False


def _extensions():
    exts = ["fenced_code", "tables", "sane_lists", "nl2br", "toc"]
    configs = {}
    if _HAS_PYGMENTS:
        exts.append("codehilite")
        configs["codehilite"] = {"guess_lang": False}
    return exts, configs


def _fallback(text: str) -> str:
    """Minimal Markdown -> HTML for when the ``markdown`` package is missing."""
    lines = text.split("\n")
    out = []
    in_code = False
    in_list = False
    para = []

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for line in lines:
        if line.strip().startswith("```"):
            if not in_code:
                flush_para()
                close_list()
                out.append("<pre><code>")
                in_code = True
            else:
                out.append("</code></pre>")
                in_code = False
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        stripped = line.strip()
        if not stripped:
            flush_para()
            close_list()
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            flush_para()
            close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue
        if re.match(r"^[-*]\s+", stripped):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + _inline(stripped[2:]) + "</li>")
            continue
        para.append(stripped)

    if in_code:
        out.append("</code></pre>")
    flush_para()
    close_list()
    return "\n".join(out)


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def render_markdown(text: str) -> str:
    if not text:
        return ""
    if _HAS_MARKDOWN:
        exts, configs = _extensions()
        return _markdown.markdown(
            text, extensions=exts, extension_configs=configs, output_format="html5"
        )
    return _fallback(text)
