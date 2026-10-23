import httpx

from app import config

from app.scrub import PLACEHOLDERS

PLACEHOLDER_LIST = ", ".join(sorted(set(PLACEHOLDERS.values())))

RECHECK_NOTE = (
    f" Important: this text has already been de-identified. The placeholders {PLACEHOLDER_LIST} "
    "mark personal information that was safely removed. Placeholders never count as identifiers, "
    "even in phrases like 'born [DATE]' or 'call [PHONE]'. Answer only about identifying details "
    "that remain in plain text."
)

def noul(instructions: str, yes: str, no: str, note: str = "") -> dict:
    return {"type": "noul", "instructions": instructions + note, "criteria": {"true": yes, "false": no}}

URGENCY_QUESTION = {
    "type": "score",
    "instructions": "How clinically urgent is this message?",
    "criteria": [
        "Administrative or scheduling",
        "General health question",
        "Symptoms that need a clinician's attention",
        "A possible emergency needing immediate care",
    ],
}

IDENTIFIER_KEYS = ["direct_identifiers", "record_numbers", "dates_and_places", "digital_identifiers"]

def build_questions(scrubbed: bool) -> dict:
    note = RECHECK_NOTE if scrubbed else ""
    return {
        "direct_identifiers": noul(
            "Does the text identify a specific person by name, phone or fax number, email address, or Social Security number?",
            "The text contains at least one direct personal identifier.",
            "The text contains no direct personal identifiers.", note),
        # ...the other three identifier questions, each with note passed the same way...
        "record_numbers": noul(
            "Does the text contain a medical record number, health plan or account number, license number, or device serial number?",
            "The text contains at least one record, account, or device number.",
            "The text contains no record, account, or device numbers.", note),
        "dates_and_places": noul(
            "Does the text tie a specific person to a date more precise than a year, or to a location smaller than a state?",
            "The text links a person to a specific date or a sub-state location.",
            "The text does not link a person to a specific date or sub-state location.", note),
        "digital_identifiers": noul(
            "Does the text contain a URL, IP address, or biometric identifier tied to a person?",
            "The text contains a digital or biometric identifier tied to a person.",
            "The text contains no digital or biometric identifiers tied to a person."),
        "urgency": URGENCY_QUESTION,   # the score question, unchanged
    }


async def judge(text: str, client: httpx.AsyncClient, scrubbed: bool = False) -> dict[str, float]:
    resp = await client.post(
        f"{config.OLLAMA_URL}/v1/systemone",
        json={"model": config.JUDGE_MODEL, "state": text, "questions": build_questions(scrubbed), "keep_alive": "30m"},
        timeout=120,
    )
    resp.raise_for_status()
    answers = resp.json()["answers"]

    scores = {key: answers[key]["noul"] for key in IDENTIFIER_KEYS}   # probability of "true"
    scores["urgent"] = answers["urgency"]["probabilities"]["3"]      # probability of the top level
    scores["urgency_level"] = answers["urgency"]["score"]             # probability-weighted level, 0 to 3
    return scores