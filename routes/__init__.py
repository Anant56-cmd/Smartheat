from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.weather_routes import weather_bp
from routes.ml_routes import ml_bp
from routes.map_routes import map_bp
from routes.vulnerability_routes import vulnerability_bp
from routes.alert_routes import alert_bp
from routes.report_routes import report_bp
from routes.recommendation_routes import recommendation_bp
from routes.optimizer_routes import optimizer_bp
from routes.api_v1_routes import api_v1_bp
from routes.docs_routes import docs_bp
from routes.simulator_routes import simulator_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'weather_bp',
    'ml_bp',
    'map_bp',
    'vulnerability_bp',
    'alert_bp',
    'report_bp',
    'recommendation_bp',
    'optimizer_bp',
    'api_v1_bp',
    'docs_bp',
    'simulator_bp'
]
