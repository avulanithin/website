from __future__ import annotations

from typing import Dict, Iterable


def _is_filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def calculate_profile_completion(profile: Dict) -> int:
    """Compute profile completion percentage dynamically.

    IMPORTANT:
    - This is calculated at request time, never stored in DB.
    - It uses only existing DB columns (no renames).

    Scoring approach (simple + explainable):
    - Each important field contributes equally.
    - Image is optional but counted to encourage upload.
    """

    fields: Iterable[str] = [
        # Personal
        "full_name",
        "age",
        "gender",
        "height_cm",
        "marital_status",
        "location",
        # Education & job
        "highest_education",
        "occupation",
        "income_range",
        # Health & lifestyle
        "smoking",
        "drinking",
        "medical_conditions",
        "fitness_level",
        # Preferences
        "pref_age_min",
        "pref_age_max",
        "pref_location",
        "pref_education_level",
        # Image (optional)
        "image_filename",
    ]

    total = 0
    filled = 0
    for f in fields:
        total += 1
        if _is_filled((profile or {}).get(f)):
            filled += 1

    if total == 0:
        return 0

    return int(round((filled / total) * 100))
