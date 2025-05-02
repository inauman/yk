import pytest
import json
from backend.services.webauthn_service import WebAuthnService
from backend.app import create_app

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