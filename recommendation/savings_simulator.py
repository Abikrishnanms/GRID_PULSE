"""
GridPulse - Personalised Energy Savings Simulator
Member 3 Contribution: Energy Intelligence & Simulation Module

Provides interactive, what-if energy savings simulations for household appliances.
Reuses established 30-day consumption calculations and validation logic from appliance_recommender.py.

Key Guarantees:
1. Pure, non-mutating calculations (baseline data is strictly preserved).
2. Strict atomic validation: invalid adjustments are rejected without partial application.
3. Accurate consumption and savings math (513.0 baseline, 415.5 simulated, 97.5 savings).
4. Continuous appliance safety: warns when a continuous load is manually reduced.
5. Clear consumption impact labels: reduced_consumption, unchanged_consumption, increased_consumption.
6. Decoupled electricity rate: monetary figures are None when rate is unavailable.
"""

from copy import deepcopy
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from recommendation.appliance_recommender import (
    DAYS_PER_MONTH,
    calculate_appliance_consumption,
    is_continuous_appliance,
    validate_appliance,
)


def validate_scenario_adjustments(
    baseline_appliances: List[Dict[str, Any]],
    adjustments: List[Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates user scenario adjustments against baseline appliances.
    Guarantees:
    - Baseline appliances must have valid, non-empty, unique IDs.
    - Adjustments must match an existing appliance ID.
    - Duplicate adjustments for the same appliance ID are rejected.
    - Immutable fields (wattage, quantity, name, id) cannot be modified.
    - proposed_hours_per_day must be float/int in [0.0, 24.0] (no bools, NaN, inf).
    - proposed_days_per_week must be strict integer in [1, 7] (no bools, NaN, inf, floats).
    - Atomically validates each adjustment (never partially applies invalid adjustments).
    - Flags safety warnings if a continuous appliance is reduced below safe continuous levels.
    """
    valid_adjustments: Dict[str, Dict[str, Any]] = {}
    safety_warnings: List[Dict[str, Any]] = []
    adjustment_errors: List[Dict[str, Any]] = []

    # 1. Index baseline appliances by ID and check uniqueness
    baseline_map: Dict[str, Dict[str, Any]] = {}
    baseline_ids_seen: Set[str] = set()

    for idx, app in enumerate(baseline_appliances):
        if not isinstance(app, dict):
            adjustment_errors.append({
                "record_type": "baseline",
                "index": idx,
                "error": "Baseline appliance record must be a dictionary.",
            })
            continue

        app_id = app.get("id")
        if not isinstance(app_id, str) or not app_id.strip():
            adjustment_errors.append({
                "record_type": "baseline",
                "index": idx,
                "error": "Baseline appliance is missing a valid non-empty string 'id'.",
            })
            continue

        clean_id = app_id.strip()
        if clean_id in baseline_ids_seen:
            adjustment_errors.append({
                "record_type": "baseline",
                "index": idx,
                "appliance_id": clean_id,
                "error": f"Duplicate baseline appliance ID '{clean_id}' detected.",
            })
            continue

        baseline_ids_seen.add(clean_id)
        baseline_map[clean_id] = app

    # 2. Validate Adjustments list
    if not isinstance(adjustments, list):
        adjustment_errors.append({
            "record_type": "adjustment",
            "error": "Adjustments must be provided as a list of dictionaries.",
        })
        return valid_adjustments, safety_warnings, adjustment_errors

    seen_adj_ids: Set[str] = set()

    for adj_idx, adj in enumerate(adjustments):
        if not isinstance(adj, dict):
            adjustment_errors.append({
                "record_type": "adjustment",
                "index": adj_idx,
                "error": "Adjustment item must be a dictionary.",
            })
            continue

        # Extract target appliance ID
        raw_id = adj.get("appliance_id") or adj.get("id")
        if not isinstance(raw_id, str) or not raw_id.strip():
            adjustment_errors.append({
                "record_type": "adjustment",
                "index": adj_idx,
                "error": "Adjustment is missing a valid non-empty string 'appliance_id' or 'id'.",
            })
            continue

        target_id = raw_id.strip()

        # Check for duplicate adjustments targeting the exact same appliance
        if target_id in seen_adj_ids:
            adjustment_errors.append({
                "record_type": "adjustment",
                "index": adj_idx,
                "appliance_id": target_id,
                "error": f"Duplicate adjustment for appliance ID '{target_id}' detected.",
            })
            # If a duplicate occurs, invalidate any previously stored entry for this target_id (atomic rejection)
            valid_adjustments.pop(target_id, None)
            continue

        seen_adj_ids.add(target_id)

        # Check if appliance exists in baseline
        if target_id not in baseline_map:
            adjustment_errors.append({
                "record_type": "adjustment",
                "index": adj_idx,
                "appliance_id": target_id,
                "error": f"Target appliance ID '{target_id}' not found in baseline appliances.",
            })
            continue

        baseline_app = baseline_map[target_id]
        reasons: List[str] = []

        # Check immutable fields: wattage and quantity must NOT be modified
        for immutable in ["wattage", "quantity", "name"]:
            if immutable in adj:
                val = adj[immutable]
                base_val = baseline_app.get(immutable)
                if val != base_val:
                    reasons.append(
                        f"Field '{immutable}' is immutable in usage simulation and cannot be changed."
                    )

        # Validate proposed hours per day
        has_hours = "proposed_hours_per_day" in adj or "hoursPerDay" in adj
        prop_hours = adj.get("proposed_hours_per_day", adj.get("hoursPerDay"))

        if has_hours:
            if prop_hours is None or isinstance(prop_hours, bool) or not isinstance(prop_hours, (int, float)):
                reasons.append("proposed_hours_per_day must be a numeric value.")
            elif not math.isfinite(prop_hours) or prop_hours < 0.0 or prop_hours > 24.0:
                reasons.append("proposed_hours_per_day must be between 0.0 and 24.0.")

        # Validate proposed days per week (must be a strict integer in [1, 7])
        has_days = "proposed_days_per_week" in adj or "daysPerWeek" in adj
        prop_days = adj.get("proposed_days_per_week", adj.get("daysPerWeek"))

        if has_days:
            # Reject booleans, floats, strings, NaN, infinity
            if prop_days is None or isinstance(prop_days, bool) or not isinstance(prop_days, int):
                reasons.append("proposed_days_per_week must be a strict integer between 1 and 7.")
            elif prop_days < 1 or prop_days > 7:
                reasons.append("proposed_days_per_week must be an integer between 1 and 7.")

        if not has_hours and not has_days:
            reasons.append("Adjustment must specify at least proposed_hours_per_day or proposed_days_per_week.")

        # Atomic rejection if any validation reasons exist
        if reasons:
            adjustment_errors.append({
                "record_type": "adjustment",
                "index": adj_idx,
                "appliance_id": target_id,
                "error": "; ".join(reasons),
            })
            continue

        # Continuous appliance safety inspection
        final_hours = float(prop_hours) if has_hours else float(baseline_app.get("hoursPerDay", 0))
        if is_continuous_appliance(baseline_app) and final_hours < float(baseline_app.get("hoursPerDay", 0)):
            safety_warnings.append({
                "appliance_id": target_id,
                "appliance_name": baseline_app.get("name", "Unknown"),
                "baseline_hours": float(baseline_app.get("hoursPerDay", 0)),
                "proposed_hours": final_hours,
                "warning": (
                    f"Continuous food preservation or essential appliance '{baseline_app.get('name')}' "
                    f"adjusted from {baseline_app.get('hoursPerDay')} to {final_hours} hrs/day. "
                    "Reducing refrigeration or critical device runtime may cause food spoilage or functional risk."
                ),
            })

        valid_adjustments[target_id] = {
            "proposed_hours_per_day": float(prop_hours) if has_hours else float(baseline_app.get("hoursPerDay", 0)),
            "proposed_days_per_week": int(prop_days) if has_days else int(baseline_app.get("daysPerWeek", 7)),
        }

    return valid_adjustments, safety_warnings, adjustment_errors


def simulate_household_savings(
    baseline_appliances: List[Dict[str, Any]],
    adjustments: List[Dict[str, Any]],
    electricity_rate: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Simulates what-if household electricity consumption and energy/cost savings.
    Preserves baseline appliances immutably.
    Calculates exact kWh delta, percentage reduction, and monetary savings.
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

    # 2. Validate adjustments and index baseline safely
    valid_adjustments, safety_warnings, adjustment_errors = validate_scenario_adjustments(
        baseline_appliances, adjustments
    )

    # 3. Filter valid baseline appliances
    valid_baseline: List[Dict[str, Any]] = []
    for app in baseline_appliances:
        if isinstance(app, dict) and app.get("id") and validate_appliance(app)[0]:
            valid_baseline.append(app)

    if not valid_baseline:
        return {
            "summary": {
                "baseline_monthly_kwh": 0.0,
                "simulated_monthly_kwh": 0.0,
                "net_monthly_savings_kwh": 0.0,
                "percentage_reduction": 0.0,
                "consumption_impact": "unchanged_consumption",
                "electricity_rate": validated_rate,
                "rate_status": rate_status,
                "baseline_monthly_cost": 0.0 if is_rate_valid else None,
                "simulated_monthly_cost": 0.0 if is_rate_valid else None,
                "net_monthly_cost_savings": 0.0 if is_rate_valid else None,
                "total_appliances": 0,
                "adjusted_appliances_count": 0,
                "unmodified_appliances_count": 0,
                "scenario_label": "Hypothetical User Simulation",
                "message": "No valid baseline appliances available to simulate.",
            },
            "appliance_breakdown": [],
            "safety_warnings": safety_warnings,
            "adjustment_errors": adjustment_errors,
        }

    # 4. Construct simulated appliances (non-mutating)
    appliance_breakdown: List[Dict[str, Any]] = []
    baseline_total_kwh = 0.0
    simulated_total_kwh = 0.0
    adjusted_count = 0
    unmodified_count = 0

    for original_app in valid_baseline:
        app_id = original_app["id"].strip()
        sim_app = deepcopy(original_app)

        base_consumption = calculate_appliance_consumption(original_app)
        base_monthly = base_consumption["monthly_kwh"]
        base_daily = base_consumption["daily_kwh"]
        baseline_total_kwh += base_monthly

        if app_id in valid_adjustments:
            adjusted_count += 1
            status = "Adjusted"
            adj_data = valid_adjustments[app_id]
            sim_app["hoursPerDay"] = adj_data["proposed_hours_per_day"]
            sim_app["daysPerWeek"] = adj_data["proposed_days_per_week"]
        else:
            unmodified_count += 1
            status = "Unmodified"

        sim_consumption = calculate_appliance_consumption(sim_app)
        sim_monthly = sim_consumption["monthly_kwh"]
        sim_daily = sim_consumption["daily_kwh"]
        simulated_total_kwh += sim_monthly

        savings_kwh = base_monthly - sim_monthly

        if is_rate_valid:
            savings_cost: Optional[float] = savings_kwh * validated_rate
            base_cost: Optional[float] = base_monthly * validated_rate
            sim_cost: Optional[float] = sim_monthly * validated_rate
        else:
            savings_cost = None
            base_cost = None
            sim_cost = None

        if base_monthly > 0:
            percentage_change = ((sim_monthly - base_monthly) / base_monthly) * 100.0
        else:
            percentage_change = 0.0

        base_hours_str = f"{float(original_app.get('hoursPerDay', 0)):.1f} hrs/day · {int(original_app.get('daysPerWeek', 7))} days/week"
        sim_hours_str = f"{float(sim_app.get('hoursPerDay', 0)):.1f} hrs/day · {int(sim_app.get('daysPerWeek', 7))} days/week"

        appliance_breakdown.append({
            "appliance_id": app_id,
            "name": original_app["name"].strip(),
            "status": status,
            "baseline_usage": base_hours_str,
            "simulated_usage": sim_hours_str,
            "baseline_daily_kwh": round(base_daily, 4),
            "simulated_daily_kwh": round(sim_daily, 4),
            "baseline_monthly_kwh": round(base_monthly, 4),
            "simulated_monthly_kwh": round(sim_monthly, 4),
            "savings_kwh": round(savings_kwh, 4),
            "savings_cost": round(savings_cost, 2) if savings_cost is not None else None,
            "percentage_change": round(percentage_change, 2),
            "baseline_monthly_cost": round(base_cost, 2) if base_cost is not None else None,
            "simulated_monthly_cost": round(sim_cost, 2) if sim_cost is not None else None,
        })

    # 5. Calculate household totals & impact
    net_savings_kwh = baseline_total_kwh - simulated_total_kwh

    if baseline_total_kwh > 0:
        pct_reduction = (net_savings_kwh / baseline_total_kwh) * 100.0
    else:
        pct_reduction = 0.0

    # Categorize consumption impact clearly
    if round(net_savings_kwh, 4) > 0.0:
        consumption_impact = "reduced_consumption"
    elif round(net_savings_kwh, 4) < 0.0:
        consumption_impact = "increased_consumption"
    else:
        consumption_impact = "unchanged_consumption"

    if is_rate_valid:
        baseline_cost = baseline_total_kwh * validated_rate
        simulated_cost = simulated_total_kwh * validated_rate
        net_cost_savings: Optional[float] = net_savings_kwh * validated_rate
    else:
        baseline_cost = None
        simulated_cost = None
        net_cost_savings = None

    return {
        "summary": {
            "baseline_monthly_kwh": round(baseline_total_kwh, 4),
            "simulated_monthly_kwh": round(simulated_total_kwh, 4),
            "net_monthly_savings_kwh": round(net_savings_kwh, 4),
            "percentage_reduction": round(pct_reduction, 2),
            "consumption_impact": consumption_impact,
            "electricity_rate": validated_rate,
            "rate_status": rate_status,
            "baseline_monthly_cost": round(baseline_cost, 2) if baseline_cost is not None else None,
            "simulated_monthly_cost": round(simulated_cost, 2) if simulated_cost is not None else None,
            "net_monthly_cost_savings": round(net_cost_savings, 2) if net_cost_savings is not None else None,
            "total_appliances": len(valid_baseline),
            "adjusted_appliances_count": adjusted_count,
            "unmodified_appliances_count": unmodified_count,
            "scenario_label": "Hypothetical User Simulation",
        },
        "appliance_breakdown": appliance_breakdown,
        "safety_warnings": safety_warnings,
        "adjustment_errors": adjustment_errors,
    }


def simulate_from_recommendations(
    baseline_appliances: List[Dict[str, Any]],
    recommendations_data: Any,
    selected_appliance_ids: Optional[List[str]] = None,
    electricity_rate: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Bridge connecting recommendation engine outputs to the savings simulator.
    Accepts either:
    - Full report dict from generate_household_recommendation_report()
    - List of actionable recommendation dicts
    Parses proposed usage (e.g. '4.5 hrs/day · 7 days/week') and simulates the scenario.
    """
    # 1. Extract recommendations list
    recs_list: List[Dict[str, Any]] = []
    if isinstance(recommendations_data, dict):
        recs_list = recommendations_data.get("actionable_recommendations", [])
    elif isinstance(recommendations_data, list):
        recs_list = recommendations_data

    # 2. Convert recommendations to adjustments
    scenario_adjustments: List[Dict[str, Any]] = []
    selected_set = set(selected_appliance_ids) if selected_appliance_ids is not None else None

    for rec in recs_list:
        if not isinstance(rec, dict):
            continue

        target_id = rec.get("appliance_id") or rec.get("id")
        if not target_id:
            continue

        if selected_set is not None and target_id not in selected_set:
            continue

        # Look for explicit fields first, otherwise parse proposed_usage string
        proposed_hours = rec.get("proposed_hours_per_day")
        proposed_days = rec.get("proposed_days_per_week")

        if proposed_hours is None or proposed_days is None:
            usage_str = rec.get("proposed_usage", "")
            # Pattern matches e.g. "4.5 hrs/day · 7 days/week" or "4.5 hrs/day · 7.0 days/week"
            match = re.search(r"([\d\.]+)\s*hrs?/day\s*·\s*([\d\.]+)\s*days?/week", usage_str)
            if match:
                proposed_hours = float(match.group(1))
                proposed_days = int(round(float(match.group(2))))

        if proposed_hours is not None and proposed_days is not None:
            scenario_adjustments.append({
                "appliance_id": target_id,
                "proposed_hours_per_day": proposed_hours,
                "proposed_days_per_week": proposed_days,
            })

    # 3. Execute simulation
    return simulate_household_savings(
        baseline_appliances=baseline_appliances,
        adjustments=scenario_adjustments,
        electricity_rate=electricity_rate,
    )
