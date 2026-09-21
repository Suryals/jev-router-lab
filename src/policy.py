"""SPINE — the escalation policy. Hand-write this (Chief).

This is the piece that turns Jev from "a classifier" into "an L1 router":
given one shadow record's answers, decide what the supervisor graph does.

Contract to implement:

    def route(answers: dict) -> str
        Returns one of: "automate" | "escalate_llm" | "page_human"

Design questions to answer while writing it (these become article content):
  - What confidence threshold gates "automate"? Start conservative
    (e.g. category confidence >= 0.9 AND page_human <= 0.2) and let the
    eval data move it.
  - Is page_human >= 0.5 the right paging bar, or should P1 gold cases
    teach you it needs to be lower (paging is cheap, missed P1s are not)?
  - Asymmetric risk: a wrong "automate" on a security alert costs more
    than a wrong "escalate_llm" on noise. Should thresholds differ per
    category?

This mirrors the L1 / L1.5 / L2 ladder from the ops platform: automate is
L1, escalate_llm is the reasoning model at L1.5, page_human is L2.
"""


def route(answers: dict) -> str:
    raise NotImplementedError("route() is Chief's to write")
