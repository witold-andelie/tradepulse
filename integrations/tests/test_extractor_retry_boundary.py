"""SYNTHETIC malformed extraction stays within the core's existing bounded retry loop."""

from integrations.live_acceptance import AuditedLLM
from integrations.meterless.llm import LLMResponse
from tradepulse.extract.runner import extract_document


def test_invalid_event_object_reaches_existing_extractor_feedback_retry(tmp_path):
    replies = ['{"events":["event_type"]}', '{"events":[]}']
    calls = []

    class Client:
        def complete(self, role, messages, _schema):
            calls.append((role, messages))
            return LLMResponse(replies[len(calls) - 1], "glm", "glm-5.3-flash", 1, 1,
                               "synthetic", False)

    llm = AuditedLLM(Client(), tmp_path / "models.jsonl")
    doc = {"symbol": "SYNTHETIC", "document_type": "EX-99.1", "accession_number": "synthetic",
           "text": "SYNTHETIC document", "sha256": "0" * 64, "available_at": "2026-10-23T12:00:00Z"}
    events, problems = extract_document(doc, llm, max_retries=1)
    assert len(calls) == 2
    assert "PREVIOUS ANSWER WAS REJECTED" in calls[1][1][1]["content"]
    assert events == [] and problems == []
    assert '"schema_valid": false' in (tmp_path / "models.jsonl").read_text()
