import os
from app import create_app
from database.seed_data import seed_database

app = create_app()

# Ensure database tables and seed data exist on startup (works with Gunicorn & Flask CLI)
with app.app_context():
    seed_database(app)

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')

    print(f"\n========================================================")
    print(f" SMARTHEAT Disaster Response Management System")
    print(f" Server running on: http://{host}:{port}")
    print(f" Primary Admin: Anant10")
    print(f" Login & Register: http://{host}:{port}/auth/login")
    print(f"========================================================\n")
    app.run(host=host, port=port, debug=debug)
