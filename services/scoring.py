from __future__ import annotations

from typing import Dict, Tuple


_EDU_RANK = {
    "high school": 1,
    "diploma": 2,
    "bachelors": 3,
    "masters": 4,
    "phd": 5,
}


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _education_score(a: Dict, b: Dict) -> float:
    """Education match: exact match best; nearby levels partial."""
    ra = _EDU_RANK.get(_norm(a.get("highest_education")), 0)
    rb = _EDU_RANK.get(_norm(b.get("highest_education")), 0)
    if ra == 0 or rb == 0:
        return 0.5
    if ra == rb:
        return 1.0
    diff = abs(ra - rb)
    return _clamp(1.0 - (diff * 0.25))


def _job_score(a: Dict, b: Dict) -> float:
    """Job match: occupation exact match else partial if same 'tech/design/etc'."""
    oa = _norm(a.get("occupation"))
    ob = _norm(b.get("occupation"))
    if not oa or not ob:
        return 0.5
    if oa == ob:
        return 1.0

    # Very simple grouping to keep the demo understandable.
    tech = {"software engineer", "developer", "data engineer", "data scientist"}
    design = {"designer", "ui designer", "ux designer"}
    business = {"manager", "sales", "marketing"}

    def group(o: str) -> str:
        if o in tech:
            return "tech"
        if o in design:
            return "design"
        if o in business:
            return "business"
        return "other"

    return 0.7 if group(oa) == group(ob) else 0.3


def _lifestyle_score(a: Dict, b: Dict) -> float:
    """Lifestyle match: smoking + drinking."""
    sa, sb = _norm(a.get("smoking")), _norm(b.get("smoking"))
    da, db = _norm(a.get("drinking")), _norm(b.get("drinking"))

    smoking_match = 1.0 if sa and sb and sa == sb else 0.5
    drinking_match = 1.0 if da and db and da == db else 0.5
    return (smoking_match + drinking_match) / 2.0


def _health_score(a: Dict, b: Dict) -> float:
    """Health match: medical conditions + fitness level."""
    ma, mb = _norm(a.get("medical_conditions")), _norm(b.get("medical_conditions"))
    fa, fb = _norm(a.get("fitness_level")), _norm(b.get("fitness_level"))

    medical_match = 1.0 if ma and mb and ma == mb else 0.5
    fitness_match = 1.0 if fa and fb and fa == fb else 0.5
    return (medical_match + fitness_match) / 2.0


def _preference_score(viewer: Dict, candidate: Dict) -> float:
    """Preference match from viewer's stored preferences.

    - Age range check
    - Preferred location check
    - Preferred education min level check

    This is intentionally simple for learning.
    """
    score = 0.0
    parts = 0

    # Age
    parts += 1
    try:
        age = int(candidate.get("age"))
        amin = int(viewer.get("pref_age_min"))
        amax = int(viewer.get("pref_age_max"))
        score += 1.0 if amin <= age <= amax else 0.0
    except Exception:
        score += 0.5

    # Location
    parts += 1
    pref_loc = _norm(viewer.get("pref_location"))
    cand_loc = _norm(candidate.get("location"))
    if pref_loc and cand_loc:
        score += 1.0 if pref_loc == cand_loc else 0.0
    else:
        score += 0.5

    # Education level (minimum)
    parts += 1
    pref_edu = _EDU_RANK.get(_norm(viewer.get("pref_education_level")), 0)
    cand_edu = _EDU_RANK.get(_norm(candidate.get("highest_education")), 0)
    if pref_edu and cand_edu:
        score += 1.0 if cand_edu >= pref_edu else 0.0
    else:
        score += 0.5

    return score / max(parts, 1)


def calculate_match_score(user_a: Dict, user_b: Dict) -> Tuple[int, Dict[str, int]]:
    """Calculate match score (0-100) with weighted components.

    Weights per requirements:
    - Education: 20
    - Job: 20
    - Lifestyle: 20
    - Health: 20
    - Preference: 20

    Returns:
        (total_percent_int, breakdown_dict)
    """
    education = _education_score(user_a, user_b)
    job = _job_score(user_a, user_b)
    lifestyle = _lifestyle_score(user_a, user_b)
    health = _health_score(user_a, user_b)
    preference = _preference_score(user_a, user_b)

    breakdown = {
        "education": round(education * 20),
        "job": round(job * 20),
        "lifestyle": round(lifestyle * 20),
        "health": round(health * 20),
        "preference": round(preference * 20),
    }
    total = int(sum(breakdown.values()))
    total = max(0, min(100, total))
    return total, breakdown
