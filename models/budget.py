from collections import Counter, deque
from typing import Dict, Any, List, Optional
from datetime import datetime

from .expense import Expense
from utils.calculations import calculate_percentage


class Budget:
    """
    Encapsulates a monthly budget, planned category allocations,
    recorded actual expenses, and overspending analytics.
    Utilizes collections.Counter for category totals and collections.deque for action history.
    """

    HOME_AND_KITCHEN_CATEGORIES = [
        "Grocery",
        "Electricity",
        "Gas",
        "Water",
        "Internet",
        "Rent",
        "Kitchen Supplies",
        "Medical Expenses",
        "Transportation",
        "Emergency Savings",
        "Other Expenses"
    ]

    PERSONAL_FINANCE_CATEGORIES = [
        "Cosmetics and Personal Care",
        "Fitness and Gym",
        "Health and Medical",
        "Shopping",
        "Clothing",
        "Food and Restaurants",
        "Transportation",
        "Education",
        "Entertainment",
        "Investments and Savings",
        "Other Expenses"
    ]

    def __init__(
        self,
        month: str,
        budget_type: str,
        total_available: float,
        planned_categories: Optional[Dict[str, float]] = None,
        expenses: Optional[List[Expense]] = None
    ):
        if not month or not str(month).strip():
            raise ValueError("Budget month cannot be empty.")
        if total_available is None or float(total_available) <= 0:
            raise ValueError(f"Total monthly available amount must be positive. Received: {total_available}")

        self.month = str(month).strip()
        self.budget_type = str(budget_type).strip()  # "Home & Kitchen" or "Personal Finance" or "Custom"
        self.total_available = round(float(total_available), 2)
        
        # Planned category allocations (category_name -> planned_amount)
        self.planned_categories: Dict[str, float] = {}
        if planned_categories:
            for cat, amt in planned_categories.items():
                self.planned_categories[str(cat).strip()] = round(max(0.0, float(amt)), 2)

        # Actual recorded expenses
        self.expenses: List[Expense] = expenses or []

        # Audit trail of modifications using collections.deque
        self.recent_actions = deque(maxlen=40)
        self.recent_actions.append(f"Budget initialized for {self.month} with PKR {self.total_available:,.2f}")

    @classmethod
    def get_default_categories_for_type(cls, budget_type: str) -> List[str]:
        """Return standardized category lists for given budget type."""
        bt = budget_type.lower()
        if "home" in bt or "kitchen" in bt:
            return list(cls.HOME_AND_KITCHEN_CATEGORIES)
        elif "personal" in bt:
            return list(cls.PERSONAL_FINANCE_CATEGORIES)
        return ["General Expense", "Savings", "Utilities", "Other Expenses"]

    def add_category(self, category_name: str, planned_amount: float = 0.0) -> bool:
        """Add a category. Fails if category already exists."""
        clean_name = str(category_name).strip()
        if not clean_name:
            raise ValueError("Category name cannot be empty.")
        if any(c.lower() == clean_name.lower() for c in self.planned_categories):
            return False  # Duplicate category
        
        amt = round(max(0.0, float(planned_amount)), 2)
        self.planned_categories[clean_name] = amt
        self.recent_actions.append(f"Added category '{clean_name}' (Planned: PKR {amt:,.2f})")
        return True

    def update_category(self, category_name: str, planned_amount: float) -> bool:
        """Update planned amount for an existing category."""
        clean_name = str(category_name).strip()
        for cat in list(self.planned_categories.keys()):
            if cat.lower() == clean_name.lower():
                amt = round(max(0.0, float(planned_amount)), 2)
                self.planned_categories[cat] = amt
                self.recent_actions.append(f"Updated category '{cat}' planned amount to PKR {amt:,.2f}")
                return True
        return False

    def remove_category(self, category_name: str) -> bool:
        """Remove a category from planned allocations."""
        clean_name = str(category_name).strip()
        for cat in list(self.planned_categories.keys()):
            if cat.lower() == clean_name.lower():
                del self.planned_categories[cat]
                self.recent_actions.append(f"Removed category '{cat}'")
                return True
        return False

    def add_expense(self, expense: Expense) -> None:
        """Record a new actual expense."""
        # Ensure category is registered in planned_categories if not present
        if not any(c.lower() == expense.category.lower() for c in self.planned_categories):
            self.planned_categories[expense.category] = 0.0
        
        self.expenses.append(expense)
        self.recent_actions.append(
            f"Recorded expense {expense.id}: {expense.category} PKR {expense.amount:,.2f}"
        )

    def find_expense(self, expense_id: str) -> Optional[Expense]:
        """Find an expense by ID."""
        for exp in self.expenses:
            if exp.id.lower() == str(expense_id).strip().lower():
                return exp
        return None

    def update_expense(
        self,
        expense_id: str,
        category: Optional[str] = None,
        amount: Optional[float] = None,
        description: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> bool:
        """Update an existing expense by ID."""
        exp = self.find_expense(expense_id)
        if not exp:
            return False
        exp.update(category=category, amount=amount, description=description, date_str=date_str)
        if category and not any(c.lower() == category.lower() for c in self.planned_categories):
            self.planned_categories[category] = 0.0
        self.recent_actions.append(f"Updated expense {exp.id}")
        return True

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense by ID."""
        exp = self.find_expense(expense_id)
        if not exp:
            return False
        self.expenses.remove(exp)
        self.recent_actions.append(f"Deleted expense {expense_id}")
        return True

    def get_category_actual_totals(self) -> Counter:
        """
        Aggregate total actual spending per category using collections.Counter.
        """
        counter = Counter()
        for exp in self.expenses:
            # Match registered category case
            matched_cat = exp.category
            for cat in self.planned_categories:
                if cat.lower() == exp.category.lower():
                    matched_cat = cat
                    break
            counter[matched_cat] += exp.amount
        return counter

    def get_total_planned(self) -> float:
        """Sum of all planned category amounts."""
        return round(sum(self.planned_categories.values()), 2)

    def get_total_actual(self) -> float:
        """Sum of all recorded actual expenses."""
        return round(sum(exp.amount for exp in self.expenses), 2)

    def get_remaining_balance(self) -> float:
        """Remaining monthly available funds: Total Available - Actual Spent."""
        return round(self.total_available - self.get_total_actual(), 2)

    def get_savings(self) -> float:
        """
        Actual savings achieved: Total Available - Total Actual Expenses.
        Cannot be negative (if negative, savings is 0 and remaining is deficit).
        """
        balance = self.get_remaining_balance()
        return max(0.0, balance)

    def get_savings_percentage(self) -> float:
        """Savings percentage relative to total available amount."""
        savings = self.get_savings()
        return calculate_percentage(savings, self.total_available)

    def get_unallocated_amount(self) -> float:
        """Unallocated funds: Total Available - Total Planned."""
        return round(self.total_available - self.get_total_planned(), 2)

    def get_category_breakdown(self) -> List[Dict[str, Any]]:
        """
        Generate detailed category breakdown comparing planned, actual, difference,
        and overspending status.
        """
        actual_totals = self.get_category_actual_totals()
        all_categories = sorted(list(set(list(self.planned_categories.keys()) + list(actual_totals.keys()))))
        
        breakdown = []
        for cat in all_categories:
            planned = self.planned_categories.get(cat, 0.0)
            actual = round(actual_totals.get(cat, 0.0), 2)
            diff = round(planned - actual, 2)
            is_overspent = actual > planned
            overspent_amount = round(actual - planned, 2) if is_overspent else 0.0

            breakdown.append({
                "category": cat,
                "planned": planned,
                "actual": actual,
                "difference": diff,  # positive means under-budget, negative means overspent
                "is_overspent": is_overspent,
                "overspent_amount": overspent_amount
            })
        return breakdown

    def get_overspending_categories(self) -> List[Dict[str, Any]]:
        """Return list of categories that have exceeded planned budget."""
        return [item for item in self.get_category_breakdown() if item["is_overspent"]]

    def is_overall_overspent(self) -> bool:
        """Check if total actual spending exceeds total monthly available amount."""
        return self.get_total_actual() > self.total_available

    def to_dict(self) -> Dict[str, Any]:
        """Convert Budget to dictionary for JSON persistence."""
        return {
            "month": self.month,
            "budget_type": self.budget_type,
            "total_available": self.total_available,
            "planned_categories": self.planned_categories,
            "expenses": [e.to_dict() for e in self.expenses],
            "recent_actions": list(self.recent_actions)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Budget":
        """Instantiate Budget from dictionary."""
        expenses = [Expense.from_dict(e) for e in data.get("expenses", [])]
        budget = cls(
            month=data.get("month", datetime.now().strftime("%B %Y")),
            budget_type=data.get("budget_type", "Home & Kitchen"),
            total_available=data.get("total_available", 50000.0),
            planned_categories=data.get("planned_categories", {}),
            expenses=expenses
        )
        for act in data.get("recent_actions", []):
            budget.recent_actions.append(act)
        return budget

    def __repr__(self) -> str:
        return f"<Budget {self.month} ({self.budget_type}): PKR {self.get_total_actual():,.2f} spent of PKR {self.total_available:,.2f}>"
