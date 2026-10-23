import httpx

from app import config

PLACEHOLDERS = {
    "PERSON": "[NAME]",
    "DATE_TIME": "[DATE]",
    "PHONE_NUMBER": "[PHONE]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "LOCATION": "[LOCATION]",
    "US_SSN": "[SSN]",
    "MEDICAL_RECORD_NUMBER": "[MRN]",
    "IP_ADDRESS": "[IP_ADDRESS]",
    "URL": "[URL]",
}

MRN_RECOGNIZER = {
    "name": "mrn_recognizer",
    "supported_language": "en",
    "supported_entity": "MEDICAL_RECORD_NUMBER",
    "patterns": [{"name": "mrn", "regex": r"\bMRN[- ]?\d{6,10}\b", "score": 0.9}],
}


async def analyze(text: str, client: httpx.AsyncClient) -> list[dict]:
    resp = await client.post(
        f"{config.PRESIDIO_ANALYZER_URL}/analyze",
        json={"text": text, "language": "en", "score_threshold": 0.4, "ad_hoc_recognizers": [MRN_RECOGNIZER]},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


async def scrub(text: str, client: httpx.AsyncClient, include: set[str] | None = None) -> tuple[str, list[str]]:
    results = await analyze(text, client)
    if include is not None:
        results = [r for r in results if r["entity_type"] in include]
    # ...the anonymize call is unchanged...
    anonymizers = {entity: {"type": "replace", "new_value": value} for entity, value in PLACEHOLDERS.items()}
    anonymizers["DEFAULT"] = {"type": "replace", "new_value": "[REDACTED]"}

    resp = await client.post(
        f"{config.PRESIDIO_ANONYMIZER_URL}/anonymize",
        json={"text": text, "analyzer_results": results, "anonymizers": anonymizers},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["text"], sorted({r["entity_type"] for r in results})

