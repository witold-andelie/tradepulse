"""SYNTHETIC source contacts are removed without changing financial measurements."""

import hashlib

import pandas as pd

from ingest.privacy import CONTACT_ADDRESS, redact_contacts, sanitize_filing_texts


def test_research_text_redacts_source_contacts_before_hashing():
    contact = "SYNTHETIC.contact" + chr(64) + "mailbox.invalid"
    text = f"SYNTHETIC revenue 17.5 and EPS 2.4. Contact {contact}."
    source = pd.DataFrame(
        [{"text": text, "char_count": len(text), "sha256": "SYNTHETIC", "symbol": "SYNTHETIC"}]
    )
    before = source.copy(deep=True)

    actual = sanitize_filing_texts(source)

    assert actual.text.iloc[0] == "SYNTHETIC revenue 17.5 and EPS 2.4. Contact [CONTACT REDACTED]."
    assert not CONTACT_ADDRESS.search(actual.text.iloc[0])
    assert actual.char_count.iloc[0] == len(actual.text.iloc[0])
    assert actual.sha256.iloc[0] == hashlib.sha256(actual.text.iloc[0].encode()).hexdigest()
    assert actual.symbol.iloc[0] == "SYNTHETIC"
    pd.testing.assert_frame_equal(source, before)


def test_contact_redaction_respects_contract_text_limit():
    contact = "a" + chr(64) + "b.test"
    text = "SYNTHETIC " * 19_999 + contact + " trailing text"
    redacted = redact_contacts(text)
    assert len(redacted) <= 200_000
    assert not CONTACT_ADDRESS.search(redacted)
