import pytest
from services.feasibility_checker import TripFeasibilityChecker
from models.trip import CostBreakdown


class TestFeasibilityChecker:
    def test_within_budget_evaluation(self):
        bk = CostBreakdown(
            transportation=5000,
            accommodation=6000,
            food=4000,
            activities_misc=2000,
            emergency_allowance=1700,
            subtotal=17000,
            total_cost=18700,
            cost_per_person=9350,
            required_rooms=1,
            remaining_budget=6300,
            shortage=0,
            feasibility_status="Within Budget"
        )
        eval_res = TripFeasibilityChecker.evaluate_feasibility(bk, available_budget=25000)
        assert eval_res["is_feasible"] is True
        assert eval_res["status"] == "Within Budget"
        assert eval_res["remaining_budget"] == 6300
        assert eval_res["shortage"] == 0

    def test_over_budget_evaluation(self):
        bk = CostBreakdown(
            transportation=5000,
            accommodation=6000,
            food=4000,
            activities_misc=2000,
            emergency_allowance=1700,
            subtotal=17000,
            total_cost=18700,
            cost_per_person=9350,
            required_rooms=1,
            remaining_budget=0,
            shortage=3700,
            feasibility_status="Over Budget"
        )
        eval_res = TripFeasibilityChecker.evaluate_feasibility(bk, available_budget=15000)
        assert eval_res["is_feasible"] is False
        assert eval_res["status"] == "Over Budget"
        assert eval_res["shortage"] == 3700
        assert "exceeds budget by PKR 3,700.00" in eval_res["message"]
