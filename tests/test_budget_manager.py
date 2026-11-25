import pytest
from services.budget_manager import MonthlyBudgetManager
from utils.data_manager import DataManager
from models.budget import Budget
from models.expense import Expense


@pytest.fixture
def budget_mgr(tmp_path):
    dm = DataManager(base_dir=str(tmp_path))
    return MonthlyBudgetManager(data_manager=dm)


class TestBudgetManager:
    def test_create_budget_valid(self, budget_mgr):
        b = budget_mgr.create_budget("November 2026", "Home & Kitchen", 100000.0)
        assert b.month == "November 2026"
        assert b.total_available == 100000.0
        assert "Grocery" in b.planned_categories
        assert "Electricity" in b.planned_categories

    def test_create_budget_invalid(self, budget_mgr):
        with pytest.raises(ValueError):
            budget_mgr.create_budget("", "Home & Kitchen", 50000.0)
        with pytest.raises(ValueError):
            budget_mgr.create_budget("November 2026", "Home & Kitchen", -500.0)

    def test_category_management(self, budget_mgr):
        budget_mgr.create_budget("November 2026", "Personal Finance", 80000.0)
        
        # Add category
        assert budget_mgr.add_category("Gym Supplements", 5000.0) is True
        # Duplicate category returns False
        assert budget_mgr.add_category("Gym Supplements", 6000.0) is False

        # Update category
        assert budget_mgr.update_category("Gym Supplements", 7500.0) is True
        assert budget_mgr.active_budget.planned_categories["Gym Supplements"] == 7500.0

        # Remove category
        assert budget_mgr.remove_category("Gym Supplements") is True
        assert "Gym Supplements" not in budget_mgr.active_budget.planned_categories

    def test_record_update_delete_expense(self, budget_mgr):
        budget_mgr.create_budget("November 2026", "Home & Kitchen", 90000.0)
        budget_mgr.update_category("Grocery", 20000.0)

        # Record expense
        exp = budget_mgr.record_expense(
            category="Grocery",
            amount=6500.0,
            description="Supermarket monthly staples",
            date_str="2026-11-05"
        )
        assert exp.id is not None
        assert exp.amount == 6500.0
        assert len(budget_mgr.active_budget.expenses) == 1

        # Update expense
        assert budget_mgr.update_expense(exp.id, amount=7000.0, description="Updated staples") is True
        assert exp.amount == 7000.0
        assert exp.description == "Updated staples"

        # Delete expense
        assert budget_mgr.delete_expense(exp.id) is True
        assert len(budget_mgr.active_budget.expenses) == 0

        # Updating nonexistent returns False
        assert budget_mgr.update_expense("NON-EXISTENT", amount=100) is False
        assert budget_mgr.delete_expense("NON-EXISTENT") is False

    def test_budget_calculations_and_overspending(self, budget_mgr):
        b = budget_mgr.create_budget("November 2026", "Custom", 50000.0, planned_categories={
            "Food": 15000.0,
            "Rent": 20000.0,
            "Internet": 3000.0
        })

        budget_mgr.record_expense("Food", 12000.0, "Dining & groceries")
        budget_mgr.record_expense("Rent", 20000.0, "Apartment rent")
        budget_mgr.record_expense("Internet", 4500.0, "Fiber internet + addon")  # Overspent!

        summary = budget_mgr.get_summary()

        # Total planned = 15000 + 20000 + 3000 = 38000
        assert summary["total_planned"] == 38000.0
        # Total actual = 12000 + 20000 + 4500 = 36500
        assert summary["total_actual"] == 36500.0
        # Remaining balance = 50000 - 36500 = 13500
        assert summary["remaining_balance"] == 13500.0
        assert summary["savings"] == 13500.0
        assert summary["savings_percentage"] == 27.0
        assert summary["unallocated_amount"] == 12000.0
        assert summary["is_overall_overspent"] is False

        # Internet is overspent by 1500
        overspent = summary["overspending_categories"]
        assert len(overspent) == 1
        assert overspent[0]["category"] == "Internet"
        assert overspent[0]["overspent_amount"] == 1500.0

    def test_save_and_load_budget(self, budget_mgr):
        b = budget_mgr.create_budget("December 2026", "Home & Kitchen", 120000.0)
        budget_mgr.record_expense("Grocery", 8000.0, "Weekly grocery")
        budget_mgr.save_current_budget()

        # Create new manager pointing to same tmp_path
        new_mgr = MonthlyBudgetManager(data_manager=budget_mgr.data_manager)
        loaded = new_mgr.load_budget_for_month("December 2026")
        assert loaded is not None
        assert loaded.total_available == 120000.0
        assert len(loaded.expenses) == 1
        assert loaded.expenses[0].amount == 8000.0
