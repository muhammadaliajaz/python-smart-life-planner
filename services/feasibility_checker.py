from typing import Dict, Any, Tuple
from models.trip import CostBreakdown, TripPlan
from utils.calculations import format_pkr


class TripFeasibilityChecker:
    """
    Evaluates whether a trip plan fits within the available budget.
    Provides diagnostic messages and shortage breakdowns.
    """

    @staticmethod
    def evaluate_feasibility(breakdown: CostBreakdown, available_budget: float) -> Dict[str, Any]:
        """
        Evaluate feasibility and provide diagnostic analysis.
        """
        status = breakdown.feasibility_status
        total_cost = breakdown.total_cost
        shortage = breakdown.shortage
        remaining = breakdown.remaining_budget

        if status == "Within Budget":
            message = (
                f"Trip is feasible! Total estimated cost ({format_pkr(total_cost)}) "
                f"is comfortably within your budget of {format_pkr(available_budget)}. "
                f"Remaining surplus: {format_pkr(remaining)}."
            )
            is_feasible = True
        elif status == "Exactly Within Budget":
            message = (
                f"Trip is exactly on budget! Estimated cost matches available budget of "
                f"{format_pkr(available_budget)} exactly."
            )
            is_feasible = True
        else:
            shortage_pct = round((shortage / total_cost) * 100, 1) if total_cost > 0 else 0.0
            message = (
                f"Trip exceeds budget by {format_pkr(shortage)} ({shortage_pct}% over). "
                f"Estimated cost: {format_pkr(total_cost)}, Available budget: {format_pkr(available_budget)}."
            )
            is_feasible = False

        return {
            "status": status,
            "is_feasible": is_feasible,
            "available_budget": available_budget,
            "total_cost": total_cost,
            "shortage": shortage,
            "remaining_budget": remaining,
            "cost_per_person": breakdown.cost_per_person,
            "message": message
        }
