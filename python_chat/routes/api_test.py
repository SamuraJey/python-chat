import secrets

from flask import Blueprint, current_app, jsonify, request, session
from flask_login import current_user, login_required

bp = Blueprint("api_test", __name__, url_prefix="/api/test")


@bp.route("/ping", methods=["GET"])
def ping():
    """Test endpoint that does not require authentication"""
    return jsonify({"message": "pong", "authenticated": current_user.is_authenticated, "username": current_user.username if current_user.is_authenticated else None})


@bp.route("/auth", methods=["GET"])
@login_required
def auth_test():
    """Test endpoint that requires authentication"""
    return jsonify({"message": "You are authenticated", "username": current_user.username, "user_id": current_user.id})


@bp.route("/csrf-token", methods=["GET"])
def get_csrf_token():
    """Generate a CSRF token for testing"""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)

    return jsonify({"csrf_token": session["csrf_token"]})


@bp.route("/form-submit", methods=["POST"])
def test_form_submit():
    """Test form submission with CSRF token"""
    csrf_token = request.form.get("csrf_token")
    test_data = request.form.get("test_data")

    # Log all headers for debugging
    headers = {key: value for key, value in request.headers.items()}
    current_app.logger.debug(f"Form submission headers: {headers}")

    # Log form data
    current_app.logger.debug(f"Form data: {request.form}")

    if not csrf_token or csrf_token != session.get("csrf_token"):
        return jsonify({"success": False, "error": "CSRF token validation failed", "received_token": csrf_token, "expected_token": session.get("csrf_token")}), 403

    return jsonify({"success": True, "message": "Form submission successful", "received_data": test_data})


@bp.route("/json-submit", methods=["POST"])
def test_json_submit():
    """Test JSON submission with CSRF token"""
    data = request.get_json()

    # Log all headers for debugging
    headers = {key: value for key, value in request.headers.items()}
    current_app.logger.debug(f"JSON submission headers: {headers}")

    # Log JSON data
    current_app.logger.debug(f"JSON data: {data}")

    csrf_token = data.get("csrf_token") if data else None
    test_data = data.get("test_data") if data else None

    # Also check X-CSRFToken header
    header_token = request.headers.get("X-CSRFToken")

    if header_token and header_token == session.get("csrf_token"):
        # Token from header is valid
        pass
    elif csrf_token and csrf_token == session.get("csrf_token"):
        # Token from JSON body is valid
        pass
    else:
        return jsonify(
            {"success": False, "error": "CSRF token validation failed", "received_token_body": csrf_token, "received_token_header": header_token, "expected_token": session.get("csrf_token")}
        ), 403

    return jsonify({"success": True, "message": "JSON submission successful", "received_data": test_data})
