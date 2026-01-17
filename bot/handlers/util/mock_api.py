from typing import Dict, Any
from datetime import datetime, timedelta
import random


class MockMetricsAPI:
    """Mock class to generate realistic test data for the metrics dashboard"""

    def __init__(self):
        # Base data that stays relatively consistent
        self.base_data = {
            "Team Performance": {
                "online": random.randint(8, 15),
                "on_job": random.randint(5, 12),
                "avg_rating": round(random.uniform(4.0, 5.0), 1),
                "efficiency": random.randint(75, 98),
                "top_performers": ["Alex Chen", "Maria Rodriguez", "Sam Taylor"]
            },
            "Job Progress": {
                "completed": random.randint(15, 30),
                "in_progress": random.randint(5, 12),
                "scheduled": random.randint(8, 20),
                "avg_duration": random.randint(45, 120),
                "on_time_rate": random.randint(85, 99)
            },
            "Equipment Status": {
                "operational": random.randint(90, 100),
                "maintenance_needed": random.randint(0, 10),
                "out_of_service": random.randint(0, 5),
                "utilization_rate": random.randint(70, 95)
            },
            "Customer Feedback": {
                "five_star": random.randint(75, 95),
                "four_star": random.randint(5, 20),
                "three_or_less": random.randint(0, 5),
                "nps_score": random.randint(70, 95),
                "recent_comments": ["Great service!", "Very professional", "Arrived on time"]
            },
            "Financial Metrics": {
                "revenue_today": round(random.uniform(2500, 5000), 2),
                "expenses_today": round(random.uniform(1000, 2500), 2),
                "margin_today": round(random.uniform(50, 75), 1),
                "outstanding_invoices": random.randint(5, 15),
                "avg_job_value": round(random.uniform(150, 300), 2)
            },
            "all": {
                "teams_active": random.randint(4, 8),
                "teams_total": 8,
                "jobs_today": random.randint(20, 40),
                "revenue_today": round(random.uniform(3000, 6000), 2),
                "efficiency": random.randint(80, 95),
                "efficiency_week": random.randint(75, 98)
            }
        }

        self.last_update = datetime.now()

    def get_metrics(self, category: str, admin_id: str) -> Dict[str, Any]:
        """Generate metrics data with small variations each time"""

        # If it's been over 10 seconds since last update, create some variations
        if (datetime.now() - self.last_update).total_seconds() > 10:
            self._update_metrics()
            self.last_update = datetime.now()

        # Return the requested category data
        if category in self.base_data:
            return self.base_data[category]
        else:
            return self.base_data["all"]  # Default fallback

    def _update_metrics(self):
        """Make small random variations to the metrics"""

        # Team Performance variations
        self.base_data["Team Performance"]["online"] += random.randint(-2, 2)
        self.base_data["Team Performance"]["online"] = max(5, min(18, self.base_data["Team Performance"]["online"]))

        self.base_data["Team Performance"]["on_job"] += random.randint(-1, 1)
        self.base_data["Team Performance"]["on_job"] = max(3, min(15, self.base_data["Team Performance"]["on_job"]))

        self.base_data["Team Performance"]["efficiency"] += random.randint(-3, 3)
        self.base_data["Team Performance"]["efficiency"] = max(70, min(100, self.base_data["Team Performance"][
            "efficiency"]))

        # Job Progress variations
        self.base_data["Job Progress"]["completed"] += random.randint(0, 2)
        self.base_data["Job Progress"]["in_progress"] += random.randint(-1, 1)
        self.base_data["Job Progress"]["scheduled"] += random.randint(-1, 2)

        # All metrics variations
        self.base_data["all"]["jobs_today"] += random.randint(0, 2)
        self.base_data["all"]["revenue_today"] += round(random.uniform(-100, 200), 2)

        # Randomly shuffle top performers occasionally
        if random.random() < 0.2:
            random.shuffle(self.base_data["Team Performance"]["top_performers"])


# Usage in your main code - add this to your file and modify display_metrics
mock_api = MockMetricsAPI()