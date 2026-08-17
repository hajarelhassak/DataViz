from flask import Blueprint, jsonify


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard"
)



@dashboard_bp.route("/stats", methods=["GET"])
def get_dashboard_stats():


    # Plus tard remplacer par des requêtes SQLAlchemy


    stats = {

        "projects": 0,

        "connections": 0,

        "kpis": 0,

        "analyses": 0

    }


    return jsonify(stats)