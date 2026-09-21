"""The triage decision schema — the questions every router must answer.

Both Jev and the baseline router answer the same three decisions per alert,
so results are directly comparable. Mirrors the AlertAnalysis model from
the aiops-prototype (Priority enum, sla_impact, system_type).
"""

from src.jev_client import choice, noul

CATEGORIES = {
    "capacity": "resource capacity issue (disk, memory, CPU, quota)",
    "availability": "service outage, downtime, or failed jobs blocking users",
    "performance": "degraded latency or throughput, service still up",
    "security": "security incident, auth anomaly, or data exposure",
    "noise": "flapping, duplicate, or informational alert needing no action",
}

PRIORITIES = {
    "P1": "immediate response, customer-facing impact or SLA breach in progress",
    "P2": "urgent, needs action this shift, no customer impact yet",
    "P3": "routine, can wait for business hours",
}


def triage_questions() -> dict[str, dict]:
    return {
        "category": choice("What type of alert is this?", CATEGORIES),
        "priority": choice("What priority should this alert get?", PRIORITIES),
        "page_human": noul(
            "Should this alert page an on-call human right now, "
            "as opposed to being handled by automation or a ticket?"
        ),
    }
