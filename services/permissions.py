from __future__ import annotations

from dataclasses import dataclass

from database import models
from services.scoring import calculate_match_score


@dataclass(frozen=True)
class MessagingGateResult:
    allowed: bool
    score: int
    interest_status: str | None


def can_message(db_path: str, from_user_id: int, to_user_id: int) -> MessagingGateResult:
    """Centralized server-side permission logic.

    Rules:
    - Both users must have profiles.
    - Match score (dynamic) must be >= 90.
    - Interest status must be accepted (either direction).

    IMPORTANT: This function MUST be used server-side before
    reading/returning any messages to avoid data leakage.
    """

    from_profile = models.get_profile_by_user_id(db_path, from_user_id)
    to_profile = models.get_profile_by_user_id(db_path, to_user_id)
    if not from_profile or not to_profile:
        return MessagingGateResult(allowed=False, score=0, interest_status=None)

    score, _ = calculate_match_score(from_profile, to_profile)

    interest_info = models.get_interest_status(db_path, from_user_id, to_user_id)
    status = interest_info["status"] if interest_info else None

    allowed = bool(score >= 90 and status == "accepted")
    return MessagingGateResult(allowed=allowed, score=int(score), interest_status=status)
