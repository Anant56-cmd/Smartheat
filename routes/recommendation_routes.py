from flask import Blueprint, render_template, request
from database.models import ResponseRecommendation
from routes.auth_routes import login_required

recommendation_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')

@recommendation_bp.route('/')
@login_required
def index():
    sector_filter = request.args.get('sector', 'all')
    level_filter = request.args.get('level', 'all')

    query = ResponseRecommendation.query

    if sector_filter != 'all':
        query = query.filter(ResponseRecommendation.target_sector == sector_filter.capitalize())
    if level_filter != 'all':
        query = query.filter(ResponseRecommendation.risk_level == level_filter.upper())

    sops = query.order_by(ResponseRecommendation.risk_level.asc(), ResponseRecommendation.priority.asc()).all()

    # Group by risk level for structured view
    grouped = {'LOW': [], 'MODERATE': [], 'HIGH': [], 'EXTREME': []}
    for item in sops:
        if item.risk_level in grouped:
            grouped[item.risk_level].append(item)

    return render_template(
        'recommendations.html',
        grouped_sops=grouped,
        total_sops=len(sops),
        selected_sector=sector_filter,
        selected_level=level_filter
    )
