from collections import namedtuple
from typing import List, Dict, Any, Optional
from models.destination import Destination
from models.trip import TripPlan, CostBreakdown
from services.trip_calculator import TripCostCalculator
from utils.calculations import format_pkr

OptimizationOption = namedtuple(
    "OptimizationOption",
    [
        "strategy",
        "description",
        "destination_name",
        "travellers",
        "days",
        "nights",
        "travel_category",
        "total_cost",
        "remaining_budget",
        "score"
    ]
)


class TripOptimizer:
    """
    Intelligent optimization service for over-budget trip plans.
    Calculates realistic, fully recalculated alternatives across 5 dimensions:
      1. Increase budget (minimum required amount)
      2. Reduce travellers (maximum people who can travel)
      3. Reduce duration (feasible days & nights)
      4. Change destination (alternative destinations matching preferences)
      5. Adjust preferences (Budget category and lower tiers)
      6. Compare and rank feasible plans based on multi-factor scoring.

    IMPORTANT: Never suggests hardcoded or unaffordable recommendations.
    Every alternative is verified via TripCostCalculator to be <= available_budget.
    """

    def __init__(self, destinations: List[Destination]):
        self.destinations = {d.name.lower(): d for d in destinations}
        self.destinations_list = destinations

    def get_destination(self, name: str) -> Optional[Destination]:
        return self.destinations.get(str(name).strip().lower())

    def generate_alternatives(
        self,
        current_plan: TripPlan,
        all_destinations: Optional[List[Destination]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive, fully calculated optimization alternatives.
        """
        dest_pool = all_destinations or self.destinations_list
        dest = self.get_destination(current_plan.destination_name)
        if not dest:
            return {"error": f"Destination '{current_plan.destination_name}' not found."}

        budget = current_plan.available_budget
        original_travellers = current_plan.travellers
        original_days = current_plan.days
        original_nights = current_plan.nights
        original_category = current_plan.travel_category
        em_pct = current_plan.emergency_percentage

        # Current breakdown
        current_breakdown = TripCostCalculator.calculate_cost(
            destination=dest,
            travellers=original_travellers,
            days=original_days,
            nights=original_nights,
            available_budget=budget,
            travel_category=original_category,
            emergency_percentage=em_pct
        )

        results: Dict[str, Any] = {
            "current_plan": {
                "destination": dest.name,
                "travellers": original_travellers,
                "days": original_days,
                "nights": original_nights,
                "category": original_category,
                "total_cost": current_breakdown.total_cost,
                "budget": budget,
                "shortage": current_breakdown.shortage,
                "feasibility": current_breakdown.feasibility_status
            },
            "strategies": {},
            "ranked_alternatives": []
        }

        # 1. Strategy: Increase Budget
        results["strategies"]["increase_budget"] = {
            "minimum_required_budget": current_breakdown.total_cost,
            "additional_budget_needed": current_breakdown.shortage,
            "description": f"Increase budget by {format_pkr(current_breakdown.shortage)} to cover the current itinerary without changing any preferences."
        }

        feasible_options: List[OptimizationOption] = []

        # 2. Strategy: Reduce Travellers
        max_feasible_travellers = None
        best_traveller_breakdown = None
        for t in range(original_travellers - 1, 0, -1):
            bk = TripCostCalculator.calculate_cost(
                destination=dest,
                travellers=t,
                days=original_days,
                nights=original_nights,
                available_budget=budget,
                travel_category=original_category,
                emergency_percentage=em_pct
            )
            if bk.total_cost <= budget:
                max_feasible_travellers = t
                best_traveller_breakdown = bk
                break  # highest feasible travellers

        if max_feasible_travellers is not None and best_traveller_breakdown is not None:
            results["strategies"]["reduce_travellers"] = {
                "feasible": True,
                "max_travellers": max_feasible_travellers,
                "cost": best_traveller_breakdown.total_cost,
                "remaining_budget": best_traveller_breakdown.remaining_budget,
                "description": f"Reduce group size from {original_travellers} to {max_feasible_travellers} traveller(s). Total: {format_pkr(best_traveller_breakdown.total_cost)} (Savings: {format_pkr(best_traveller_breakdown.remaining_budget)})."
            }
            feasible_options.append(OptimizationOption(
                strategy="Reduce Travellers",
                description=f"Travel with {max_feasible_travellers} person(s)",
                destination_name=dest.name,
                travellers=max_feasible_travellers,
                days=original_days,
                nights=original_nights,
                travel_category=original_category,
                total_cost=best_traveller_breakdown.total_cost,
                remaining_budget=best_traveller_breakdown.remaining_budget,
                score=self._calculate_score(
                    preserved_travellers=max_feasible_travellers / original_travellers,
                    preserved_days=1.0,
                    category_match=1.0,
                    dest_match=1.0,
                    budget_utilization=best_traveller_breakdown.total_cost / budget if budget > 0 else 0
                )
            ))
        else:
            results["strategies"]["reduce_travellers"] = {
                "feasible": False,
                "description": "Budget is insufficient even for 1 single traveller at this destination and duration."
            }

        # 3. Strategy: Reduce Duration
        best_duration = None
        # Try reducing days and nights systematically
        found_duration = False
        for d in range(original_days - 1, 0, -1):
            # Try corresponding nights from d down to 0
            max_n = min(original_nights, d)
            for n in range(max_n, -1, -1):
                bk = TripCostCalculator.calculate_cost(
                    destination=dest,
                    travellers=original_travellers,
                    days=d,
                    nights=n,
                    available_budget=budget,
                    travel_category=original_category,
                    emergency_percentage=em_pct
                )
                if bk.total_cost <= budget:
                    best_duration = (d, n, bk)
                    found_duration = True
                    break
            if found_duration:
                break

        if best_duration:
            d_feas, n_feas, bk_dur = best_duration
            results["strategies"]["reduce_duration"] = {
                "feasible": True,
                "days": d_feas,
                "nights": n_feas,
                "cost": bk_dur.total_cost,
                "remaining_budget": bk_dur.remaining_budget,
                "description": f"Shorten trip from {original_days}D/{original_nights}N to {d_feas}D/{n_feas}N. Total: {format_pkr(bk_dur.total_cost)} (Savings: {format_pkr(bk_dur.remaining_budget)})."
            }
            feasible_options.append(OptimizationOption(
                strategy="Reduce Duration",
                description=f"Trip duration adjusted to {d_feas} Days / {n_feas} Nights",
                destination_name=dest.name,
                travellers=original_travellers,
                days=d_feas,
                nights=n_feas,
                travel_category=original_category,
                total_cost=bk_dur.total_cost,
                remaining_budget=bk_dur.remaining_budget,
                score=self._calculate_score(
                    preserved_travellers=1.0,
                    preserved_days=d_feas / original_days,
                    category_match=1.0,
                    dest_match=1.0,
                    budget_utilization=bk_dur.total_cost / budget if budget > 0 else 0
                )
            ))
        else:
            results["strategies"]["reduce_duration"] = {
                "feasible": False,
                "description": "Shortening duration alone does not make the trip affordable within current budget."
            }

        # 4. Strategy: Adjust Preferences (Category downgrade to Budget / Standard)
        category_options = ["Budget"]
        if original_category == "Premium":
            category_options.append("Standard")

        cat_feasible = []
        for cat in category_options:
            if cat != original_category:
                bk_cat = TripCostCalculator.calculate_cost(
                    destination=dest,
                    travellers=original_travellers,
                    days=original_days,
                    nights=original_nights,
                    available_budget=budget,
                    travel_category=cat,
                    emergency_percentage=em_pct
                )
                if bk_cat.total_cost <= budget:
                    cat_feasible.append((cat, bk_cat))
                    feasible_options.append(OptimizationOption(
                        strategy="Adjust Travel Category",
                        description=f"Switch to '{cat}' category with economy transportation and accommodation",
                        destination_name=dest.name,
                        travellers=original_travellers,
                        days=original_days,
                        nights=original_nights,
                        travel_category=cat,
                        total_cost=bk_cat.total_cost,
                        remaining_budget=bk_cat.remaining_budget,
                        score=self._calculate_score(
                            preserved_travellers=1.0,
                            preserved_days=1.0,
                            category_match=0.8 if cat == "Standard" else 0.6,
                            dest_match=1.0,
                            budget_utilization=bk_cat.total_cost / budget if budget > 0 else 0
                        )
                    ))

        if cat_feasible:
            # Pick best (highest category first)
            best_cat, bk_c = cat_feasible[-1]
            results["strategies"]["adjust_category"] = {
                "feasible": True,
                "category": best_cat,
                "cost": bk_c.total_cost,
                "remaining_budget": bk_c.remaining_budget,
                "description": f"Switch travel tier to '{best_cat}'. Total: {format_pkr(bk_c.total_cost)} (Savings: {format_pkr(bk_c.remaining_budget)})."
            }
        else:
            results["strategies"]["adjust_category"] = {
                "feasible": False,
                "description": "Adjusting travel category alone is insufficient for current budget."
            }

        # 5. Strategy: Change Destination (Compare all other destinations)
        alt_destinations = []
        preferred_type = current_plan.destination_type
        for other_d in dest_pool:
            if other_d.name.lower() == dest.name.lower():
                continue

            # Check with original category first, then Budget category
            for cat in [original_category, "Budget"]:
                bk_other = TripCostCalculator.calculate_cost(
                    destination=other_d,
                    travellers=original_travellers,
                    days=original_days,
                    nights=original_nights,
                    available_budget=budget,
                    travel_category=cat,
                    emergency_percentage=em_pct
                )
                if bk_other.total_cost <= budget:
                    type_bonus = 1.0 if (preferred_type in ("Any", other_d.category)) else 0.7
                    alt_destinations.append({
                        "destination": other_d.name,
                        "category": cat,
                        "type": other_d.category,
                        "cost": bk_other.total_cost,
                        "remaining_budget": bk_other.remaining_budget
                    })
                    feasible_options.append(OptimizationOption(
                        strategy="Change Destination",
                        description=f"Visit {other_d.name} ({other_d.category}) under {cat} category",
                        destination_name=other_d.name,
                        travellers=original_travellers,
                        days=original_days,
                        nights=original_nights,
                        travel_category=cat,
                        total_cost=bk_other.total_cost,
                        remaining_budget=bk_other.remaining_budget,
                        score=self._calculate_score(
                            preserved_travellers=1.0,
                            preserved_days=1.0,
                            category_match=0.9 if cat == original_category else 0.6,
                            dest_match=type_bonus,
                            budget_utilization=bk_other.total_cost / budget if budget > 0 else 0
                        )
                    ))
                    break  # Found best category for this destination

        results["strategies"]["change_destination"] = {
            "feasible": len(alt_destinations) > 0,
            "count": len(alt_destinations),
            "destinations": alt_destinations[:5]
        }

        # 6. Rank all feasible options by multi-factor score
        feasible_options.sort(key=lambda opt: opt.score, reverse=True)
        results["ranked_alternatives"] = [opt._asdict() for opt in feasible_options]

        return results

    @staticmethod
    def _calculate_score(
        preserved_travellers: float,
        preserved_days: float,
        category_match: float,
        dest_match: float,
        budget_utilization: float
    ) -> float:
        """
        Multi-factor ranking score:
        - preserved_travellers (weight 30%)
        - preserved_days (weight 25%)
        - dest_match (weight 20%)
        - category_match (weight 15%)
        - budget_utilization (weight 10% - close to budget without exceeding)
        """
        return round(
            (preserved_travellers * 30.0) +
            (preserved_days * 25.0) +
            (dest_match * 20.0) +
            (category_match * 15.0) +
            (min(1.0, budget_utilization) * 10.0),
            2
        )
