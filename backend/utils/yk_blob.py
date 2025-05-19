from fido2.hid import CtapHidDevice
from fido2.client import Fido2Client
from fido2.ctap2.base import Ctap2
from fido2.ctap2.pin import ClientPin
from fido2.ctap2 import CredentialManagement as CM
from fido2.ctap2.blob import LargeBlobs
from typing import Optional
import functools
import os

RP_ID = "localhost"  # must match the RP ID used at registration


def get_yubikey_device():
    """
    Return the first available YubiKey device, or raise if not found.
    """
    dev = next(CtapHidDevice.list_devices(), None)
    if not dev:
        raise RuntimeError("No YubiKey found.")
    return dev


def get_credential_and_largeblobkey(cred_id: bytes, pin: Optional[str] = None):
    """
    Find the resident credential and its largeBlobKey for the given credential ID.
    Args:
        cred_id: Credential ID as bytes
        pin: Optional PIN (if not provided, will prompt)
    Returns:
        (cred, large_blob_key, ctap2, pin_proto, pin_token)
    """
    dev = get_yubikey_device()
    ctap2 = Ctap2(dev)
    client_pin = ClientPin(ctap2)
    if pin is None:
        pin = input("Enter YubiKey PIN: ")
    combined_perms = (
        ClientPin.PERMISSION.CREDENTIAL_MGMT | ClientPin.PERMISSION.LARGE_BLOB_WRITE
    )
    pin_token = client_pin.get_pin_token(
        pin,
        permissions=combined_perms,
    )
    pin_proto = client_pin.protocol
    cred_mgmt = CM(ctap2, pin_proto, pin_token)
    # Enumerate resident RPs & credentials
    rps = list(cred_mgmt.enumerate_rps())
    all_creds = []
    for rp in rps:
        rp_hash = rp.get(CM.RESULT.RP_ID_HASH) or rp.get("rp", {}).get("idHash")
        if rp_hash is None:
            continue
        for cred in cred_mgmt.enumerate_creds(rp_hash):
            all_creds.append(cred)
    # Find the credential by ID
    cred = None
    for c in all_creds:
        cid_obj = c.get("credentialId") or c.get(CM.RESULT.CREDENTIAL_ID)
        if isinstance(cid_obj, (bytes, bytearray)):
            cid_comp = bytes(cid_obj)
        elif isinstance(cid_obj, dict):
            cid_comp = cid_obj.get("id") or cid_obj.get("rawId")
        else:
            cid_comp = None
        if cid_comp == cred_id:
            cred = c
            break
    if not cred:
        raise RuntimeError("Credential ID not found among resident credentials.")
    large_blob_key = cred.get("largeBlobKey") or cred.get(CM.RESULT.LARGE_BLOB_KEY)
    if large_blob_key is None:
        raise RuntimeError("Selected credential does not have a largeBlobKey.")
    return cred, large_blob_key, ctap2, pin_proto, pin_token


def write_blob(cred_id: bytes, blob: bytes, pin: Optional[str] = None):
    """
    Write the given blob to the YubiKey's large-blob storage for the specified credential.
    Args:
        cred_id: Credential ID as bytes
        blob: Data to write (bytes)
        pin: Optional PIN (if not provided, will prompt)
    """
    _, large_blob_key, ctap2, pin_proto, pin_token = get_credential_and_largeblobkey(cred_id, pin)
    lb = LargeBlobs(ctap2, pin_proto, pin_token)
    lb.put_blob(large_blob_key, blob)


def read_blob(cred_id: bytes, pin: Optional[str] = None) -> bytes:
    """
    Read the blob from the YubiKey's large-blob storage for the specified credential.
    Args:
        cred_id: Credential ID as bytes
        pin: Optional PIN (if not provided, will prompt)
    Returns:
        blob (bytes)
    """
    _, large_blob_key, ctap2, pin_proto, pin_token = get_credential_and_largeblobkey(cred_id, pin)
    lb = LargeBlobs(ctap2, pin_proto, pin_token)
    return lb.get_blob(large_blob_key) 