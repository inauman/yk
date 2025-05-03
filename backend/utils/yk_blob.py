import os
import base64
import sqlite3
from fido2.ctap2.base import Ctap2
from fido2.ctap2 import LargeBlobs
from fido2.ctap2.extensions import HmacSecretExtension
from fido2.hid import CtapHidDevice
from backend.models.init_db import DB_PATH

def get_credential_id_for_username(username: str) -> bytes:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            SELECT credential_id FROM credentials
            JOIN users ON credentials.user_id = users.id
            WHERE users.username=?
            ORDER BY credentials.id DESC LIMIT 1
        """, (username,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f'No credential found for username {username}')
        return base64.urlsafe_b64decode(row[0])

def get_fido2_device():
    devices = list(CtapHidDevice.list_devices())
    if not devices:
        raise RuntimeError('No FIDO device found')
    return devices[0]

def write_blob(username: str, blob: bytes):
    cred_id = get_credential_id_for_username(username)
    device = get_fido2_device()
    ctap2 = Ctap2(device)
    large_blobs = LargeBlobs(ctap2)
    try:
        # This will prompt for user touch
        large_blobs.set_blob(cred_id, blob)
    except Exception as e:
        raise RuntimeError(f'Failed to write large blob: {e}')

def read_blob(username: str) -> bytes:
    cred_id = get_credential_id_for_username(username)
    device = get_fido2_device()
    ctap2 = Ctap2(device)
    large_blobs = LargeBlobs(ctap2)
    try:
        # This will prompt for user touch
        blob = large_blobs.get_blob(cred_id)
        return blob
    except Exception as e:
        raise RuntimeError(f'Failed to read large blob: {e}')

def derive_hmac_secret_from_yk(username: str, salt: bytes) -> bytes:
    cred_id = get_credential_id_for_username(username)
    device = get_fido2_device()
    ctap2 = Ctap2(device)
    # TODO: Use HmacSecretExtension to perform hmac-secret operation
    # See fido2.ctap2.extensions.HmacSecretExtension for usage
    raise NotImplementedError('HmacSecretExtension usage for hmac-secret not yet implemented') 