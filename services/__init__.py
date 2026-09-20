from services.risk_service import calculate_composite_heat_risk, compute_hazard_score
from services.alert_service import (
    check_and_create_alert, resolve_alert, get_active_alerts_count,
    get_recent_alerts, generate_simulated_dispatch_log
)
from services.recommendation_engine import (
    get_recommendations_for_level, get_all_recommendations_grouped
)
from services.realtime_weather_service import (
    fetch_live_weather, sync_all_stations_realtime
)

__all__ = [
    'calculate_composite_heat_risk',
    'compute_hazard_score',
    'check_and_create_alert',
    'resolve_alert',
    'get_active_alerts_count',
    'get_recent_alerts',
    'generate_simulated_dispatch_log',
    'get_recommendations_for_level',
    'get_all_recommendations_grouped',
    'fetch_live_weather',
    'sync_all_stations_realtime'
]
