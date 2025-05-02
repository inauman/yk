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

class WebAuthnService:
    """
    Service for handling WebAuthn registration and authentication ceremonies using webauthn 2.x API.
    Maintains in-memory challenge and credential storage for demo/testing purposes.
    """
    def __init__(self):
        # In-memory challenge store: {username: challenge}
        self.challenges = {}
        # In-memory credential store: {username: {"credential_id": ..., "public_key": ..., "sign_count": ...}}
        self.credentials = {}
        # Relying party info (customize as needed)
        self.rp_id = "localhost"  # Change to your domain in production
        self.rp_name = "YK Bitcoin Seed Vault"

    def generate_registration_options(self, username: str, display_name: str) -> dict:
        """
        Generate WebAuthn registration options (challenge, user info, etc.)
        :param username: The username of the registering user
        :param display_name: The display name for the user
        :return: A dictionary with registration options
        """
        # Generate a random user id (should be stable per user in production)
        user_id = os.urandom(16)
        authenticator_selection = AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
            resident_key=ResidentKeyRequirement.REQUIRED,
            require_resident_key=True,
        )
        options = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_name=username,
            user_id=user_id,
            user_display_name=display_name,
            authenticator_selection=authenticator_selection,
        )
        # Store challenge for later verification (as bytes)
        self.challenges[username] = options.challenge
        return options_to_json(options)

    def verify_registration_response(self, response: dict) -> dict:
        """
        Verify the WebAuthn registration response from the client.
        :param response: The response object from the client
        :return: A dictionary with verification result and credential info
        """
        try:
            username = response.get('username')
            challenge = self.challenges.get(username)
            if not challenge:
                return {"success": False, "error": "No challenge found for user."}
            verification = verify_registration_response(
                credential=response,
                expected_challenge=challenge,
                expected_rp_id=self.rp_id,
                expected_origin="https://localhost:5173",  # Match frontend dev server origin
                require_user_verification=True,
            )
            # Store credential for authentication
            self.credentials[username] = {
                "credential_id": verification.credential_id,
                "public_key": verification.credential_public_key,
                "sign_count": verification.sign_count
            }
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
        """
        Generate WebAuthn authentication (assertion) options for the given user.
        :param username: The username of the authenticating user
        :return: A dictionary with authentication options
        """
        cred = self.credentials.get(username)
        if not cred:
            return {"error": "No credential registered for user."}
        options = generate_authentication_options(
            rp_id=self.rp_id,
            allow_credentials=[PublicKeyCredentialDescriptor(
                id=cred["credential_id"],
                type=PublicKeyCredentialType.PUBLIC_KEY
            )],
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        self.challenges[username] = options.challenge
        return options_to_json(options)

    def verify_authentication_response(self, response: dict) -> dict:
        """
        Verify the WebAuthn authentication (assertion) response from the client.
        :param response: The response object from the client
        :return: A dictionary with verification result
        """
        try:
            username = response.get('username')
            challenge = self.challenges.get(username)
            cred = self.credentials.get(username)
            if not challenge or not cred:
                return {"success": False, "error": "No challenge or credential found for user."}
            verification = verify_authentication_response(
                credential=response,
                expected_challenge=challenge,
                expected_rp_id=self.rp_id,
                expected_origin="https://localhost:5173",  # Match frontend dev server origin
                credential_public_key=cred["public_key"],
                credential_current_sign_count=cred["sign_count"],
                require_user_verification=True,
            )
            # Update sign count
            cred["sign_count"] = verification.new_sign_count
            return {
                "success": True,
                "new_sign_count": verification.new_sign_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)} 