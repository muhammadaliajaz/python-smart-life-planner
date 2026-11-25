import os
import json
import pytest
from utils.data_manager import DataManager


@pytest.fixture
def temp_dm(tmp_path):
    return DataManager(base_dir=str(tmp_path))


class TestDataManager:
    def test_directory_creation(self, temp_dm):
        assert os.path.exists(temp_dm.data_dir)
        assert os.path.exists(temp_dm.config_dir)
        assert os.path.exists(temp_dm.reports_dir)

    def test_developer_config_defaults(self, temp_dm):
        cfg = temp_dm.load_developer_config()
        assert "developer_name" in cfg
        assert "github_username" in cfg
        assert "email" in cfg

    def test_save_and_load_developer_config(self, temp_dm):
        custom = {
            "developer_name": "Test Student",
            "github_username": "student-test",
            "email": "student@example.com"
        }
        assert temp_dm.save_developer_config(custom) is True
        loaded = temp_dm.load_developer_config()
        assert loaded["developer_name"] == "Test Student"
        assert loaded["github_username"] == "student-test"
        assert loaded["email"] == "student@example.com"

    def test_corrupted_json_handling(self, temp_dm):
        corrupt_path = os.path.join(temp_dm.data_dir, "trips.json")
        with open(corrupt_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json content ...")

        trips = temp_dm.load_trips()
        assert trips == []  # Gracefully returns default empty list without crashing

    def test_empty_json_handling(self, temp_dm):
        empty_path = os.path.join(temp_dm.data_dir, "budgets.json")
        with open(empty_path, "w", encoding="utf-8") as f:
            f.write("")

        budgets = temp_dm.load_budgets()
        assert budgets == []

    def test_trips_persistence(self, temp_dm):
        trip_entry = {
            "plan_id": "TRIP-001",
            "destination_name": "Swat",
            "travellers": 3,
            "days": 4,
            "nights": 3,
            "available_budget": 50000.0
        }
        assert temp_dm.append_trip(trip_entry) is True
        loaded = temp_dm.load_trips()
        assert len(loaded) == 1
        assert loaded[0]["destination_name"] == "Swat"

    def test_list_generated_reports(self, temp_dm):
        assert temp_dm.list_generated_reports() == []
        rep_file = os.path.join(temp_dm.reports_dir, "Trip_Report_Test_2026.pdf")
        with open(rep_file, "w", encoding="utf-8") as f:
            f.write("%PDF-dummy")
        reps = temp_dm.list_generated_reports()
        assert "Trip_Report_Test_2026.pdf" in reps
