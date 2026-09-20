import os
from flask import Flask, render_template
from config import Config
from database.db import db
from database.models import Alert
from routes import (
    auth_bp, dashboard_bp, weather_bp, ml_bp,
    map_bp, vulnerability_bp, alert_bp, report_bp,
    recommendation_bp, optimizer_bp, api_v1_bp,
    docs_bp, simulator_bp
)

def create_app(config_class=Config):
    """Application factory for SMARTHEAT disaster management platform."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MODEL_DIR'], exist_ok=True)
    os.makedirs(os.path.join(Config.BASE_DIR, 'database'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(vulnerability_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(optimizer_bp)
    app.register_blueprint(api_v1_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(simulator_bp)

    # Global context processors for dynamic alerts badge in navbar
    @app.context_processor
    def inject_global_context():
        try:
            active_alerts = Alert.query.filter_by(status='Active').count()
        except Exception:
            active_alerts = 0
        return {
            'nav_active_alerts': active_alerts,
            'app_title': 'SMARTHEAT — Pan-India Heat Wave Intelligence'
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Favicon route for direct browser requests
    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory
        return send_from_directory(os.path.join(app.root_path, 'static', 'img'),
                                   'favicon.svg', mimetype='image/svg+xml')

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from database.seed_data import seed_database
        seed_database(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
