#!/usr/bin/env python3
"""
YubiKey Large-Blob read/write helper script.

Usage:
  python largeblob_tool.py write <credId> <blob.bin>
  python largeblob_tool.py read  <credId>            > blob.bin

Requires:
  pip install python-fido2==1.2.0
  YubiKey firmware ≥ 5.5, and a FIDO2 PIN set.

IMPORTANT IMPLEMENTATION NOTES (2024):

- This script uses the python-fido2 library to read/write large blobs (arbitrary data) to a credential on a YubiKey 5 NFC or similar device.
- The correct way to access large-blob storage is via the LargeBlobs API (fido2.ctap2.blob.LargeBlobs), not via CredentialManagement.
- When requesting a PIN/UV token, you MUST combine permissions:
    ClientPin.PERMISSION.CREDENTIAL_MGMT | ClientPin.PERMISSION.LARGE_BLOB_WRITE
  If you do not, the YubiKey will reject the operation with CTAP error 0x33 (PIN_AUTH_INVALID).
- Credential and RP fields may be returned as either string keys or enum keys, and credential IDs may be bytes or dicts. Always check both.
- All status and prompt messages are routed to stderr, so stdout is reserved for binary blob data. This is critical for correct file output.
- User presence (touch) is not always required for large-blob operations, depending on YubiKey firmware and permissions. The script prompts for touch before write/read, but the device may not require it.
- To debug issues:
    * Check for CTAP error codes (e.g., 0x33 for PIN_AUTH_INVALID)
    * Use shasum/diff to verify round-trip integrity of written/read blobs
    * If you see output contamination, ensure all prints except the blob go to stderr
    * If you see KeyError/AttributeError, check for both string and enum keys, and for bytes/dict credential IDs

For more debugging and codebase navigation tips, see the Cursor Rules in .cursor/rules.
"""
import sys
from binascii import unhexlify
from fido2.hid import CtapHidDevice
from fido2.client import Fido2Client
from fido2.ctap2.base import Ctap2
from fido2.ctap2.pin import ClientPin
from fido2.ctap2 import CredentialManagement
from exampleutils import CliInteraction
from fido2.ctap2 import CredentialManagement as CM
from fido2.ctap2.blob import LargeBlobs
import os
import functools

RP_ID = "localhost"  # must exactly match the RP ID used at registration
log = functools.partial(print, file=sys.stderr)


def pick_credential(creds):
    log("\nResident Credentials on your YubiKey:")
    for idx, cred in enumerate(creds):
        user = cred.get("user") or cred.get(CM.RESULT.USER, {})
        name = user.get("name", "<no name>")
        cid_obj = cred.get("credentialId") or cred.get(CM.RESULT.CREDENTIAL_ID)
        # cid_obj can be raw bytes or a PublicKeyCredentialDescriptor-like dict
        if isinstance(cid_obj, (bytes, bytearray)):
            cid_hex = cid_obj.hex()
            cid_bytes_val = bytes(cid_obj)
        elif isinstance(cid_obj, dict):
            cid_bytes_val = cid_obj.get("id") or cid_obj.get("rawId")
            cid_hex = cid_bytes_val.hex() if isinstance(cid_bytes_val, (bytes, bytearray)) else ""
        else:
            cid_hex = ""
            cid_bytes_val = None
        log(f"  [{idx}] user={name}, cred_id={cid_hex[:16]}…")
    while True:
        sel = input(f"Pick credential [0–{len(creds)-1}]: ")
        if sel.isdigit() and 0 <= (i := int(sel)) < len(creds):
            return creds[i]
        log("Invalid selection.")


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("write", "read"):
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]
    cred_id_hex = sys.argv[2]
    cred_id = unhexlify(cred_id_hex)

    # Find a YubiKey
    dev = next(CtapHidDevice.list_devices(), None)
    if not dev:
        print("No YubiKey found.")
        sys.exit(1)

    origin = f"https://{RP_ID}"
    interaction = CliInteraction()
    client = Fido2Client(dev, origin, user_interaction=interaction)
    log(f"Using RP ID: {RP_ID}")

    # Set up CTAP2 and PIN
    ctap2 = Ctap2(dev)
    client_pin = ClientPin(ctap2)
    pin = interaction.request_pin(None, None)
    combined_perms = (
        ClientPin.PERMISSION.CREDENTIAL_MGMT | ClientPin.PERMISSION.LARGE_BLOB_WRITE
    )
    pin_token = client_pin.get_pin_token(
        pin,
        permissions=combined_perms,
    )
    pin_proto = client_pin.protocol
    cred_mgmt = CredentialManagement(ctap2, pin_proto, pin_token)

    # Enumerate resident RPs & credentials
    try:
        rps = list(cred_mgmt.enumerate_rps())
    except Exception as e:
        log(f"Error enumerating RPs: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    if not rps:
        log("No RPs with resident credentials found.")
        sys.exit(1)

    all_creds = []
    for rp in rps:
        # Access RP ID hash using the RESULT enum key
        try:
            rp_hash = rp[CM.RESULT.RP_ID_HASH]
        except KeyError:
            # Fallback for older library versions that may return string keys
            rp_hash = rp.get("rp", {}).get("idHash")
            if rp_hash is None:
                continue

        for cred in cred_mgmt.enumerate_creds(rp_hash):
            all_creds.append(cred)

    if not all_creds:
        log("No resident credentials found.")
        sys.exit(1)

    # Try to find the credential by ID
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
        log("Credential ID not found among resident credentials. Please select manually.")
        cred = pick_credential(all_creds)
        cid_obj = cred.get("credentialId") or cred.get(CM.RESULT.CREDENTIAL_ID)
        if isinstance(cid_obj, (bytes, bytearray)):
            cred_id = bytes(cid_obj)
        elif isinstance(cid_obj, dict):
            cred_id = cid_obj.get("id") or cid_obj.get("rawId")
        else:
            cred_id = cred_id  # Keep original

    # Extract the largeBlobKey for this credential
    large_blob_key = cred.get("largeBlobKey") or cred.get(CM.RESULT.LARGE_BLOB_KEY)
    if large_blob_key is None:
        log("Selected credential does not have a largeBlobKey. Cannot proceed.")
        sys.exit(1)

    # Set up LargeBlobs helper
    lb = LargeBlobs(ctap2, pin_proto, pin_token)

    # Override prompt_up to write to stderr so it doesn't pollute stdout
    def _prompt_up():
        log("\nTouch your authenticator device now...\n")

    interaction.prompt_up = _prompt_up

    if mode == "write":
        blob_path = sys.argv[3] if len(sys.argv) > 3 else input("Path to blob file: ")
        blob_path = os.path.expanduser(blob_path)
        try:
            with open(blob_path, "rb") as fh:
                data = fh.read()
        except FileNotFoundError:
            log(f"File not found: {blob_path}")
            sys.exit(1)
        except PermissionError:
            log(
                "Permission denied when accessing the blob file. "
                "Ensure the path is correct and that the script has permission to read it."
            )
            sys.exit(1)
        interaction.prompt_up()
        log(f"Writing {len(data)} bytes to large-blob…")
        try:
            lb.put_blob(large_blob_key, data)
            log("Write complete.")
        except Exception as e:
            log(f"Error writing large-blob: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:  # mode == "read"
        interaction.prompt_up()
        log("Reading large-blob…")
        try:
            blob = lb.get_blob(large_blob_key)
            sys.stdout.buffer.write(blob)
        except Exception as e:
            log(f"Error reading large-blob: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
