from flask import Blueprint, request, jsonify
from backend.services.webauthn_service import WebAuthnService
import base64

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
webauthn_service = WebAuthnService()

@bp.route('/begin-registration', methods=['POST'])
def begin_registration():
    data = request.get_json()
    username = data.get('username')
    display_name = data.get('displayName')
    if not username or not display_name:
        return jsonify({"status": "error", "error": {"code": "bad_request", "message": "Missing username or displayName"}}), 400
    options = webauthn_service.generate_registration_options(username, display_name)
    return jsonify({"status": "success", "data": {"publicKey": options}})

@bp.route('/complete-registration', methods=['POST'])
def complete_registration():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({"status": "error", "error": {"code": "bad_request", "message": "Missing username in response"}}), 400
    result = webauthn_service.verify_registration_response(data)
    if not result.get('success'):
        return jsonify({"status": "error", "error": {"code": "registration_failed", "message": result.get('error', 'Unknown error')}}), 400
    return jsonify({"status": "success", "data": {
        "credentialId": b64url_encode(result["credential_id"]),
        "publicKey": b64url_encode(result["public_key"]),
        "signCount": result["sign_count"]
    }})

@bp.route('/begin-authentication', methods=['POST'])
def begin_authentication():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({"status": "error", "error": {"code": "bad_request", "message": "Missing username"}}), 400
    options = webauthn_service.generate_authentication_options(username)
    if 'error' in options:
        return jsonify({"status": "error", "error": {"code": "no_credential", "message": options['error']}}), 400
    return jsonify({"status": "success", "data": {"publicKey": options}})

@bp.route('/complete-authentication', methods=['POST'])
def complete_authentication():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({"status": "error", "error": {"code": "bad_request", "message": "Missing username in response"}}), 400
    result = webauthn_service.verify_authentication_response(data)
    if not result.get('success'):
        return jsonify({"status": "error", "error": {"code": "authentication_failed", "message": result.get('error', 'Unknown error')}}), 400
    return jsonify({"status": "success", "data": {
        "verified": result["success"],
        "newSignCount": result["new_sign_count"]
    }}) 