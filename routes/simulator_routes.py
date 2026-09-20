"""
Climate Crisis & Grid Failure Stress Simulator Blueprint
Provides interactive UI for simulating compound climate shocks across India.
"""

from flask import Blueprint, render_template
from routes.auth_routes import login_required

simulator_bp = Blueprint('simulator', __name__, url_prefix='/simulator')

@simulator_bp.route('/')
@login_required
def index():
    return render_template('simulator.html')
