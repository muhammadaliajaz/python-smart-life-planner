import math
from typing import Dict, Any, Optional
from models.destination import Destination
from models.trip import CostBreakdown, TripPlan
from utils.calculations import calculate_rooms_needed


class TripCostCalculator:
    """
    Performs deterministic financial calculations for Pakistan Trip Planner.
    Handles zero-night day trips, room capacities, emergency allowances,
    and category pricing adjustments.
    """

    DEFAULT_EMERGENCY_PERCENTAGE = 10.0  # 10% safety cushion

    @classmethod
    def calculate_cost(
        cls,
        destination: Destination,
        travellers: int,
        days: int,
        nights: int,
        available_budget: float,
        travel_category: str = "Standard",
        emergency_percentage: Optional[float] = None
    ) -> CostBreakdown:
        """
        Calculate complete itemized cost breakdown for a trip plan.
        
        Assumptions:
        - Transportation = cost_per_person * travellers
        - Required rooms = ceil(travellers / room_capacity)
        - Accommodation = room_cost * rooms * nights (0 if nights == 0)
        - Food = food_cost_per_person_day * travellers * days
        - Activities & Misc = activities_cost_per_person * travellers
        - Emergency allowance = subtotal * (emergency_percentage / 100)
        - Total = subtotal + emergency_allowance
        - Feasibility status based on budget comparison.
        """
        if travellers <= 0:
            raise ValueError(f"Travellers must be positive. Received: {travellers}")
        if days <= 0:
            raise ValueError(f"Days must be positive. Received: {days}")
        if nights < 0:
            raise ValueError(f"Nights cannot be negative. Received: {nights}")
        if nights > days:
            raise ValueError(f"Nights ({nights}) cannot exceed days ({days}).")
        if available_budget < 0:
            raise ValueError(f"Available budget cannot be negative. Received: {available_budget}")

        em_pct = cls.DEFAULT_EMERGENCY_PERCENTAGE if emergency_percentage is None else float(emergency_percentage)
        if em_pct < 0:
            em_pct = 0.0

        rates = destination.get_rates(travel_category)

        # 1. Transportation
        transport_cost = round(rates["transport_per_person"] * travellers, 2)

        # 2. Accommodation & Rooms
        required_rooms = calculate_rooms_needed(travellers, destination.room_capacity)
        if nights == 0:
            accommodation_cost = 0.0
        else:
            accommodation_cost = round(rates["accommodation_per_room_night"] * required_rooms * nights, 2)

        # 3. Food
        food_cost = round(rates["food_per_person_day"] * travellers * days, 2)

        # 4. Activities and Miscellaneous
        activities_cost = round(rates["activities_per_person"] * travellers, 2)

        # 5. Subtotal
        subtotal = round(transport_cost + accommodation_cost + food_cost + activities_cost, 2)

        # 6. Emergency Allowance
        emergency_allowance = round(subtotal * (em_pct / 100.0), 2)

        # 7. Total Cost & Per Person
        total_cost = round(subtotal + emergency_allowance, 2)
        cost_per_person = round(total_cost / travellers, 2)

        # 8. Budget Feasibility
        budget = round(float(available_budget), 2)
        diff = round(budget - total_cost, 2)

        if math.isclose(budget, total_cost, abs_tol=0.01):
            feasibility_status = "Exactly Within Budget"
            remaining_budget = 0.0
            shortage = 0.0
        elif budget > total_cost:
            feasibility_status = "Within Budget"
            remaining_budget = diff
            shortage = 0.0
        else:
            feasibility_status = "Over Budget"
            remaining_budget = 0.0
            shortage = round(total_cost - budget, 2)

        return CostBreakdown(
            transportation=transport_cost,
            accommodation=accommodation_cost,
            food=food_cost,
            activities_misc=activities_cost,
            emergency_allowance=emergency_allowance,
            subtotal=subtotal,
            total_cost=total_cost,
            cost_per_person=cost_per_person,
            required_rooms=required_rooms,
            remaining_budget=remaining_budget,
            shortage=shortage,
            feasibility_status=feasibility_status
        )
