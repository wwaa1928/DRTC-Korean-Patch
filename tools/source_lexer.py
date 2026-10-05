"""Token-aware literal scanning of the user-owned game; no game source is bundled."""
import re

def lex_literals(data, quoted_words=frozenset({b'"quoted'})):
    i = 0
    previous = None
    skip_next = False
    found, warnings = [], []
    size = len(data)
    while i < size:
        if data[i:i+1].isspace():
            i += 1
            continue
        start = i
        end = i
        while end < size and not data[end:end+1].isspace():
            end += 1
        token = data[start:end]
        if skip_next:
            skip_next = False
            previous = token
            i = end
            continue
        if token in (b'//', b'\\'):
            lf = data.find(b'\n', end)
            i = size if lf < 0 else lf + 1
            previous = None
            continue
        if token == b'(*':
            # DRTC base.df implements this as tokens through the first exact *).
            m = re.search(rb'(?<!\S)\*\)(?!\S)', data[end:])
            if not m:
                warnings.append({'byte': start, 'kind': 'unclosed-block-comment'})
                break
            i = end + m.end()
            previous = None
            continue
        if token == b'(':
            close = data.find(b')', end)
            if close < 0:
                warnings.append({'byte': start, 'kind': 'unclosed-stack-comment'})
                break
            i = close + 1
            previous = None
            continue
        if token in (b':', b'char', b"'", b"[']", b'postpone'):
            skip_next = True
            previous = token
            i = end
            continue
        if token in quoted_words:
            previous = token
            i = end
            continue
        prefix = None
        if data[i] == 34:
            prefix = 'string'
            content_start = i + 1
        elif token == b'abort"':
            prefix = 'abort-message'
            content_start = end
            if content_start < size and data[content_start:content_start+1].isspace():
                content_start += 1
        if prefix:
            close = data.find(b'"', content_start)
            if close < 0:
                warnings.append({'byte': start, 'kind': 'unclosed-string'})
                break
            text = data[content_start:close].decode('utf-8')
            found.append({'start': content_start, 'end': close, 'opening': start,
                          'source': text, 'kind': prefix,
                          'previous_token': (previous or b'').decode('utf-8', 'replace')})
            i = close + 1
            previous = b'<string>'
            continue
        previous = token
        i = end
    return found, warnings


def classify_literal(item, after):
    text = item['source']
    if not text or not re.search('[A-Za-z]', text):
        return 'review-technical-or-punctuation'
    if item['kind'] == 'abort-message':
        return 'review-debug-error'
    if re.search(r'(?i)(?:\.(?:df|txt|png|mp3|dll|exe|zip)|[\\/](?:gfx|data|deathforth|rooms)/)', text) and '\n' not in text:
        return 'review-path-or-identifier'
    if re.match(rb'\s+(?:evaluate|\$load|load|parse|\$=|str>|>str)\b', after):
        return 'review-code-or-identifier'
    if len(text) > 150 and sum(c.isalpha() for c in text) / len(text) < .18:
        return 'review-map-or-code'
    return 'text-candidate'


