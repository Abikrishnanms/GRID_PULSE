"""
GridPulse - Personalised Appliance Energy Recommendation Engine
Member 3 Contribution: Energy Intelligence & Recommendation Module

Pure Python recommendation service for appliance energy ranking, high-impact identification,
and explainable hypothetical energy-saving suggestions.

Key Principles:
1. Aligned with established 30-day monthly consumption formula.
2. Unrounded calculations internally; formatted upon presentation.
3. Decoupled rate handling: no silent default rates; cost is None if rate is unavailable.
4. Continuous appliances (e.g. refrigerators >= 20h/day) never receive runtime reductions.
5. Low-impact appliances (< 5% share) appear in rankings but have reductions suppressed.
6. Savings are strictly hypothetical scenarios, never guaranteed actuals.
"""

from copy import deepcopy
import math
from typing import Any, Dict, List, Optional, Tuple

DAYS_PER_MONTH = 30


def validate_appliance(appliance: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a single appliance record.
    Invalid records are flagged with descriptive reasons and never silently coerced.
    """
    reasons = []

    if not isinstance(appliance, dict):
        return False, ["Appliance record must be a dictionary."]

    name = appliance.get("name")
    if not isinstance(name, str) or not name.strip():
        reasons.append("Appliance name must be a non-empty string.")

    wattage = appliance.get("wattage")
    if wattage is None or isinstance(wattage, bool) or not isinstance(wattage, (int, float)):
        reasons.append("Wattage must be a numeric value.")
    elif not math.isfinite(wattage) or wattage <= 0:
        reasons.append("Wattage must be a positive, finite number (> 0).")

    quantity = appliance.get("quantity", 1)
    if quantity is None or isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
        reasons.append("Quantity must be a positive integer.")
    elif not math.isfinite(quantity) or quantity < 1 or not float(quantity).is_integer():
        reasons.append("Quantity must be an integer >= 1.")

    hours = appliance.get("hoursPerDay")
    if hours is None or isinstance(hours, bool) or not isinstance(hours, (int, float)):
        reasons.append("hoursPerDay must be a numeric value.")
    elif not math.isfinite(hours) or hours < 0 or hours > 24:
        reasons.append("hoursPerDay must be between 0.0 and 24.0.")

    days = appliance.get("daysPerWeek", 7)
    if days is None or isinstance(days, bool) or not isinstance(days, (int, float)):
        reasons.append("daysPerWeek must be a numeric value.")
    elif not math.isfinite(days) or days < 1 or days > 7:
        reasons.append("daysPerWeek must be between 1.0 and 7.0.")

    return len(reasons) == 0, reasons


def calculate_appliance_consumption(appliance: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates daily, weekly, and monthly electricity consumption for an appliance in kWh.
    Assumes a standard 30-day month. Returns unrounded float values.
    """
    wattage = float(appliance["wattage"])
    quantity = float(appliance.get("quantity", 1))
    hours_per_day = float(appliance.get("hoursPerDay", 0))
    days_per_week = float(appliance.get("daysPerWeek", 7))

    # Daily average smoothed over a 7-day week
    daily_kwh = (wattage * quantity * hours_per_day * days_per_week) / 7.0 / 1000.0
    weekly_kwh = daily_kwh * 7.0
    monthly_kwh = daily_kwh * DAYS_PER_MONTH

    return {
        "daily_kwh": daily_kwh,
        "weekly_kwh": weekly_kwh,
        "monthly_kwh": monthly_kwh,
    }


def rank_appliances_by_consumption(
    valid_appliances: List[Dict[str, Any]],
    total_household_kwh: float,
    electricity_rate: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Ranks appliances by monthly consumption in descending order.
    Preserves original input order for ties (stable sort).
    Computes exact percentage contribution to total household appliance consumption.
    """
    ranked_list = []

    for index, app in enumerate(valid_appliances):
        consumption = calculate_appliance_consumption(app)
        monthly_kwh = consumption["monthly_kwh"]

        if total_household_kwh > 0:
            percentage_share = (monthly_kwh / total_household_kwh) * 100.0
        else:
            percentage_share = 0.0

        if electricity_rate is not None and isinstance(electricity_rate, (int, float)) and electricity_rate > 0 and math.isfinite(electricity_rate):
            monthly_cost: Optional[float] = monthly_kwh * float(electricity_rate)
        else:
            monthly_cost = None

        ranked_list.append({
            "original_index": index,
            "id": app.get("id", f"app-{index + 1}"),
            "name": app["name"].strip(),
            "wattage": float(app["wattage"]),
            "quantity": int(app.get("quantity", 1)),
            "hoursPerDay": float(app.get("hoursPerDay", 0)),
            "daysPerWeek": float(app.get("daysPerWeek", 7)),
            "consumption": consumption,
            "percentage_of_total": percentage_share,
            "monthly_cost": monthly_cost,
        })

    # Stable sort descending by monthly_kwh
    ranked_list.sort(key=lambda item: item["consumption"]["monthly_kwh"], reverse=True)

    # Assign ranks (1-based)
    for rank, item in enumerate(ranked_list, start=1):
        item["rank"] = rank

    return ranked_list


def identify_high_impact_appliances(
    ranked_appliances: List[Dict[str, Any]],
    threshold_percent: float = 20.0,
    threshold_kwh: float = 30.0,
) -> List[Dict[str, Any]]:
    """
    Identifies high-impact appliances that dominate household energy consumption.
    An appliance is high impact if its share >= threshold_percent OR monthly_kwh >= threshold_kwh.
    """
    high_impact = []
    for item in ranked_appliances:
        share = item["percentage_of_total"]
        monthly_kwh = item["consumption"]["monthly_kwh"]
        if share >= threshold_percent or monthly_kwh >= threshold_kwh:
            high_impact.append(item)
    return high_impact


def is_continuous_appliance(appliance: Dict[str, Any]) -> bool:
    """
    Determines if an appliance is continuous / essential (e.g. refrigerator/freezer or >= 20h/day).
    """
    hours = float(appliance.get("hoursPerDay", 0))
    name = appliance.get("name", "").lower()
    continuous_keywords = ["refrigerator", "fridge", "freezer", "medical", "aquarium"]

    if hours >= 20.0:
        return True
    if any(keyword in name for keyword in continuous_keywords):
        return True
    return False


def generate_usage_reduction_suggestion(
    ranked_item: Dict[str, Any],
    electricity_rate: Optional[float] = None,
    low_impact_threshold_percent: float = 5.0,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Generates a realistic, hypothetical usage-reduction suggestion for an appliance.
    Returns a tuple of (actionable_recommendation, suppression_info):
    - If continuous appliance: runtime reduction is suppressed for safety.
    - If below low-impact threshold (< 5%): reduction is suppressed to avoid alert fatigue.
    - Otherwise: returns an actionable hypothetical scenario with exact delta kWh and delta cost.
    """
    app_id = ranked_item["id"]
    name = ranked_item["name"]
    wattage = ranked_item["wattage"]
    hours = ranked_item["hoursPerDay"]
    days = ranked_item["daysPerWeek"]
    share = ranked_item["percentage_of_total"]
    current_monthly_kwh = ranked_item["consumption"]["monthly_kwh"]

    # Rule 1: Continuous Appliance Safety
    if is_continuous_appliance(ranked_item):
        suppression = {
            "appliance_id": app_id,
            "appliance_name": name,
            "status": "No Runtime Reduction",
            "reason": (
                f"Continuous/essential appliance ({hours:.1f} hrs/day). "
                "Operating duration must not be reduced for food safety or functional continuity. "
                "Ensure clean condenser coils and proper door seals for passive efficiency."
            ),
        }
        return None, suppression

    # Rule 2: Low-Impact Threshold Suppression (< 5%)
    if share < low_impact_threshold_percent:
        suppression = {
            "appliance_id": app_id,
            "appliance_name": name,
            "status": "Low Impact Suppressed",
            "reason": (
                f"Contributes only {share:.2f}% of total appliance consumption. "
                "Usage reduction would yield negligible energy savings and is suppressed."
            ),
        }
        return None, suppression

    # Rule 3: Formulate Practical Reduction Scenario
    proposed_hours = hours
    proposed_days = days
    scenario_type = "Runtime Optimization"
    action_title = "Moderate Daily Runtime"
    action_detail = ""

    # High wattage climate/cooling/heating (> 1000W)
    if wattage >= 1000.0 and hours >= 2.0:
        reduction_hours = 1.5 if hours >= 4.0 else 1.0
        proposed_hours = max(0.5, hours - reduction_hours)
        scenario_type = "Daily Runtime Adjustment"
        action_title = f"Reduce daily operation by {reduction_hours:.1f} hrs"
        action_detail = (
            f"Hypothetical scenario: Setting a timer or adjusting the thermostat to curtail runtime "
            f"from {hours:.1f} to {proposed_hours:.1f} hours/day."
        )
    # High wattage short-duration heating (e.g. Geyser / Water Heater >= 1500W, 0.5 to 2.0 hrs)
    elif wattage >= 1500.0 and 0.5 <= hours < 2.0:
        reduction_hours = 0.5
        proposed_hours = max(0.5, hours - reduction_hours)
        scenario_type = "Pre-heating Optimization"
        action_title = "Reduce heating duration by 30 mins"
        action_detail = (
            f"Hypothetical scenario: Turning off the heater 30 minutes earlier and relying on residual "
            f"tank heat, reducing daily usage from {hours:.1f} to {proposed_hours:.1f} hours."
        )
    # High frequency batch load (daysPerWeek >= 5 and wattage >= 300W, e.g. Washing Machine)
    elif days >= 5 and wattage >= 300.0:
        reduction_days = 2
        proposed_days = max(1, days - reduction_days)
        scenario_type = "Load Consolidation"
        action_title = f"Consolidate use to {proposed_days} days/week"
        action_detail = (
            f"Hypothetical scenario: Running full batches {proposed_days} days/week instead of "
            f"{days} days/week (-{reduction_days} days)."
        )
    # General active appliance
    else:
        reduction_hours = max(0.5, round(hours * 0.25, 1))
        proposed_hours = max(0.5, hours - reduction_hours)
        scenario_type = "Usage Reduction"
        action_title = f"Reduce daily runtime by {reduction_hours:.1f} hrs"
        action_detail = (
            f"Hypothetical scenario: Trimming daily operation from {hours:.1f} to {proposed_hours:.1f} hours."
        )

    # Compute proposed consumption using identical formula
    proposed_appliance = deepcopy(ranked_item)
    proposed_appliance["hoursPerDay"] = proposed_hours
    proposed_appliance["daysPerWeek"] = proposed_days

    proposed_consumption = calculate_appliance_consumption(proposed_appliance)
    proposed_monthly_kwh = proposed_consumption["monthly_kwh"]
    saved_kwh = max(0.0, current_monthly_kwh - proposed_monthly_kwh)

    # Cost savings (only if rate is valid)
    if electricity_rate is not None and isinstance(electricity_rate, (int, float)) and electricity_rate > 0 and math.isfinite(electricity_rate):
        cost_savings: Optional[float] = saved_kwh * float(electricity_rate)
    else:
        cost_savings = None

    actionable = {
        "appliance_id": app_id,
        "appliance_name": name,
        "trigger_reason": f"Accounts for {share:.2f}% of household electricity ({current_monthly_kwh:.2f} kWh/month)",
        "scenario_type": scenario_type,
        "current_usage": f"{hours:.1f} hrs/day · {days} days/week",
        "proposed_usage": f"{proposed_hours:.1f} hrs/day · {proposed_days} days/week",
        "action_title": action_title,
        "action_detail": action_detail,
        "hypothetical_savings_kwh": saved_kwh,
        "hypothetical_cost_savings": cost_savings,
    }

    return actionable, None


def generate_household_recommendation_report(
    appliances: List[Dict[str, Any]],
    electricity_rate: Optional[float] = None,
    low_impact_threshold_percent: float = 5.0,
    high_impact_threshold_percent: float = 20.0,
) -> Dict[str, Any]:
    """
    Main recommendation engine pipeline.
    Validates inputs, ranks appliances, identifies high-impact loads, and generates
    transparent, hypothetical energy reduction scenarios.
    """
    # 1. Rate validation
    is_rate_valid = (
        electricity_rate is not None
        and isinstance(electricity_rate, (int, float))
        and not isinstance(electricity_rate, bool)
        and math.isfinite(electricity_rate)
        and electricity_rate > 0
    )
    validated_rate = float(electricity_rate) if is_rate_valid else None
    rate_status = "valid" if is_rate_valid else "unavailable"

    # 2. Separate valid and invalid appliances
    valid_appliances = []
    invalid_appliances = []

    if isinstance(appliances, list):
        for index, item in enumerate(appliances):
            is_valid, reasons = validate_appliance(item)
            if is_valid:
                valid_appliances.append(item)
            else:
                invalid_appliances.append({
                    "record_index": index,
                    "raw_data": item,
                    "validation_reasons": reasons,
                })

    # 3. Handle empty valid list
    if not valid_appliances:
        return {
            "summary": {
                "total_appliances_submitted": len(appliances) if isinstance(appliances, list) else 0,
                "valid_appliances_count": 0,
                "invalid_appliances_count": len(invalid_appliances),
                "total_monthly_kwh": 0.0,
                "total_monthly_cost": None if not is_rate_valid else 0.0,
                "electricity_rate": validated_rate,
                "rate_status": rate_status,
                "total_hypothetical_savings_kwh": 0.0,
                "total_hypothetical_cost_savings": None if not is_rate_valid else 0.0,
                "potential_reduction_percent": 0.0,
                "message": "No valid appliances registered to analyze.",
            },
            "ranked_appliances": [],
            "high_impact_appliances": [],
            "actionable_recommendations": [],
            "suppressed_or_informational": [],
            "invalid_appliances": invalid_appliances,
        }

    # 4. Calculate total household monthly consumption
    total_household_monthly_kwh = sum(
        calculate_appliance_consumption(app)["monthly_kwh"]
        for app in valid_appliances
    )

    total_household_cost = (
        total_household_monthly_kwh * validated_rate
        if is_rate_valid
        else None
    )

    # 5. Rank all appliances
    ranked = rank_appliances_by_consumption(
        valid_appliances,
        total_household_monthly_kwh,
        validated_rate,
    )

    # 6. Identify high impact appliances
    high_impact = identify_high_impact_appliances(
        ranked,
        threshold_percent=high_impact_threshold_percent,
    )

    # 7. Generate recommendations
    actionable_recs = []
    suppressed_info = []

    for item in ranked:
        actionable, suppressed = generate_usage_reduction_suggestion(
            item,
            electricity_rate=validated_rate,
            low_impact_threshold_percent=low_impact_threshold_percent,
        )
        if actionable:
            actionable_recs.append(actionable)
        if suppressed:
            suppressed_info.append(suppressed)

    # 8. Compute total hypothetical savings
    total_savings_kwh = sum(rec["hypothetical_savings_kwh"] for rec in actionable_recs)

    if is_rate_valid:
        total_cost_savings: Optional[float] = total_savings_kwh * validated_rate
    else:
        total_cost_savings = None

    if total_household_monthly_kwh > 0:
        potential_reduction_pct = (total_savings_kwh / total_household_monthly_kwh) * 100.0
    else:
        potential_reduction_pct = 0.0

    # 9. Assemble final report
    return {
        "summary": {
            "total_appliances_submitted": len(appliances),
            "valid_appliances_count": len(valid_appliances),
            "invalid_appliances_count": len(invalid_appliances),
            "total_monthly_kwh": round(total_household_monthly_kwh, 4),
            "total_monthly_cost": round(total_household_cost, 2) if total_household_cost is not None else None,
            "electricity_rate": validated_rate,
            "rate_status": rate_status,
            "total_hypothetical_savings_kwh": round(total_savings_kwh, 4),
            "total_hypothetical_cost_savings": round(total_cost_savings, 2) if total_cost_savings is not None else None,
            "potential_reduction_percent": round(potential_reduction_pct, 2),
        },
        "ranked_appliances": [
            {
                "rank": item["rank"],
                "id": item["id"],
                "name": item["name"],
                "monthly_kwh": round(item["consumption"]["monthly_kwh"], 4),
                "percentage_of_total": round(item["percentage_of_total"], 2),
                "monthly_cost": round(item["monthly_cost"], 2) if item["monthly_cost"] is not None else None,
                "daily_kwh": round(item["consumption"]["daily_kwh"], 4),
            }
            for item in ranked
        ],
        "high_impact_appliances": [item["name"] for item in high_impact],
        "actionable_recommendations": [
            {
                "appliance_id": rec["appliance_id"],
                "appliance_name": rec["appliance_name"],
                "action_title": rec["action_title"],
                "scenario_type": rec["scenario_type"],
                "trigger_reason": rec["trigger_reason"],
                "current_usage": rec["current_usage"],
                "proposed_usage": rec["proposed_usage"],
                "action_detail": rec["action_detail"],
                "hypothetical_savings_kwh": round(rec["hypothetical_savings_kwh"], 4),
                "hypothetical_cost_savings": round(rec["hypothetical_cost_savings"], 2) if rec["hypothetical_cost_savings"] is not None else None,
            }
            for rec in actionable_recs
        ],
        "suppressed_or_informational": suppressed_info,
        "invalid_appliances": invalid_appliances,
    }
