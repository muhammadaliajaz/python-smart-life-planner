from typing import Dict, Any, List, Optional
from collections import deque
from models.budget import Budget
from models.expense import Expense
from utils.data_manager import DataManager
from utils.validators import validate_positive_number, validate_non_empty_string


class MonthlyBudgetManager:
    """
    Orchestrates Module Two: Monthly Budget Manager.
    Supports budget creation, category management, expense tracking,
    overspending analysis, savings calculation, and persistence.
    """

    def __init__(self, data_manager: Optional[DataManager] = None):
        self.data_manager = data_manager or DataManager()
        self.active_budget: Optional[Budget] = None
        self.history = deque(maxlen=50)

    def create_budget(
        self,
        month: str,
        budget_type: str,
        total_available: float,
        planned_categories: Optional[Dict[str, float]] = None
    ) -> Budget:
        """
        Create a new monthly budget with selected type and categories.
        """
        ok_month, clean_month, err_month = validate_non_empty_string(month, "Budget Month")
        if not ok_month:
            raise ValueError(err_month)

        ok_avail, clean_avail, err_avail = validate_positive_number(total_available, "Monthly Available Amount")
        if not ok_avail:
            raise ValueError(err_avail)

        # Default planned categories if none provided
        categories: Dict[str, float] = {}
        if planned_categories:
            categories = {k: float(v) for k, v in planned_categories.items()}
        else:
            default_cats = Budget.get_default_categories_for_type(budget_type)
            for c in default_cats:
                categories[c] = 0.0

        budget = Budget(
            month=clean_month,
            budget_type=budget_type,
            total_available=clean_avail,
            planned_categories=categories
        )

        self.active_budget = budget
        self.history.append(f"Created {budget_type} budget for {clean_month}")
        return budget

    def load_budget_for_month(self, month: str) -> Optional[Budget]:
        """Load saved budget by month from data storage."""
        budgets_data = self.data_manager.load_budgets()
        clean_month = month.strip().lower()
        for b_dict in budgets_data:
            if b_dict.get("month", "").strip().lower() == clean_month:
                self.active_budget = Budget.from_dict(b_dict)
                self.history.append(f"Loaded budget for {self.active_budget.month}")
                return self.active_budget
        return None

    def save_current_budget(self) -> bool:
        """Persist active budget to storage."""
        if not self.active_budget:
            return False
        success = self.data_manager.upsert_budget(self.active_budget.to_dict())
        if success:
            self.history.append(f"Saved budget for {self.active_budget.month}")
        return success

    def add_category(self, category_name: str, planned_amount: float = 0.0) -> bool:
        """Add a new category to the active budget."""
        if not self.active_budget:
            raise ValueError("No active budget selected.")
        if planned_amount < 0:
            raise ValueError("Planned category amount cannot be negative.")
        return self.active_budget.add_category(category_name, planned_amount)

    def update_category(self, category_name: str, planned_amount: float) -> bool:
        """Update planned amount of an existing category."""
        if not self.active_budget:
            raise ValueError("No active budget selected.")
        if planned_amount < 0:
            raise ValueError("Planned category amount cannot be negative.")
        return self.active_budget.update_category(category_name, planned_amount)

    def remove_category(self, category_name: str) -> bool:
        """Remove a category from the active budget."""
        if not self.active_budget:
            raise ValueError("No active budget selected.")
        return self.active_budget.remove_category(category_name)

    def record_expense(
        self,
        category: str,
        amount: float,
        description: str,
        date_str: Optional[str] = None
    ) -> Expense:
        """Record a new actual expense."""
        if not self.active_budget:
            raise ValueError("No active budget selected.")
        
        ok_amt, clean_amt, err_amt = validate_positive_number(amount, "Expense Amount")
        if not ok_amt:
            raise ValueError(err_amt)
        
        expense = Expense(
            category=category,
            amount=clean_amt,
            description=description,
            date_str=date_str
        )
        self.active_budget.add_expense(expense)
        return expense

    def update_expense(
        self,
        expense_id: str,
        category: Optional[str] = None,
        amount: Optional[float] = None,
        description: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> bool:
        """Update an existing expense."""
        if not self.active_budget:
            raise ValueError("No active budget selected.")
        return self.active_budget.update_expense(
            expense_id=expense_id,
            category=category,
            amount=amount,
            description=description,
            date_str=date_str
        )

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense by ID."""
        if not self.active_budget:
            raise ValueError("No active budget selected.")
        return self.active_budget.delete_expense(expense_id)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get complete financial analytics for active budget:
        planned, actual, balance, savings, overspending, category breakdown.
        """
        if not self.active_budget:
            raise ValueError("No active budget selected.")

        b = self.active_budget
        total_planned = b.get_total_planned()
        total_actual = b.get_total_actual()
        remaining = b.get_remaining_balance()
        savings = b.get_savings()
        savings_pct = b.get_savings_percentage()
        unallocated = b.get_unallocated_amount()
        overspent_cats = b.get_overspending_categories()
        is_overspent = b.is_overall_overspent()

        return {
            "month": b.month,
            "budget_type": b.budget_type,
            "total_available": b.total_available,
            "total_planned": total_planned,
            "total_actual": total_actual,
            "remaining_balance": remaining,
            "savings": savings,
            "savings_percentage": savings_pct,
            "unallocated_amount": unallocated,
            "is_overall_overspent": is_overspent,
            "overspending_categories": overspent_cats,
            "category_breakdown": b.get_category_breakdown(),
            "expense_count": len(b.expenses)
        }
