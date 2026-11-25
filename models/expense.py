import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class Expense:
    """
    Represents an individual financial expense entry.
    Encapsulates id, category, amount, description, and date.
    """

    def __init__(
        self,
        category: str,
        amount: float,
        description: str,
        date_str: Optional[str] = None,
        expense_id: Optional[str] = None
    ):
        if not category or not str(category).strip():
            raise ValueError("Expense category cannot be empty.")
        if amount is None or float(amount) <= 0:
            raise ValueError(f"Expense amount must be positive. Received: {amount}")
        if not description or not str(description).strip():
            raise ValueError("Expense description cannot be empty.")

        self.category = str(category).strip()
        self.amount = round(float(amount), 2)
        self.description = str(description).strip()
        
        # Validate or default date
        if date_str:
            self.date = str(date_str).strip()
        else:
            self.date = datetime.now().strftime("%Y-%m-%d")

        self.id = str(expense_id).strip() if expense_id else f"EXP-{uuid.uuid4().hex[:8].upper()}"

    def update(self, category: Optional[str] = None, amount: Optional[float] = None,
               description: Optional[str] = None, date_str: Optional[str] = None) -> None:
        """Update expense fields with validation."""
        if category is not None:
            if not category.strip():
                raise ValueError("Expense category cannot be empty.")
            self.category = category.strip()
        if amount is not None:
            val = float(amount)
            if val <= 0:
                raise ValueError(f"Expense amount must be positive. Received: {amount}")
            self.amount = round(val, 2)
        if description is not None:
            if not description.strip():
                raise ValueError("Expense description cannot be empty.")
            self.description = description.strip()
        if date_str is not None:
            self.date = date_str.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert expense to dictionary representation."""
        return {
            "id": self.id,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
            "date": self.date
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Expense":
        """Instantiate Expense from dictionary."""
        return cls(
            category=data.get("category", "General"),
            amount=data.get("amount", 0.0),
            description=data.get("description", "Expense"),
            date_str=data.get("date"),
            expense_id=data.get("id")
        )

    def __repr__(self) -> str:
        return f"<Expense {self.id}: {self.category} PKR {self.amount:,.2f} on {self.date}>"
