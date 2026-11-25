import os
import pytest
from pdf.pdf_generator import PDFReportGenerator
from utils.data_manager import DataManager
from models.trip import TripPlan
from models.budget import Budget
from models.destination import Destination
from services.trip_calculator import TripCostCalculator


@pytest.fixture
def pdf_gen(tmp_path):
    dm = DataManager(base_dir=str(tmp_path))
    dm.save_developer_config({
        "developer_name": "Muhammad Ali Ajaz",
        "github_username": "muhammadaliajaz",
        "email": "chaudharyaliajaz@gmail.com"
    })
    return PDFReportGenerator(data_manager=dm)


@pytest.fixture
def confirmed_trip():
    dest = Destination(
        name="Skardu",
        region="Gilgit-Baltistan",
        category="Lakes & Nature",
        room_capacity=2,
        base_transport_cost_per_person=10000,
        base_accommodation_cost_per_room_night=6000,
        food_cost_per_person_day=2500,
        activities_misc_cost_per_person=3000,
        highlights=["Shangrila Lake", "Deosai Plains"]
    )
    plan = TripPlan(
        destination_name="Skardu",
        departure_city="Islamabad",
        travellers=2,
        days=4,
        nights=3,
        available_budget=100000.0,
        travel_category="Standard",
        destination_type="Lakes & Nature",
        itinerary=[
            {"day": 1, "title": "Arrival in Skardu", "description": "Flight/Drive to Skardu", "accommodation": "Shangrila Resort", "meals": "Dinner"},
            {"day": 2, "title": "Upper Kachura Lake", "description": "Boating and hiking", "accommodation": "Shangrila Resort", "meals": "All meals"},
            {"day": 3, "title": "Deosai Plains Excursion", "description": "Sheosar lake visit", "accommodation": "Skardu Hotel", "meals": "All meals"},
            {"day": 4, "title": "Return to Islamabad", "description": "Flight back home", "accommodation": "Home", "meals": "Breakfast"}
        ]
    )
    plan.breakdown = TripCostCalculator.calculate_cost(
        dest, 2, 4, 3, available_budget=100000.0, travel_category="Standard"
    )
    plan.confirm_plan()
    return plan


class TestPDFGenerator:
    def test_unconfirmed_trip_rejects_pdf_generation(self, pdf_gen):
        unconfirmed = TripPlan("Murree", "Islamabad", 2, 2, 1, 30000.0)
        unconfirmed.breakdown = TripCostCalculator.calculate_cost(
            Destination("Murree", "Punjab", "Mountains"), 2, 2, 1, 30000.0
        )
        assert unconfirmed.is_confirmed is False

        with pytest.raises(ValueError, match="Cannot generate final PDF report for an unconfirmed trip plan"):
            pdf_gen.generate_trip_pdf(unconfirmed)

    def test_confirmed_trip_generates_pdf(self, pdf_gen, confirmed_trip):
        pdf_path = pdf_gen.generate_trip_pdf(confirmed_trip)
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith(".pdf")
        assert os.path.getsize(pdf_path) > 1000  # Non-trivial PDF size

    def test_monthly_budget_generates_pdf(self, pdf_gen):
        budget = Budget("November 2026", "Home & Kitchen", 90000.0, planned_categories={
            "Grocery": 25000.0,
            "Electricity": 15000.0,
            "Rent": 35000.0
        })
        budget.add_expense(budget.expenses and None or __import__("models.expense").expense.Expense(
            category="Grocery",
            amount=22000.0,
            description="Monthly grocery store checkout",
            date_str="2026-11-10"
        ))

        pdf_path = pdf_gen.generate_budget_pdf(budget)
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith(".pdf")
        assert os.path.getsize(pdf_path) > 1000

    def test_unique_pdf_filenames_prevent_overwriting(self, pdf_gen, confirmed_trip):
        file1 = pdf_gen.generate_trip_pdf(confirmed_trip)
        file2 = pdf_gen.generate_trip_pdf(confirmed_trip)
        assert file1 != file2
        assert os.path.exists(file1)
        assert os.path.exists(file2)
