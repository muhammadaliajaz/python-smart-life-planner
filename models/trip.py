import uuid
from collections import namedtuple
from typing import Dict, Any, List, Optional
from datetime import datetime

# Structured record for financial breakdown using collections.namedtuple
CostBreakdown = namedtuple(
    "CostBreakdown",
    [
        "transportation",
        "accommodation",
        "food",
        "activities_misc",
        "emergency_allowance",
        "subtotal",
        "total_cost",
        "cost_per_person",
        "required_rooms",
        "remaining_budget",
        "shortage",
        "feasibility_status"
    ]
)


class TripPlan:
    """
    Represents a Pakistan Trip Plan including constraints, preferences,
    cost calculations, day-wise itinerary, and confirmation status.
    Supports rollback of unconfirmed modifications.
    """

    def __init__(
        self,
        destination_name: str,
        departure_city: str,
        travellers: int,
        days: int,
        nights: int,
        available_budget: float,
        travel_category: str = "Standard",
        transport_preference: str = "Standard AC Bus/Car",
        accommodation_preference: str = "Standard Hotel Room",
        destination_type: str = "Any",
        emergency_percentage: float = 10.0,
        itinerary: Optional[List[Dict[str, Any]]] = None,
        plan_id: Optional[str] = None
    ):
        self.plan_id = plan_id or f"TRIP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.destination_name = str(destination_name).strip()
        self.departure_city = str(departure_city).strip()
        self.travellers = int(travellers)
        self.days = int(days)
        self.nights = int(nights)
        self.available_budget = round(float(available_budget), 2)
        self.travel_category = str(travel_category).strip().capitalize()
        self.transport_preference = str(transport_preference).strip()
        self.accommodation_preference = str(accommodation_preference).strip()
        self.destination_type = str(destination_type).strip()
        self.emergency_percentage = float(emergency_percentage)
        self.itinerary = itinerary or []
        
        # Computed breakdown
        self.breakdown: Optional[CostBreakdown] = None
        self.is_confirmed: bool = False
        self.confirmed_at: Optional[str] = None

        # Backup state snapshot for safe rollback of cancelled/unconfirmed edits
        self._snapshot: Optional[Dict[str, Any]] = None

    def create_snapshot(self) -> None:
        """Create a state snapshot before modifications."""
        self._snapshot = self.to_dict()

    def restore_snapshot(self) -> bool:
        """Restore previous state if modification was cancelled."""
        if not self._snapshot:
            return False
        self.destination_name = self._snapshot["destination_name"]
        self.departure_city = self._snapshot["departure_city"]
        self.travellers = self._snapshot["travellers"]
        self.days = self._snapshot["days"]
        self.nights = self._snapshot["nights"]
        self.available_budget = self._snapshot["available_budget"]
        self.travel_category = self._snapshot["travel_category"]
        self.transport_preference = self._snapshot["transport_preference"]
        self.accommodation_preference = self._snapshot["accommodation_preference"]
        self.destination_type = self._snapshot.get("destination_type", "Any")
        self.emergency_percentage = self._snapshot.get("emergency_percentage", 10.0)
        self.itinerary = self._snapshot.get("itinerary", [])
        self.is_confirmed = self._snapshot.get("is_confirmed", False)
        self.confirmed_at = self._snapshot.get("confirmed_at")
        self._snapshot = None
        return True

    def commit_changes(self) -> None:
        """Clear the snapshot upon user confirmation of changes."""
        self._snapshot = None

    def confirm_plan(self) -> None:
        """Mark plan as final and confirmed."""
        self.is_confirmed = True
        self.confirmed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """Convert TripPlan to dictionary for persistence."""
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "destination_name": self.destination_name,
            "departure_city": self.departure_city,
            "travellers": self.travellers,
            "days": self.days,
            "nights": self.nights,
            "available_budget": self.available_budget,
            "travel_category": self.travel_category,
            "transport_preference": self.transport_preference,
            "accommodation_preference": self.accommodation_preference,
            "destination_type": self.destination_type,
            "emergency_percentage": self.emergency_percentage,
            "is_confirmed": self.is_confirmed,
            "confirmed_at": self.confirmed_at,
            "breakdown": self.breakdown._asdict() if self.breakdown else None,
            "itinerary": self.itinerary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TripPlan":
        """Reconstruct TripPlan from dictionary."""
        plan = cls(
            destination_name=data.get("destination_name", "Murree"),
            departure_city=data.get("departure_city", "Islamabad"),
            travellers=data.get("travellers", 1),
            days=data.get("days", 1),
            nights=data.get("nights", 0),
            available_budget=data.get("available_budget", 0.0),
            travel_category=data.get("travel_category", "Standard"),
            transport_preference=data.get("transport_preference", "Standard AC Bus/Car"),
            accommodation_preference=data.get("accommodation_preference", "Standard Hotel Room"),
            destination_type=data.get("destination_type", "Any"),
            emergency_percentage=data.get("emergency_percentage", 10.0),
            itinerary=data.get("itinerary", []),
            plan_id=data.get("plan_id")
        )
        plan.created_at = data.get("created_at", plan.created_at)
        plan.is_confirmed = data.get("is_confirmed", False)
        plan.confirmed_at = data.get("confirmed_at")
        
        b = data.get("breakdown")
        if b and isinstance(b, dict):
            plan.breakdown = CostBreakdown(
                transportation=b.get("transportation", 0.0),
                accommodation=b.get("accommodation", 0.0),
                food=b.get("food", 0.0),
                activities_misc=b.get("activities_misc", 0.0),
                emergency_allowance=b.get("emergency_allowance", 0.0),
                subtotal=b.get("subtotal", 0.0),
                total_cost=b.get("total_cost", 0.0),
                cost_per_person=b.get("cost_per_person", 0.0),
                required_rooms=b.get("required_rooms", 1),
                remaining_budget=b.get("remaining_budget", 0.0),
                shortage=b.get("shortage", 0.0),
                feasibility_status=b.get("feasibility_status", "Unknown")
            )
        return plan

    def __repr__(self) -> str:
        return f"<TripPlan {self.plan_id}: {self.destination_name} ({self.days}D/{self.nights}N, {self.travellers}p)>"
