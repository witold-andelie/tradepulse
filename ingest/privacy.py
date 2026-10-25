"""Remove source contact addresses from publishable research text before hashing."""

from __future__ import annotations

import hashlib
import re

CONTACT_ADDRESS = re.compile(r"[\w.+%'-]+@(?:[\w-]+\.)+[\w-]{2,63}")


def redact_contacts(text: str) -> str:
    """Keep research prose and numbers while removing contact addresses within the text budget."""
    return CONTACT_ADDRESS.sub("[CONTACT REDACTED]", text)[:200_000]


def sanitize_filing_texts(data):
    """Return a copy whose text, char_count and sha256 all describe the redacted text."""
    result = data.copy()
    result["text"] = result.text.map(redact_contacts).astype("string")
    result["char_count"] = result.text.str.len().astype("Int64")
    result["sha256"] = result.text.map(
        lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()
    ).astype("string")
    return result
