from typing import Dict, Any, List, Optional


class Destination:
    """
    Encapsulates destination data, regional category, and pricing parameters.
    Supports calculating category-specific pricing (Budget, Standard, Premium).
    """

    def __init__(
        self,
        name: str,
        region: str,
        category: str,
        room_capacity: int = 2,
        base_transport_cost_per_person: float = 3000.0,
        base_accommodation_cost_per_room_night: float = 4500.0,
        food_cost_per_person_day: float = 2000.0,
        activities_misc_cost_per_person: float = 2500.0,
        category_rates: Optional[Dict[str, Dict[str, float]]] = None,
        highlights: Optional[List[str]] = None
    ):
        self.name = str(name).strip()
        self.region = str(region).strip()
        self.category = str(category).strip()  # Mountains, Lakes & Nature, Historical Places
        self.room_capacity = max(1, int(room_capacity))
        self.base_transport_cost_per_person = float(base_transport_cost_per_person)
        self.base_accommodation_cost_per_room_night = float(base_accommodation_cost_per_room_night)
        self.food_cost_per_person_day = float(food_cost_per_person_day)
        self.activities_misc_cost_per_person = float(activities_misc_cost_per_person)
        self.category_rates = category_rates or {}
        self.highlights = highlights or []

    def get_rates(self, travel_category: str = "Standard") -> Dict[str, float]:
        """
        Return rates customized for travel category (Budget, Standard, Premium).
        Returns a dict with:
          - transport_per_person
          - accommodation_per_room_night
          - food_per_person_day
          - activities_per_person
        """
        cat_key = travel_category.strip().capitalize()
        rates = self.category_rates.get(cat_key, {})

        # Compute category-scaled values
        transport_mult = rates.get("transport_multiplier", 1.0 if cat_key == "Budget" else (1.4 if cat_key == "Standard" else 2.2))
        food_mult = rates.get("food_multiplier", 1.0 if cat_key == "Budget" else (1.3 if cat_key == "Standard" else 2.0))
        act_mult = rates.get("activities_multiplier", 0.8 if cat_key == "Budget" else (1.2 if cat_key == "Standard" else 2.0))

        # Room cost can be explicitly set in rates or scaled
        room_cost = rates.get("accommodation_per_room_night")
        if room_cost is None:
            mult = 0.8 if cat_key == "Budget" else (1.3 if cat_key == "Standard" else 2.2)
            room_cost = self.base_accommodation_cost_per_room_night * mult

        return {
            "transport_per_person": round(self.base_transport_cost_per_person * transport_mult, 2),
            "accommodation_per_room_night": round(float(room_cost), 2),
            "food_per_person_day": round(self.food_cost_per_person_day * food_mult, 2),
            "activities_per_person": round(self.activities_misc_cost_per_person * act_mult, 2)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert Destination object to dictionary."""
        return {
            "name": self.name,
            "region": self.region,
            "category": self.category,
            "room_capacity": self.room_capacity,
            "base_transport_cost_per_person": self.base_transport_cost_per_person,
            "base_accommodation_cost_per_room_night": self.base_accommodation_cost_per_room_night,
            "food_cost_per_person_day": self.food_cost_per_person_day,
            "activities_misc_cost_per_person": self.activities_misc_cost_per_person,
            "category_rates": self.category_rates,
            "highlights": self.highlights
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Destination":
        """Instantiate Destination from dictionary."""
        return cls(
            name=data.get("name", "Unknown"),
            region=data.get("region", "Pakistan"),
            category=data.get("category", "General"),
            room_capacity=data.get("room_capacity", 2),
            base_transport_cost_per_person=data.get("base_transport_cost_per_person", 3000.0),
            base_accommodation_cost_per_room_night=data.get("base_accommodation_cost_per_room_night", 4000.0),
            food_cost_per_person_day=data.get("food_cost_per_person_day", 2000.0),
            activities_misc_cost_per_person=data.get("activities_misc_cost_per_person", 2000.0),
            category_rates=data.get("category_rates", {}),
            highlights=data.get("highlights", [])
        )

    def __repr__(self) -> str:
        return f"<Destination {self.name} ({self.category}, {self.region})>"
