"""
GridPulse - Unit Tests for Personalised Appliance Energy Recommendation Engine
Member 3 Contribution: Energy Intelligence & Recommendation Module

Uses Python's built-in unittest framework (zero external packages required).
"""

import math
import unittest

from recommendation.appliance_recommender import (
    calculate_appliance_consumption,
    generate_household_recommendation_report,
    generate_usage_reduction_suggestion,
    identify_high_impact_appliances,
    is_continuous_appliance,
    rank_appliances_by_consumption,
    validate_appliance,
)


class TestApplianceRecommender(unittest.TestCase):
    def setUp(self):
        """Standard baseline household suite approved in the design."""
        self.standard_appliances = [
            {
                "id": "ac-01",
                "name": "Air Conditioner",
                "wattage": 1500,
                "quantity": 1,
                "hoursPerDay": 6.0,
                "daysPerWeek": 7,
            },
            {
                "id": "fridge-01",
                "name": "Refrigerator",
                "wattage": 200,
                "quantity": 1,
                "hoursPerDay": 24.0,
                "daysPerWeek": 7,
            },
            {
                "id": "heater-01",
                "name": "Water Heater",
                "wattage": 2000,
                "quantity": 1,
                "hoursPerDay": 1.5,
                "daysPerWeek": 7,
            },
            {
                "id": "led-01",
                "name": "LED Bulbs",
                "wattage": 10,
                "quantity": 5,
                "hoursPerDay": 6.0,
                "daysPerWeek": 7,
            },
        ]
        self.standard_rate = 8.0

    # ---------------------------------------------------------
    # Test 1: Refrigerator calculation (200W, 24h, 7d = 144 kWh)
    # ---------------------------------------------------------
    def test_refrigerator_calculation(self):
        fridge = {
            "name": "Refrigerator",
            "wattage": 200,
            "quantity": 1,
            "hoursPerDay": 24.0,
            "daysPerWeek": 7,
        }
        res = calculate_appliance_consumption(fridge)
        # Daily: (200 * 1 * 24 * 7) / 7000 = 4.8 kWh/day
        self.assertAlmostEqual(res["daily_kwh"], 4.8, places=4)
        # Monthly: 4.8 * 30 = 144.0 kWh/month (NOT 14.4)
        self.assertAlmostEqual(res["monthly_kwh"], 144.0, places=4)

    # ---------------------------------------------------------
    # Test 2: Correct total household consumption (513 kWh)
    # ---------------------------------------------------------
    def test_correct_total_household_consumption(self):
        report = generate_household_recommendation_report(
            self.standard_appliances, electricity_rate=self.standard_rate
        )
        total_kwh = report["summary"]["total_monthly_kwh"]
        # 270 (AC) + 144 (Fridge) + 90 (Geyser) + 9 (LEDs) = 513.0 kWh
        self.assertAlmostEqual(total_kwh, 513.0, places=4)
        self.assertEqual(report["summary"]["valid_appliances_count"], 4)

    # ---------------------------------------------------------
    # Test 3: Percentage contributions (sum to 100%)
    # ---------------------------------------------------------
    def test_percentage_contributions(self):
        report = generate_household_recommendation_report(
            self.standard_appliances, electricity_rate=self.standard_rate
        )
        ranked = report["ranked_appliances"]
        shares = {item["name"]: item["percentage_of_total"] for item in ranked}

        # Expected: AC: 52.63%, Fridge: 28.07%, Water Heater: 17.54%, LED Bulbs: 1.75%
        self.assertAlmostEqual(shares["Air Conditioner"], 52.63, places=1)
        self.assertAlmostEqual(shares["Refrigerator"], 28.07, places=1)
        self.assertAlmostEqual(shares["Water Heater"], 17.54, places=1)
        self.assertAlmostEqual(shares["LED Bulbs"], 1.75, places=1)

        total_percentage = sum(shares.values())
        self.assertTrue(math.isclose(total_percentage, 100.0, abs_tol=0.05))

    # ---------------------------------------------------------
    # Test 4: Ranking order and ties
    # ---------------------------------------------------------
    def test_ranking_order_and_ties(self):
        # Tied appliances: two different appliances with identical 60 kWh/month consumption
        tied_appliances = [
            {"name": "Appliance A", "wattage": 1000, "hoursPerDay": 2, "daysPerWeek": 7},  # 60 kWh
            {"name": "Appliance B", "wattage": 500, "hoursPerDay": 4, "daysPerWeek": 7},   # 60 kWh
            {"name": "Heavy AC", "wattage": 2000, "hoursPerDay": 4, "daysPerWeek": 7},    # 240 kWh
            {"name": "Small Light", "wattage": 20, "hoursPerDay": 5, "daysPerWeek": 7},   # 3 kWh
        ]
        report = generate_household_recommendation_report(tied_appliances)
        ranked = report["ranked_appliances"]

        # Heavy AC must be #1
        self.assertEqual(ranked[0]["name"], "Heavy AC")
        self.assertEqual(ranked[0]["rank"], 1)

        # Stable sort: Appliance A was submitted before Appliance B; input order must be preserved
        self.assertEqual(ranked[1]["name"], "Appliance A")
        self.assertEqual(ranked[2]["name"], "Appliance B")
        self.assertAlmostEqual(ranked[1]["monthly_kwh"], 60.0)
        self.assertAlmostEqual(ranked[2]["monthly_kwh"], 60.0)

        # Small Light is last
        self.assertEqual(ranked[3]["name"], "Small Light")
        self.assertEqual(ranked[3]["rank"], 4)

    # ---------------------------------------------------------
    # Test 5: Empty appliance list
    # ---------------------------------------------------------
    def test_empty_appliance_list(self):
        report = generate_household_recommendation_report([], electricity_rate=8.0)
        self.assertEqual(report["summary"]["total_appliances_submitted"], 0)
        self.assertEqual(report["summary"]["valid_appliances_count"], 0)
        self.assertEqual(report["summary"]["total_monthly_kwh"], 0.0)
        self.assertEqual(report["summary"]["total_monthly_cost"], 0.0)
        self.assertEqual(len(report["ranked_appliances"]), 0)
        self.assertEqual(len(report["actionable_recommendations"]), 0)
        self.assertEqual(len(report["invalid_appliances"]), 0)

    # ---------------------------------------------------------
    # Test 6: Invalid appliance records & validation messages
    # ---------------------------------------------------------
    def test_invalid_appliance_records(self):
        mixed_list = [
            {"name": "Valid Fan", "wattage": 75, "quantity": 2, "hoursPerDay": 8, "daysPerWeek": 7},
            {"name": "", "wattage": 100, "hoursPerDay": 2},  # invalid name
            {"name": "Bad Wattage", "wattage": -50, "hoursPerDay": 2},  # negative wattage
            {"name": "Bad Hours", "wattage": 100, "hoursPerDay": 25},  # > 24 hours
            {"name": "Bad Days", "wattage": 100, "hoursPerDay": 2, "daysPerWeek": 8},  # > 7 days
            {"name": "Bad Quantity", "wattage": 100, "quantity": 0, "hoursPerDay": 2},  # < 1 quantity
        ]
        report = generate_household_recommendation_report(mixed_list, electricity_rate=8.0)
        self.assertEqual(report["summary"]["valid_appliances_count"], 1)
        self.assertEqual(report["summary"]["invalid_appliances_count"], 5)
        self.assertEqual(len(report["invalid_appliances"]), 5)

        # Ensure validation reasons are specific and non-empty
        for inv in report["invalid_appliances"]:
            self.assertTrue(len(inv["validation_reasons"]) >= 1)

        # Confirm valid fan was processed without coercion of bad items
        self.assertEqual(report["ranked_appliances"][0]["name"], "Valid Fan")

    # ---------------------------------------------------------
    # Test 7: Missing and invalid electricity rates
    # ---------------------------------------------------------
    def test_missing_and_invalid_electricity_rates(self):
        for bad_rate in [None, -5.0, 0.0, "invalid_rate", False]:
            report = generate_household_recommendation_report(
                self.standard_appliances, electricity_rate=bad_rate
            )
            # Consumption must still compute accurately
            self.assertAlmostEqual(report["summary"]["total_monthly_kwh"], 513.0)
            self.assertAlmostEqual(report["summary"]["total_hypothetical_savings_kwh"], 97.5)

            # Cost and monetary savings must be None / unavailable (never silently defaulting to 8)
            self.assertIsNone(report["summary"]["electricity_rate"])
            self.assertEqual(report["summary"]["rate_status"], "unavailable")
            self.assertIsNone(report["summary"]["total_monthly_cost"])
            self.assertIsNone(report["summary"]["total_hypothetical_cost_savings"])

            # Check individual ranked items and recommendations
            for item in report["ranked_appliances"]:
                self.assertIsNone(item["monthly_cost"])
            for rec in report["actionable_recommendations"]:
                self.assertIsNone(rec["hypothetical_cost_savings"])

    # ---------------------------------------------------------
    # Test 8: Low-impact recommendation suppression (< 5%)
    # ---------------------------------------------------------
    def test_low_impact_suppression(self):
        report = generate_household_recommendation_report(
            self.standard_appliances, electricity_rate=self.standard_rate
        )
        # LED Bulbs is at 1.75% (< 5%)
        # 1. It MUST appear in ranked_appliances
        ranked_names = [a["name"] for a in report["ranked_appliances"]]
        self.assertIn("LED Bulbs", ranked_names)

        # 2. It must NOT appear in actionable_recommendations
        rec_names = [r["appliance_name"] for r in report["actionable_recommendations"]]
        self.assertNotIn("LED Bulbs", rec_names)

        # 3. It MUST be logged in suppressed_or_informational
        suppressed_names = [s["appliance_name"] for s in report["suppressed_or_informational"]]
        self.assertIn("LED Bulbs", suppressed_names)
        led_suppressed = next(s for s in report["suppressed_or_informational"] if s["appliance_name"] == "LED Bulbs")
        self.assertEqual(led_suppressed["status"], "Low Impact Suppressed")

    # ---------------------------------------------------------
    # Test 9: Continuous appliance safety (Refrigerator)
    # ---------------------------------------------------------
    def test_continuous_appliance_safety(self):
        report = generate_household_recommendation_report(
            self.standard_appliances, electricity_rate=self.standard_rate
        )
        # Refrigerator runs 24h/day
        # 1. It must NOT receive a runtime reduction recommendation
        actionable_names = [r["appliance_name"] for r in report["actionable_recommendations"]]
        self.assertNotIn("Refrigerator", actionable_names)

        # 2. It must be logged in suppressed_or_informational with safety reason
        fridge_suppressed = next(
            s for s in report["suppressed_or_informational"] if s["appliance_name"] == "Refrigerator"
        )
        self.assertEqual(fridge_suppressed["status"], "No Runtime Reduction")
        self.assertIn("food safety", fridge_suppressed["reason"].lower())

    # ---------------------------------------------------------
    # Test 10: Hypothetical AC and water heater savings
    # ---------------------------------------------------------
    def test_hypothetical_savings_calculations(self):
        report = generate_household_recommendation_report(
            self.standard_appliances, electricity_rate=self.standard_rate
        )
        recs = {r["appliance_name"]: r for r in report["actionable_recommendations"]}

        # 1. AC: 1500W reduced from 6.0h to 4.5h (-1.5h/day)
        # (1500 * 1 * 1.5 * 7) / 7000 * 30 = 67.5 kWh/month
        # 67.5 kWh * ₹8 = ₹540.00
        self.assertIn("Air Conditioner", recs)
        self.assertAlmostEqual(recs["Air Conditioner"]["hypothetical_savings_kwh"], 67.5, places=4)
        self.assertAlmostEqual(recs["Air Conditioner"]["hypothetical_cost_savings"], 540.0, places=2)

        # 2. Water Heater: 2000W reduced from 1.5h to 1.0h (-0.5h/day)
        # (2000 * 1 * 0.5 * 7) / 7000 * 30 = 30.0 kWh/month
        # 30.0 kWh * ₹8 = ₹240.00
        self.assertIn("Water Heater", recs)
        self.assertAlmostEqual(recs["Water Heater"]["hypothetical_savings_kwh"], 30.0, places=4)
        self.assertAlmostEqual(recs["Water Heater"]["hypothetical_cost_savings"], 240.0, places=2)

        # Total hypothetical savings: 67.5 + 30.0 = 97.5 kWh | ₹780.00
        self.assertAlmostEqual(report["summary"]["total_hypothetical_savings_kwh"], 97.5, places=4)
        self.assertAlmostEqual(report["summary"]["total_hypothetical_cost_savings"], 780.0, places=2)

    # ---------------------------------------------------------
    # Test 11: Recommendation output structure
    # ---------------------------------------------------------
    def test_recommendation_output_structure(self):
        report = generate_household_recommendation_report(
            self.standard_appliances, electricity_rate=self.standard_rate
        )
        # Required top-level keys
        for key in [
            "summary",
            "ranked_appliances",
            "high_impact_appliances",
            "actionable_recommendations",
            "suppressed_or_informational",
            "invalid_appliances",
        ]:
            self.assertIn(key, report)

        # Summary keys
        for key in [
            "total_monthly_kwh",
            "total_monthly_cost",
            "electricity_rate",
            "rate_status",
            "total_hypothetical_savings_kwh",
            "total_hypothetical_cost_savings",
            "potential_reduction_percent",
        ]:
            self.assertIn(key, report["summary"])


if __name__ == "__main__":
    unittest.main()
