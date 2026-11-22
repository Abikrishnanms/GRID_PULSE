"""
GridPulse - Unit Tests for Personalised Energy Savings Simulator
Member 3 Contribution: Energy Intelligence & Simulation Module

Uses Python's built-in unittest framework (zero external packages required).
"""

from copy import deepcopy
import math
import unittest

from recommendation.appliance_recommender import (
    generate_household_recommendation_report,
)
from recommendation.savings_simulator import (
    simulate_from_recommendations,
    simulate_household_savings,
    validate_scenario_adjustments,
)


class TestSavingsSimulator(unittest.TestCase):
    def setUp(self):
        """Standard baseline household suite approved in design."""
        self.baseline_appliances = [
            {
                "id": "a1",
                "name": "Air Conditioner",
                "wattage": 1500,
                "quantity": 1,
                "hoursPerDay": 6.0,
                "daysPerWeek": 7,
            },
            {
                "id": "a2",
                "name": "Refrigerator",
                "wattage": 200,
                "quantity": 1,
                "hoursPerDay": 24.0,
                "daysPerWeek": 7,
            },
            {
                "id": "a3",
                "name": "Water Heater",
                "wattage": 2000,
                "quantity": 1,
                "hoursPerDay": 1.5,
                "daysPerWeek": 7,
            },
            {
                "id": "a4",
                "name": "LED Bulbs",
                "wattage": 10,
                "quantity": 5,
                "hoursPerDay": 6.0,
                "daysPerWeek": 7,
            },
        ]
        self.standard_rate = 8.0

    # ---------------------------------------------------------
    # Test 1: Water heater standalone adjustment
    # ---------------------------------------------------------
    def test_water_heater_standalone_adjustment(self):
        # Water heater reduced from 1.5h to 1.0h, 7 days/week
        adjustments = [
            {"appliance_id": "a3", "proposed_hours_per_day": 1.0, "proposed_days_per_week": 7}
        ]
        result = simulate_household_savings(
            self.baseline_appliances, adjustments, electricity_rate=self.standard_rate
        )
        summary = result["summary"]
        self.assertAlmostEqual(summary["baseline_monthly_kwh"], 513.0, places=4)
        self.assertAlmostEqual(summary["simulated_monthly_kwh"], 483.0, places=4)
        self.assertAlmostEqual(summary["net_monthly_savings_kwh"], 30.0, places=4)
        self.assertAlmostEqual(summary["net_monthly_cost_savings"], 240.0, places=2)
        self.assertEqual(summary["consumption_impact"], "reduced_consumption")

        # Check breakdown
        wh_item = next(item for item in result["appliance_breakdown"] if item["appliance_id"] == "a3")
        self.assertEqual(wh_item["status"], "Adjusted")
        self.assertAlmostEqual(wh_item["baseline_monthly_kwh"], 90.0, places=4)
        self.assertAlmostEqual(wh_item["simulated_monthly_kwh"], 60.0, places=4)
        self.assertAlmostEqual(wh_item["savings_kwh"], 30.0, places=4)
        self.assertAlmostEqual(wh_item["savings_cost"], 240.0, places=2)

    # ---------------------------------------------------------
    # Test 2: Correct combined savings (AC + Water Heater)
    # ---------------------------------------------------------
    def test_correct_combined_savings(self):
        # AC: 6.0h -> 4.5h | Water Heater: 1.5h -> 1.0h
        adjustments = [
            {"appliance_id": "a1", "proposed_hours_per_day": 4.5, "proposed_days_per_week": 7},
            {"appliance_id": "a3", "proposed_hours_per_day": 1.0, "proposed_days_per_week": 7},
        ]
        result = simulate_household_savings(
            self.baseline_appliances, adjustments, electricity_rate=self.standard_rate
        )
        summary = result["summary"]

        # Assert exact mathematical figures
        self.assertAlmostEqual(summary["baseline_monthly_kwh"], 513.0, places=4)
        self.assertAlmostEqual(summary["simulated_monthly_kwh"], 415.5, places=4)
        self.assertAlmostEqual(summary["net_monthly_savings_kwh"], 97.5, places=4)
        self.assertAlmostEqual(summary["net_monthly_cost_savings"], 780.0, places=2)
        self.assertAlmostEqual(summary["percentage_reduction"], 19.01, places=2)

        self.assertAlmostEqual(summary["baseline_monthly_cost"], 4104.0, places=2)
        self.assertAlmostEqual(summary["simulated_monthly_cost"], 3324.0, places=2)
        self.assertEqual(summary["adjusted_appliances_count"], 2)
        self.assertEqual(summary["unmodified_appliances_count"], 2)

    # ---------------------------------------------------------
    # Test 3: Unmodified appliance preservation
    # ---------------------------------------------------------
    def test_unmodified_appliance_preservation(self):
        # Only adjust AC
        adjustments = [{"appliance_id": "a1", "proposed_hours_per_day": 4.5}]
        result = simulate_household_savings(self.baseline_appliances, adjustments)

        breakdown = {item["appliance_id"]: item for item in result["appliance_breakdown"]}

        # Refrigerator must remain strictly 144 kWh
        self.assertEqual(breakdown["a2"]["status"], "Unmodified")
        self.assertAlmostEqual(breakdown["a2"]["baseline_monthly_kwh"], 144.0, places=4)
        self.assertAlmostEqual(breakdown["a2"]["simulated_monthly_kwh"], 144.0, places=4)
        self.assertAlmostEqual(breakdown["a2"]["savings_kwh"], 0.0, places=4)

        # LED Bulbs must remain strictly 9 kWh
        self.assertEqual(breakdown["a4"]["status"], "Unmodified")
        self.assertAlmostEqual(breakdown["a4"]["baseline_monthly_kwh"], 9.0, places=4)
        self.assertAlmostEqual(breakdown["a4"]["simulated_monthly_kwh"], 9.0, places=4)
        self.assertAlmostEqual(breakdown["a4"]["savings_kwh"], 0.0, places=4)

    # ---------------------------------------------------------
    # Test 4: Strict integer days validation (1 to 7)
    # ---------------------------------------------------------
    def test_strict_integer_days_validation(self):
        # Reject non-integers, booleans, and out-of-range days
        bad_day_values = [4.5, True, False, 0, 8, -1, "5", float("nan"), float("inf")]
        for bad_val in bad_day_values:
            adjustments = [
                {"appliance_id": "a1", "proposed_hours_per_day": 4.0, "proposed_days_per_week": bad_val}
            ]
            valid_adj, warnings, errors = validate_scenario_adjustments(
                self.baseline_appliances, adjustments
            )
            self.assertEqual(len(valid_adj), 0, f"Expected rejection for days value: {bad_val}")
            self.assertEqual(len(errors), 1, f"Expected error for days value: {bad_val}")

    # ---------------------------------------------------------
    # Test 5: Duplicate adjustment rejection
    # ---------------------------------------------------------
    def test_duplicate_adjustment_rejection(self):
        # Two adjustments targeting the exact same appliance 'a1'
        adjustments = [
            {"appliance_id": "a1", "proposed_hours_per_day": 4.0},
            {"appliance_id": "a1", "proposed_hours_per_day": 5.0},
        ]
        valid_adj, warnings, errors = validate_scenario_adjustments(
            self.baseline_appliances, adjustments
        )
        # Duplicate must be rejected; neither should be applied
        self.assertNotIn("a1", valid_adj)
        self.assertTrue(any("Duplicate adjustment" in err["error"] for err in errors))

    # ---------------------------------------------------------
    # Test 6: Immutable field rejection (wattage, quantity, name)
    # ---------------------------------------------------------
    def test_immutable_field_rejection(self):
        # Attempt to change wattage
        bad_adjustments = [
            {"appliance_id": "a1", "proposed_hours_per_day": 4.0, "wattage": 2000},
            {"appliance_id": "a3", "proposed_hours_per_day": 1.0, "quantity": 2},
        ]
        for bad_adj in bad_adjustments:
            valid_adj, warnings, errors = validate_scenario_adjustments(
                self.baseline_appliances, [bad_adj]
            )
            self.assertEqual(len(valid_adj), 0)
            self.assertTrue(any("immutable" in err["error"] for err in errors))

    # ---------------------------------------------------------
    # Test 7: Atomic validation (no partial updates)
    # ---------------------------------------------------------
    def test_atomic_validation(self):
        # Valid hours (4.0), but invalid days (8 days/week)
        adjustment = {
            "appliance_id": "a1",
            "proposed_hours_per_day": 4.0,
            "proposed_days_per_week": 8,
        }
        valid_adj, warnings, errors = validate_scenario_adjustments(
            self.baseline_appliances, [adjustment]
        )
        self.assertEqual(len(valid_adj), 0)
        self.assertEqual(len(errors), 1)

        # In full simulation, AC must remain unmodified because adjustment was atomically rejected
        result = simulate_household_savings(self.baseline_appliances, [adjustment])
        ac_item = next(i for i in result["appliance_breakdown"] if i["appliance_id"] == "a1")
        self.assertEqual(ac_item["status"], "Unmodified")
        self.assertAlmostEqual(ac_item["simulated_monthly_kwh"], 270.0)

    # ---------------------------------------------------------
    # Test 8: Increased consumption labelling
    # ---------------------------------------------------------
    def test_increased_consumption_labelling(self):
        # AC increased from 6.0h to 8.0h/day
        adjustments = [{"appliance_id": "a1", "proposed_hours_per_day": 8.0}]
        result = simulate_household_savings(
            self.baseline_appliances, adjustments, electricity_rate=self.standard_rate
        )
        summary = result["summary"]

        # AC baseline: 270 kWh -> simulated: 360 kWh
        # Net savings: 513 - 603 = -90 kWh
        self.assertAlmostEqual(summary["baseline_monthly_kwh"], 513.0, places=4)
        self.assertAlmostEqual(summary["simulated_monthly_kwh"], 603.0, places=4)
        self.assertAlmostEqual(summary["net_monthly_savings_kwh"], -90.0, places=4)
        self.assertAlmostEqual(summary["net_monthly_cost_savings"], -720.0, places=2)
        self.assertAlmostEqual(summary["percentage_reduction"], -17.54, places=2)

        # Must be explicitly labelled increased_consumption
        self.assertEqual(summary["consumption_impact"], "increased_consumption")

    # ---------------------------------------------------------
    # Test 9: Continuous appliance safety warning
    # ---------------------------------------------------------
    def test_continuous_appliance_safety_warning(self):
        # User manually reduces Refrigerator from 24h to 12h
        adjustments = [{"appliance_id": "a2", "proposed_hours_per_day": 12.0}]
        result = simulate_household_savings(self.baseline_appliances, adjustments)

        # Calculation proceeds mathematically
        ref_item = next(i for i in result["appliance_breakdown"] if i["appliance_id"] == "a2")
        self.assertEqual(ref_item["status"], "Adjusted")
        self.assertAlmostEqual(ref_item["simulated_monthly_kwh"], 72.0, places=4)

        # Must generate explicit safety warning
        self.assertEqual(len(result["safety_warnings"]), 1)
        self.assertIn("food spoilage", result["safety_warnings"][0]["warning"].lower())

    # ---------------------------------------------------------
    # Test 10: Missing and invalid electricity rates
    # ---------------------------------------------------------
    def test_missing_and_invalid_electricity_rates(self):
        adjustments = [{"appliance_id": "a1", "proposed_hours_per_day": 4.5}]

        for bad_rate in [None, -8.0, 0.0, "bad_rate", False]:
            result = simulate_household_savings(
                self.baseline_appliances, adjustments, electricity_rate=bad_rate
            )
            summary = result["summary"]
            # kWh savings must calculate accurately
            self.assertAlmostEqual(summary["net_monthly_savings_kwh"], 67.5, places=4)

            # Cost outputs must be None / unavailable (never silently defaulting to 8)
            self.assertIsNone(summary["electricity_rate"])
            self.assertEqual(summary["rate_status"], "unavailable")
            self.assertIsNone(summary["baseline_monthly_cost"])
            self.assertIsNone(summary["simulated_monthly_cost"])
            self.assertIsNone(summary["net_monthly_cost_savings"])

    # ---------------------------------------------------------
    # Test 11: Baseline input immutability
    # ---------------------------------------------------------
    def test_baseline_immutability(self):
        original_copy = deepcopy(self.baseline_appliances)
        adjustments = [
            {"appliance_id": "a1", "proposed_hours_per_day": 4.5},
            {"appliance_id": "a3", "proposed_hours_per_day": 1.0},
        ]
        _ = simulate_household_savings(self.baseline_appliances, adjustments)

        # Assert baseline_appliances was not mutated
        self.assertEqual(self.baseline_appliances, original_copy)

    # ---------------------------------------------------------
    # Test 12: Interoperability with recommendation engine
    # ---------------------------------------------------------
    def test_interoperability_with_recommendation_engine(self):
        # 1. Run the recommendation engine
        rec_report = generate_household_recommendation_report(
            self.baseline_appliances, electricity_rate=self.standard_rate
        )
        self.assertTrue(len(rec_report["actionable_recommendations"]) >= 2)

        # 2. Feed recommendation report directly into simulator bridge
        sim_result = simulate_from_recommendations(
            self.baseline_appliances,
            rec_report,
            electricity_rate=self.standard_rate,
        )
        summary = sim_result["summary"]

        # Must replicate the exact combined scenario (97.5 kWh savings / ₹780)
        self.assertAlmostEqual(summary["baseline_monthly_kwh"], 513.0, places=4)
        self.assertAlmostEqual(summary["simulated_monthly_kwh"], 415.5, places=4)
        self.assertAlmostEqual(summary["net_monthly_savings_kwh"], 97.5, places=4)
        self.assertAlmostEqual(summary["net_monthly_cost_savings"], 780.0, places=2)

        # Test selecting a single recommendation by ID
        single_sim = simulate_from_recommendations(
            self.baseline_appliances,
            rec_report,
            selected_appliance_ids=["a1"],
            electricity_rate=self.standard_rate,
        )
        self.assertAlmostEqual(single_sim["summary"]["net_monthly_savings_kwh"], 67.5, places=4)

    # ---------------------------------------------------------
    # Test 13: Edge Cases (Missing IDs, Duplicates, Zero Consumption)
    # ---------------------------------------------------------
    def test_edge_cases(self):
        # Duplicate baseline IDs
        dup_baseline = [
            {"id": "same-id", "name": "Fan 1", "wattage": 50, "hoursPerDay": 2, "daysPerWeek": 7},
            {"id": "same-id", "name": "Fan 2", "wattage": 60, "hoursPerDay": 3, "daysPerWeek": 7},
        ]
        res = simulate_household_savings(dup_baseline, [{"appliance_id": "same-id", "proposed_hours_per_day": 1}])
        self.assertTrue(any("Duplicate baseline" in err["error"] for err in res["adjustment_errors"]))

        # Zero baseline consumption
        zero_baseline = [
            {"id": "z1", "name": "Off Device", "wattage": 100, "hoursPerDay": 0, "daysPerWeek": 7}
        ]
        zero_res = simulate_household_savings(zero_baseline, [{"appliance_id": "z1", "proposed_hours_per_day": 0}])
        self.assertEqual(zero_res["summary"]["baseline_monthly_kwh"], 0.0)
        self.assertEqual(zero_res["summary"]["percentage_reduction"], 0.0)
        self.assertEqual(zero_res["summary"]["consumption_impact"], "unchanged_consumption")

        # Non-numeric / NaN hours
        nan_adj = [{"appliance_id": "a1", "proposed_hours_per_day": float("nan")}]
        valid_adj, warnings, errors = validate_scenario_adjustments(self.baseline_appliances, nan_adj)
        self.assertEqual(len(valid_adj), 0)
        self.assertTrue(len(errors) >= 1)


if __name__ == "__main__":
    unittest.main()
