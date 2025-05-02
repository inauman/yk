from typing import Any, Dict
import os
import base64
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers import options_to_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
)
import sqlite3
from backend.models.init_db import DB_PATH

class WebAuthnService:
    """
    Service for handling WebAuthn registration and authentication ceremonies using webauthn 2.x API.
    Maintains in-memory challenge and credential storage for demo/testing purposes.
    """
    def __init__(self):
        self.rp_id = "localhost"
        self.rp_name = "YK Bitcoin Seed Vault"

    def _get_conn(self):
        return sqlite3.connect(DB_PATH)

    def _get_user(self, username):
        with self._get_conn() as conn:
            cur = conn.execute("SELECT id, user_id, username, display_name FROM users WHERE username=?", (username,))
            return cur.fetchone()

    def _create_user(self, username, display_name, user_id_bytes):
        with self._get_conn() as conn:
            conn.execute("INSERT INTO users (user_id, username, display_name) VALUES (?, ?, ?)", (base64.urlsafe_b64encode(user_id_bytes).decode(), username, display_name))
            conn.commit()
            return self._get_user(username)

    def generate_registration_options(self, username: str, display_name: str) -> dict:
        user = self._get_user(username)
        if user:
            user_id_bytes = base64.urlsafe_b64decode(user[1])
        else:
            user_id_bytes = os.urandom(16)
            self._create_user(username, display_name, user_id_bytes)
        authenticator_selection = AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
            resident_key=ResidentKeyRequirement.REQUIRED,
            require_resident_key=True,
        )
        options = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_name=username,
            user_id=user_id_bytes,
            user_display_name=display_name,
            authenticator_selection=authenticator_selection,
        )
        # Store challenge in DB
        with self._get_conn() as conn:
            user = self._get_user(username)
            conn.execute("INSERT INTO challenges (user_id, challenge, type) VALUES (?, ?, 'registration')", (user[0], base64.urlsafe_b64encode(options.challenge).decode()))
            conn.commit()
        return options_to_json(options)

    def verify_registration_response(self, response: dict) -> dict:
        try:
            username = response.get('username')
            user = self._get_user(username)
            if not user:
                return {"success": False, "error": "User not found."}
            with self._get_conn() as conn:
                cur = conn.execute("SELECT challenge FROM challenges WHERE user_id=? AND type='registration' ORDER BY created_at DESC LIMIT 1", (user[0],))
                row = cur.fetchone()
                if not row:
                    return {"success": False, "error": "No challenge found for user."}
                challenge = base64.urlsafe_b64decode(row[0])
            verification = verify_registration_response(
                credential=response,
                expected_challenge=challenge,
                expected_rp_id=self.rp_id,
                expected_origin="https://localhost:5173",
                require_user_verification=True,
            )
            # Store credential in DB
            with self._get_conn() as conn:
                conn.execute("INSERT INTO credentials (user_id, credential_id, public_key, sign_count) VALUES (?, ?, ?, ?)",
                    (user[0], base64.urlsafe_b64encode(verification.credential_id).decode(), base64.urlsafe_b64encode(verification.credential_public_key).decode(), verification.sign_count))
                conn.commit()
            return {
                "success": True,
                "credential_id": verification.credential_id,
                "public_key": verification.credential_public_key,
                "sign_count": verification.sign_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def b64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

    def generate_authentication_options(self, username: str) -> dict:
        user = self._get_user(username)
        if not user:
            return {"error": "User not found."}
        with self._get_conn() as conn:
            cur = conn.execute("SELECT credential_id FROM credentials WHERE user_id=? ORDER BY id DESC LIMIT 1", (user[0],))
            row = cur.fetchone()
            if not row:
                return {"error": "No credential registered for user."}
            cred_id = base64.urlsafe_b64decode(row[0])
        options = generate_authentication_options(
            rp_id=self.rp_id,
            allow_credentials=[PublicKeyCredentialDescriptor(
                id=cred_id,
                type=PublicKeyCredentialType.PUBLIC_KEY
            )],
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        # Store challenge in DB
        with self._get_conn() as conn:
            conn.execute("INSERT INTO challenges (user_id, challenge, type) VALUES (?, ?, 'authentication')", (user[0], base64.urlsafe_b64encode(options.challenge).decode()))
            conn.commit()
        return options_to_json(options)

    def verify_authentication_response(self, response: dict) -> dict:
        try:
            username = response.get('username')
            user = self._get_user(username)
            if not user:
                return {"success": False, "error": "User not found."}
            with self._get_conn() as conn:
                cur = conn.execute("SELECT challenge FROM challenges WHERE user_id=? AND type='authentication' ORDER BY created_at DESC LIMIT 1", (user[0],))
                row = cur.fetchone()
                if not row:
                    return {"success": False, "error": "No challenge found for user."}
                challenge = base64.urlsafe_b64decode(row[0])
                cur = conn.execute("SELECT credential_id, public_key, sign_count FROM credentials WHERE user_id=? ORDER BY id DESC LIMIT 1", (user[0],))
                cred_row = cur.fetchone()
                if not cred_row:
                    return {"success": False, "error": "No credential found for user."}
                cred_id = base64.urlsafe_b64decode(cred_row[0])
                public_key = base64.urlsafe_b64decode(cred_row[1])
                sign_count = cred_row[2]
            verification = verify_authentication_response(
                credential=response,
                expected_challenge=challenge,
                expected_rp_id=self.rp_id,
                expected_origin="https://localhost:5173",
                credential_public_key=public_key,
                credential_current_sign_count=sign_count,
                require_user_verification=True,
            )
            # Update sign count in DB
            with self._get_conn() as conn:
                conn.execute("UPDATE credentials SET sign_count=? WHERE user_id=? AND credential_id=?", (verification.new_sign_count, user[0], base64.urlsafe_b64encode(cred_id).decode()))
                conn.commit()
            return {
                "success": True,
                "new_sign_count": verification.new_sign_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)} 