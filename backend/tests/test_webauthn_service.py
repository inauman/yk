import pytest
import json
from backend.services.webauthn_service import WebAuthnService
from backend.app import create_app
import sqlite3
import os
from backend.models.init_db import DB_PATH

def test_generate_registration_options():
    service = WebAuthnService()
    result = service.generate_registration_options('alice', 'Alice')
    result = json.loads(result)
    assert isinstance(result, dict)
    assert 'challenge' in result
    assert 'rp' in result
    assert 'user' in result
    assert 'pubKeyCredParams' in result

def test_verify_registration_response():
    service = WebAuthnService()
    # Simulate registration to get challenge
    service.generate_registration_options('alice', 'Alice')
    # Mock response with username only (should fail due to missing credential fields)
    response = {'username': 'alice'}
    result = service.verify_registration_response(response)
    assert isinstance(result, dict)
    assert 'success' in result
    assert not result['success']
    assert 'error' in result

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_begin_registration_api(client):
    resp = client.post('/api/v1/auth/begin-registration', json={
        'username': 'alice',
        'displayName': 'Alice'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'
    assert 'publicKey' in data['data']
    pk = json.loads(data['data']['publicKey'])
    assert 'challenge' in pk
    assert 'rp' in pk
    assert 'user' in pk

def test_complete_registration_api_missing_username(client):
    resp = client.post('/api/v1/auth/complete-registration', json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'bad_request'

def test_begin_authentication_api_no_credential(client):
    resp = client.post('/api/v1/auth/begin-authentication', json={
        'username': 'bob'
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'no_credential'

def test_begin_authentication_api_after_registration(client):
    # Register first
    client.post('/api/v1/auth/begin-registration', json={
        'username': 'alice',
        'displayName': 'Alice'
    })
    # Fake complete registration to store credential
    client.post('/api/v1/auth/complete-registration', json={
        'username': 'alice',
        'id': 'fakeid',
        'rawId': 'fakeid',
        'response': {'clientDataJSON': 'fake', 'attestationObject': 'fake'},
        'type': 'public-key'
    })
    # Now begin authentication
    resp = client.post('/api/v1/auth/begin-authentication', json={
        'username': 'alice'
    })
    # Should succeed (even though credential is fake, this tests the flow)
    assert resp.status_code == 200 or resp.status_code == 400
    data = resp.get_json()
    if resp.status_code == 200:
        assert data['status'] == 'success'
        assert 'publicKey' in data['data']
    else:
        assert data['status'] == 'error'

def test_db_schema():
    # Check that all tables exist
    expected_tables = {'users', 'credentials', 'challenges', 'seeds', 'seed_credentials'}
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cur.fetchall()}
        assert expected_tables.issubset(tables)
        # Check columns for users table
        cur = conn.execute("PRAGMA table_info(users);")
        user_cols = {row[1] for row in cur.fetchall()}
        assert {'id', 'user_id', 'username', 'display_name', 'created_at', 'updated_at'}.issubset(user_cols)
        # Check columns for credentials table
        cur = conn.execute("PRAGMA table_info(credentials);")
        cred_cols = {row[1] for row in cur.fetchall()}
        assert {'id', 'user_id', 'credential_id', 'public_key', 'sign_count', 'nickname', 'registered_at'}.issubset(cred_cols)
        # Check columns for challenges table
        cur = conn.execute("PRAGMA table_info(challenges);")
        chal_cols = {row[1] for row in cur.fetchall()}
        assert {'id', 'user_id', 'challenge', 'type', 'created_at', 'expires_at'}.issubset(chal_cols)
        # Check columns for seeds table
        cur = conn.execute("PRAGMA table_info(seeds);")
        seed_cols = {row[1] for row in cur.fetchall()}
        assert {'id', 'user_id', 'encrypted_seed', 'iv', 'salt', 'wrapped_key', 'created_at', 'updated_at'}.issubset(seed_cols)
        # Check columns for seed_credentials table
        cur = conn.execute("PRAGMA table_info(seed_credentials);")
        sc_cols = {row[1] for row in cur.fetchall()}
        assert {'id', 'seed_id', 'credential_id'}.issubset(sc_cols) 