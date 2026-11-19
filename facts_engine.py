"""Shared fact normalization, validation and incremental-update rules."""

from __future__ import annotations

import math


KEY_ALIASES = {
    "duration": "duration_hours",
    "event_duration": "duration_hours",
    "break_time": "prayer_break_minutes",
    "break_duration": "prayer_break_minutes",
    "honorarium": "judge_honorarium",
    "judging_time": "judging_time_per_team",
    "minutes_per_team": "judging_time_per_team",
    "service_charge_percent": "service_charge_percentage",
    "vendor_quote": "extra_cost",
}

BOOLEAN_KEYS = {"step_free_required", "venue_step_free", "venue_unavailable"}
AREAS = {"venue", "schedule", "food", "judging", "budget"}


def normalized_entity(value):
    return " ".join(str(value or "").strip().casefold().split())


def normalize_fact(fact):
    """Normalize a copy; preserve its evidence and original source."""
    result = dict(fact)
    result["key"] = KEY_ALIASES.get(result.get("key"), result.get("key"))
    value = result.get("value")
    if isinstance(value, str):
        compact = value.strip().replace(",", "")
        if compact.isdecimal():
            result["value"] = int(compact)
    if isinstance(result.get("entity"), str):
        result["entity"] = result["entity"].strip()
    return result


def merge_facts(existing, incoming):
    """Latest message wins for the same key/entity, including paid expenses.

    Different expense entities (e.g. trophies and banners) remain separate.
    The caller retains earlier evidence separately in its trace/history.
    """
    merged = [normalize_fact(f) for f in existing]
    for raw_fact in incoming:
        new = normalize_fact(raw_fact)
        identity = (new.get("key"), normalized_entity(new.get("entity")))
        merged = [
            old for old in merged
            if (old.get("key"), normalized_entity(old.get("entity"))) != identity
        ]
        merged.append(new)
    return merged


def validate_facts(facts):
    errors = []
    if not isinstance(facts, list):
        return ["The facts field must be a list"]
    for index, fact in enumerate(facts, 1):
        if not isinstance(fact, dict):
            errors.append(f"Fact {index}: Expected an object")
            continue
        if fact.get("area") not in AREAS:
            errors.append(f"Fact {index}: Invalid area")
        if not isinstance(fact.get("key"), str) or not fact["key"].strip():
            errors.append(f"Fact {index}: Missing key")
        if not fact.get("detail"):
            errors.append(f"Fact {index}: Missing detail")
        if not fact.get("source"):
            errors.append(f"Fact {index}: Missing source")
        value = fact.get("value")
        if value is None:
            continue  # Explicit unknowns are allowed, not silently guessed.
        if fact.get("key") in BOOLEAN_KEYS:
            if type(value) is not bool:
                errors.append(f"Fact {index}: Expected true or false")
        elif type(value) not in (int, float) or not math.isfinite(value):
            errors.append(f"Fact {index}: Invalid numeric value")
        elif value < 0:
            errors.append(f"Fact {index}: Negative values are not valid for {fact.get('key')}")
        elif fact.get("key") in {"team_size", "duration_hours", "max_teams_per_judge", "judging_time_per_team"} and value == 0:
            errors.append(f"Fact {index}: {fact.get('key')} must be greater than zero")
    return errors
