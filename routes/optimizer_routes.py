from flask import Blueprint, render_template
from routes.auth_routes import login_required

optimizer_bp = Blueprint('optimizer', __name__, url_prefix='/optimizer')

@optimizer_bp.route('/')
@login_required
def index():
    return render_template('optimizer.html')
