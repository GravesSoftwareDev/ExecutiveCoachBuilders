from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlparse

from django.utils.html import escape
from django.utils.safestring import mark_safe


_ALLOWED_TAGS = {
    'a', 'b', 'blockquote', 'br', 'code', 'em', 'h1', 'h2', 'h3', 'h4',
    'i', 'li', 'ol', 'p', 'pre', 'span', 'strong', 'u', 'ul',
}
_ALLOWED_ATTRS = {
    'a': {'href', 'title', 'rel', 'target'},
}
_SUPPRESSED_TAGS = {'iframe', 'object', 'script', 'style'}


def _safe_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in {'http', 'https', 'mailto', 'tel'}:
        return ''
    return value


class _ArticleHTMLCleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.suppressed_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SUPPRESSED_TAGS:
            self.suppressed_depth += 1
            return
        if self.suppressed_depth:
            return
        if tag not in _ALLOWED_TAGS:
            return
        clean_attrs = []
        allowed = _ALLOWED_ATTRS.get(tag, set())
        for name, value in attrs:
            if name not in allowed:
                continue
            if name == 'href':
                value = _safe_url(value or '')
                if not value:
                    continue
            clean_attrs.append(f' {name}="{escape(value or "")}"')
        if tag == 'a' and not any(a.startswith(' rel=') for a in clean_attrs):
            clean_attrs.append(' rel="noopener noreferrer"')
        self.out.append(f'<{tag}{"".join(clean_attrs)}>')

    def handle_endtag(self, tag):
        if tag in _SUPPRESSED_TAGS and self.suppressed_depth:
            self.suppressed_depth -= 1
            return
        if self.suppressed_depth:
            return
        if tag in _ALLOWED_TAGS and tag != 'br':
            self.out.append(f'</{tag}>')

    def handle_data(self, data):
        if self.suppressed_depth:
            return
        self.out.append(escape(data))

    def handle_entityref(self, name):
        if self.suppressed_depth:
            return
        self.out.append(f'&{name};')

    def handle_charref(self, name):
        if self.suppressed_depth:
            return
        self.out.append(f'&#{name};')


def render_article_html(html: str):
    cleaner = _ArticleHTMLCleaner()
    cleaner.feed(html or '')
    cleaner.close()
    return mark_safe(''.join(cleaner.out))
