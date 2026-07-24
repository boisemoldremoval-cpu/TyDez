#!/usr/bin/env python3
"""
Generate cryptographically secure, URL-safe tokens.

Useful for share links, cache-busting suffixes, upload keys, and any place that
needs an unguessable string safe to drop straight into a URL or filename.

    python3 tokens.py                 # one 32-byte token (~43 chars)
    python3 tokens.py 16              # one 16-byte token (shorter)
    python3 tokens.py 32 5            # five 32-byte tokens, one per line
    python3 tokens.py --hex 16        # hex instead of URL-safe base64

As a library:

    from tokens import url_safe_token
    slug = url_safe_token()           # e.g. "e08xiX3-IqurVLX1nNzKHaUxo30UEuNhkA0S6cETl94"
"""

import secrets
import sys

# 32 bytes of entropy (256 bits) — well beyond guessable, still compact.
DEFAULT_NBYTES = 32


def url_safe_token(nbytes: int = DEFAULT_NBYTES) -> str:
    """Return a URL-safe base64 token carrying `nbytes` of entropy.

    The returned string is longer than `nbytes` (base64 expansion) and contains
    only characters safe in URLs, filenames, and headers: A-Z, a-z, 0-9, - and _.
    """
    if nbytes < 1:
        raise ValueError("nbytes must be >= 1")
    return secrets.token_urlsafe(nbytes)


def hex_token(nbytes: int = DEFAULT_NBYTES) -> str:
    """Return a hex token carrying `nbytes` of entropy (2 hex chars per byte)."""
    if nbytes < 1:
        raise ValueError("nbytes must be >= 1")
    return secrets.token_hex(nbytes)


def main():
    args = sys.argv[1:]
    as_hex = "--hex" in args
    args = [a for a in args if a != "--hex"]

    try:
        nbytes = int(args[0]) if len(args) >= 1 else DEFAULT_NBYTES
        count = int(args[1]) if len(args) >= 2 else 1
    except ValueError:
        print("usage: python3 tokens.py [nbytes] [count] [--hex]", file=sys.stderr)
        raise SystemExit(2)

    if nbytes < 1 or count < 1:
        print("nbytes and count must both be >= 1", file=sys.stderr)
        raise SystemExit(2)

    gen = hex_token if as_hex else url_safe_token
    for _ in range(count):
        print(gen(nbytes))


if __name__ == "__main__":
    main()
