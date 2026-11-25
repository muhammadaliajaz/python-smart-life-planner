import os
import json
import logging
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class DataManager:
    """
    Handles data persistence for destinations, confirmed trip plans,
    monthly budgets, and developer configuration.
    Safely handles missing or corrupted files.
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # Default to root of project
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, "data")
        self.config_dir = os.path.join(self.base_dir, "config")
        self.reports_dir = os.path.join(self.base_dir, "reports")
        
        # Audit log of data operations using collections.deque
        self.operation_history = deque(maxlen=50)

        # Ensure directories exist
        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Create required directories if they do not exist."""
        for path in (self.data_dir, self.config_dir, self.reports_dir):
            os.makedirs(path, exist_ok=True)

    def _safe_load_json(self, file_path: str, default_data: Any) -> Any:
        """Helper to load JSON file safely, returning default_data on error."""
        if not os.path.exists(file_path):
            self.operation_history.append(f"File not found: {file_path}. Using defaults.")
            return default_data
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self.operation_history.append(f"File empty: {file_path}. Using defaults.")
                    return default_data
                return json.loads(content)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
            self.operation_history.append(f"Corrupt/Unreadable JSON in {file_path}: {e}")
            logger.warning("Corrupted or invalid JSON in %s: %s", file_path, e)
            return default_data

    def _safe_save_json(self, file_path: str, data: Any) -> bool:
        """Save JSON data atomically/safely to disk."""
        try:
            self.ensure_directories()
            temp_path = f"{file_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic replace on Windows / POSIX
            if os.path.exists(file_path):
                os.replace(temp_path, file_path)
            else:
                os.rename(temp_path, file_path)
            self.operation_history.append(f"Saved JSON: {file_path}")
            return True
        except (OSError, TypeError) as e:
            self.operation_history.append(f"Failed to save {file_path}: {e}")
            logger.error("Error saving JSON to %s: %s", file_path, e)
            if os.path.exists(f"{file_path}.tmp"):
                try:
                    os.remove(f"{file_path}.tmp")
                except OSError:
                    pass
            return False

    def load_developer_config(self) -> Dict[str, str]:
        """Load developer profile from config/developer.json."""
        config_path = os.path.join(self.config_dir, "developer.json")
        default_config = {
            "developer_name": "Muhammad Ali Ajaz",
            "github_username": "muhammadaliajaz",
            "email": "chaudharyaliajaz@gmail.com"
        }
        data = self._safe_load_json(config_path, default_config)
        # Ensure keys exist
        if not isinstance(data, dict):
            return default_config
        return {
            "developer_name": data.get("developer_name", default_config["developer_name"]),
            "github_username": data.get("github_username", default_config["github_username"]),
            "email": data.get("email", default_config["email"])
        }

    def save_developer_config(self, config_dict: Dict[str, str]) -> bool:
        """Save developer configuration."""
        config_path = os.path.join(self.config_dir, "developer.json")
        return self._safe_save_json(config_path, config_dict)

    def load_destinations_raw(self) -> List[Dict[str, Any]]:
        """Load destinations from data/destinations.json."""
        dest_path = os.path.join(self.data_dir, "destinations.json")
        data = self._safe_load_json(dest_path, {"destinations": []})
        if isinstance(data, dict) and "destinations" in data:
            return data.get("destinations", [])
        elif isinstance(data, list):
            return data
        return []

    def load_trips(self) -> List[Dict[str, Any]]:
        """Load confirmed trips."""
        path = os.path.join(self.data_dir, "trips.json")
        data = self._safe_load_json(path, [])
        return data if isinstance(data, list) else []

    def save_trips(self, trips: List[Dict[str, Any]]) -> bool:
        """Save confirmed trips."""
        path = os.path.join(self.data_dir, "trips.json")
        return self._safe_save_json(path, trips)

    def append_trip(self, trip_dict: Dict[str, Any]) -> bool:
        """Append a newly confirmed trip plan to trips.json."""
        trips = self.load_trips()
        trips.append(trip_dict)
        return self.save_trips(trips)

    def load_budgets(self) -> List[Dict[str, Any]]:
        """Load monthly budget records."""
        path = os.path.join(self.data_dir, "budgets.json")
        data = self._safe_load_json(path, [])
        return data if isinstance(data, list) else []

    def save_budgets(self, budgets: List[Dict[str, Any]]) -> bool:
        """Save monthly budget records."""
        path = os.path.join(self.data_dir, "budgets.json")
        return self._safe_save_json(path, budgets)

    def upsert_budget(self, budget_dict: Dict[str, Any]) -> bool:
        """Save or update budget record by month."""
        budgets = self.load_budgets()
        month = budget_dict.get("month")
        updated = False
        for i, b in enumerate(budgets):
            if b.get("month") == month:
                budgets[i] = budget_dict
                updated = True
                break
        if not updated:
            budgets.append(budget_dict)
        return self.save_budgets(budgets)

    def list_generated_reports(self) -> List[str]:
        """List all generated PDF report files in the reports directory."""
        if not os.path.exists(self.reports_dir):
            return []
        try:
            files = [
                f for f in os.listdir(self.reports_dir)
                if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(self.reports_dir, f))
            ]
            files.sort(reverse=True)
            return files
        except OSError:
            return []
