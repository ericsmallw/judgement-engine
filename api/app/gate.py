from dataclasses import dataclass

import httpx

from app import config
from app.judge import IDENTIFIER_KEYS, judge
from app.llm import chat
from app.scrub import analyze, scrub

ESCALATION_REPLY = (
    "This sounds like it could be a medical emergency. Please call 911 or your local emergency number now."
)


@dataclass
class GateResult:
    status: str            # clean | scrubbed | local_only | escalated
    route: str
    model: str | None
    sent_text: str | None  # what actually left the gate, if anything
    reply: str
    scores: dict[str, float]
    entities: list[str]
    passes: int




# Strong on their own; dates and locations only count when the judge ties them to a person.
STRONG_ENTITIES = {"PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN", "MEDICAL_RECORD_NUMBER", "IP_ADDRESS"}
CONTEXTUAL_ENTITIES = {"DATE_TIME", "LOCATION"}


def is_flagged(scores: dict[str, float], entities: list[str]) -> bool:
    model_flag = any(scores[key] >= config.PHI_THRESHOLD for key in IDENTIFIER_KEYS)
    strong_entity = any(e in STRONG_ENTITIES for e in entities)
    return model_flag or strong_entity   # a bare DATE_TIME no longer triggers on its own


def entities_to_scrub(scores: dict[str, float]) -> set[str]:
    include = set(STRONG_ENTITIES)
    if scores["dates_and_places"] >= config.PHI_THRESHOLD:
        include |= CONTEXTUAL_ENTITIES      # scrub dates and places only when they're personal
    return include


async def run_gate(message: str, client: httpx.AsyncClient) -> GateResult:
    scores = await judge(message, client)

    # Emergencies go to people, not a model.
    if scores["urgent"] >= config.URGENT_THRESHOLD:
        return GateResult("escalated", "emergency script + human", None, None, ESCALATION_REPLY, scores, [], 1)

    entities = sorted({r["entity_type"] for r in await analyze(message, client)})
    if not is_flagged(scores, entities):
        reply = await chat(config.CLOUD_MODEL, message, client)
        return GateResult("clean", "cloud model", config.CLOUD_MODEL, message, reply, scores, [], 1)

    # Scrub, then re-check once: a hard limit, never "until it stabilizes".
    scrubbed, found = await scrub(message, client, entities_to_scrub(scores))
    scores = await judge(scrubbed, client, scrubbed=True)
    remaining = sorted({r["entity_type"] for r in await analyze(scrubbed, client)})

    if is_flagged(scores, remaining):
        reply = await chat(config.LOCAL_MODEL, scrubbed, client)  # still risky: never leaves this machine
        return GateResult("local_only", "local model", config.LOCAL_MODEL, scrubbed, reply, scores, found, 2)

    reply = await chat(config.CLOUD_MODEL, scrubbed, client)
    return GateResult("scrubbed", "cloud model", config.CLOUD_MODEL, scrubbed, reply, scores, found, 2)