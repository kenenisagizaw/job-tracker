from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_applications: int
    status_distribution: dict[str, int]
