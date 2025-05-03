from flask import Blueprint, request, jsonify
from backend.utils.seed_utils import gen_mnemonic, encrypt_seed, decrypt_blob, entropy_to_mnemonic
from backend.utils.yk_blob import write_blob, read_blob

bp = Blueprint('seed', __name__, url_prefix='/api/v1/seed')

@bp.route('/store', methods=['POST'])
def store_seed():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'status': 'error', 'error': 'Missing username'}), 400
    mnemonic, entropy = gen_mnemonic()
    try:
        blob = encrypt_seed(username, entropy)
        write_blob(username, blob)
        # Do not return mnemonic for security
        return jsonify({'status': 'success', 'message': 'Seed stored.'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@bp.route('/retrieve', methods=['POST'])
def retrieve_seed():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'status': 'error', 'error': 'Missing username'}), 400
    try:
        blob = read_blob(username)
        entropy = decrypt_blob(username, blob)
        mnemonic = entropy_to_mnemonic(entropy)
        return jsonify({'status': 'success', 'mnemonic': mnemonic}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500 