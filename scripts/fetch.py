#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["scrapling[fetchers]", "html2text"]
# ///
"""
Universal web content extractor (Scrapling + html2text).
Returns clean Markdown with headings, links, images, lists, and code blocks.

Usage:
  uv run fetch.py <url> [max_chars] [--stealth]

Modes:
  (default)   Fast HTTP fetch via Fetcher — works for most sites (~1-3s)
  --stealth   Headless browser via StealthyFetcher — for JS-rendered or
              anti-scraping sites like WeChat, Zhihu, Juejin (~5-15s)

Examples:
  uv run fetch.py https://sspai.com/post/73145
  uv run fetch.py https://mp.weixin.qq.com/s/xxx 30000 --stealth
  uv run fetch.py https://zhuanlan.zhihu.com/p/12345 --stealth
"""

import sys
import os
import re
import json
import logging

# Ensure UTF-8 output on Windows (avoid GBK encoding errors with Chinese content)
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def check_dependencies():
    """Check if required packages are installed and provide install instructions."""
    missing = []
    try:
        import scrapling  # noqa: F401
    except ImportError:
        missing.append("scrapling")
    try:
        import html2text  # noqa: F401
    except ImportError:
        missing.append("html2text")

    if missing:
        import shutil

        if shutil.which("uv"):
            hint = f"  uv run {__file__} <url>   (dependencies are resolved automatically)"
        else:
            hint = (
                f"  Option 1 (recommended — isolated):\n"
                f"    pip install uv\n"
                f"    uv run {__file__} <url>\n"
                f"\n"
                f"  Option 2 (global install):\n"
                f"    pip install {' '.join(missing)}"
            )
        print(
            f"Error: missing dependencies: {', '.join(missing)}\n"
            f"\n"
            f"{hint}",
            file=sys.stderr,
        )
        sys.exit(1)


def fix_lazy_images(html_raw):
    """
    Promote data-src to src for lazy-loaded images (WeChat, Zhihu, etc.).
    Many Chinese platforms use data-src for the real image URL while src
    holds a tiny placeholder. html2text only reads src, so we swap them.
    """
    def _replace(m):
        tag = m.group(0)
        data_src = m.group(1)
        # Remove existing src="..." to avoid duplicate src attributes
        tag = re.sub(r'\ssrc="[^"]*"', '', tag)
        # Remove the data-src="..." itself
        tag = re.sub(r'\sdata-src="[^"]*"', '', tag)
        # Insert the real src after <img
        tag = tag.replace('<img', f'<img src="{data_src}"', 1)
        return tag

    return re.sub(r'<img[^>]*?\sdata-src="([^"]+)"[^>]*?>', _replace, html_raw)


def fix_wechat_code_blocks(html_raw):
    """
    Fix WeChat's code snippet blocks:
    1. Remove line-number <ul> lists (rendered as '* * * *' by html2text).
    2. Insert newlines between consecutive <code> tags inside <pre>, so each
       line renders on its own line instead of being concatenated.
    """
    # Remove line-number lists
    html_raw = re.sub(
        r'<ul\s+class="code-snippet__line-index[^"]*"[^>]*>.*?</ul>',
        '',
        html_raw,
        flags=re.DOTALL,
    )
    # Insert newline between consecutive </code><code> inside <pre>
    html_raw = re.sub(r'</code>\s*<code>', '\n', html_raw)
    return html_raw


# CSS selectors in priority order — the first match with enough content wins.
# Covers most blog/article platforms without needing per-site customization.
CONTENT_SELECTORS = [
    "article",
    "main",
    ".post-content",
    ".entry-content",
    ".article-content",
    ".article-body",
    ".article-detail",         # 36kr
    ".article-holder",         # InfoQ
    ".post_body",              # 163.com (NetEase)
    ".markdown-body",          # GitHub
    ".Post-RichText",          # Zhihu
    "#article_content",        # CSDN
    ".article-area",           # Juejin
    ".ssa-article",            # Toutiao
    '[role="article"]',
    '[itemprop="articleBody"]',
]

# WeChat has a unique DOM structure — try these first for mp.weixin.qq.com
WECHAT_SELECTORS = [
    "div#js_content",
    "div.rich_media_content",
]

# Minimum characters for a selector match to be considered "real content"
MIN_CONTENT_LENGTH = 200


def html_to_markdown(html_raw, max_chars=30000):
    """Convert raw HTML to clean Markdown."""
    import html2text

    html_raw = fix_lazy_images(html_raw)
    html_raw = fix_wechat_code_blocks(html_raw)

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0       # No line wrapping
    h.skip_internal_links = True
    h.ignore_emphasis = False
    h.mark_code = True     # Use fenced code blocks (```) instead of indentation

    md = h.handle(html_raw)
    # Convert [code]...[/code] to fenced code blocks
    md = md.replace("[code]", "```").replace("[/code]", "```")
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md[:max_chars]


def extract_content(page, url, max_chars=30000):
    """
    Try content selectors to find the article body.
    Returns (markdown_text, matched_selector).
    """
    is_wechat = "mp.weixin.qq.com" in url
    selectors = (WECHAT_SELECTORS + CONTENT_SELECTORS) if is_wechat else CONTENT_SELECTORS

    for selector in selectors:
        els = page.css(selector)
        if els:
            md = html_to_markdown(els[0].html_content, max_chars)
            if len(md) >= MIN_CONTENT_LENGTH:
                return md, selector

    # Fallback: convert the entire page
    md = html_to_markdown(page.html_content, max_chars)
    return md, "body(fallback)"


def _suppress_scrapling_logs():
    """Scrapling's logger is noisy (deprecation warnings, fetch info). Silence it."""
    logging.getLogger("scrapling").setLevel(logging.CRITICAL)


def fetch_fast(url, max_chars=30000, timeout=15):
    """
    Fast HTTP fetch — no JavaScript execution.
    Works for most blogs and static sites.
    """
    from scrapling.fetchers import Fetcher
    _suppress_scrapling_logs()

    page = Fetcher().get(url, timeout=timeout, stealthy_headers=True)
    return extract_content(page, url, max_chars)


def fetch_stealth(url, max_chars=30000, timeout=30000):
    """
    Headless browser fetch — executes JavaScript, bypasses anti-scraping.
    Required for: WeChat articles, Zhihu, Juejin, and other JS-rendered pages.
    Slower (~5-15s) but more reliable for protected content.
    """
    from scrapling.fetchers import StealthyFetcher
    _suppress_scrapling_logs()

    page = StealthyFetcher().fetch(
        url,
        headless=True,
        network_idle=True,
        timeout=timeout,
    )
    return extract_content(page, url, max_chars)


def fetch(url, max_chars=30000, stealth=False):
    """
    Main entry point. Fetches URL and returns (markdown, selector, mode).
    If stealth=False, tries fast mode first and falls back to stealth
    when the result is too short (likely a JS-rendered page).
    """
    if stealth:
        md, selector = fetch_stealth(url, max_chars)
        return md, selector, "stealth"

    # Try fast mode first
    md, selector = fetch_fast(url, max_chars)

    # If fast mode got barely any content, the page likely needs JS rendering
    if len(md) < MIN_CONTENT_LENGTH:
        try:
            md_stealth, sel_stealth = fetch_stealth(url, max_chars)
            if len(md_stealth) > len(md):
                return md_stealth, sel_stealth, "stealth(auto-fallback)"
        except Exception:
            pass  # Stick with fast mode result

    return md, selector, "fast"


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 fetch.py <url> [max_chars] [--stealth]\n"
            "\n"
            "Options:\n"
            "  max_chars   Maximum output characters (default: 30000)\n"
            "  --stealth   Use headless browser for JS-rendered pages\n"
            "  --json      Output as JSON with metadata\n",
            file=sys.stderr,
        )
        sys.exit(1)

    url = sys.argv[1]
    args = sys.argv[2:]

    stealth = "--stealth" in args
    json_output = "--json" in args
    args = [a for a in args if not a.startswith("--")]
    max_chars = int(args[0]) if args else 30000

    try:
        md, selector, mode = fetch(url, max_chars, stealth=stealth)

        if json_output:
            result = {
                "url": url,
                "mode": mode,
                "selector": selector,
                "content_length": len(md),
                "content": md,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(md)

    except Exception as e:
        error_msg = f"Error fetching {url}: {type(e).__name__}: {e}"
        if json_output:
            print(json.dumps({"url": url, "error": error_msg}, ensure_ascii=False))
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    check_dependencies()
    main()
