import pytest
from backend.utils import seed_utils, yk_blob
from mnemonic import Mnemonic


def test_seed_roundtrip():
    """
    Full round-trip test: generate mnemonic, encrypt, write to YubiKey, read back, decrypt, and verify.
    Requires a real YubiKey with a resident credential and PIN.
    """
    # Prompt for credential ID (hex) and PIN
    cred_id_hex = input("Enter credential ID (hex): ").strip()
    cred_id = bytes.fromhex(cred_id_hex)
    pin = input("Enter YubiKey PIN: ").strip()

    # 1. Generate mnemonic and entropy
    mnemonic_str, entropy = seed_utils.gen_mnemonic(256)
    print(f"Generated mnemonic: {mnemonic_str}")

    # 2. Generate random salt
    import os
    salt = os.urandom(32)
    print(f"Salt (hex): {salt.hex()}")

    # 3. Derive hmac-secret from YubiKey (simulate: for real use, this would be via WebAuthn extension)
    # For this test, we'll just use a random 32-byte secret as a stand-in
    # In a real integration, you would use the browser or python-fido2 to get the hmac-secret
    secret = os.urandom(32)
    print(f"(Simulated) hmac-secret (hex): {secret.hex()}")

    # 4. Encrypt the entropy
    blob = seed_utils.encrypt_seed(entropy, secret, salt)
    print(f"Encrypted blob (hex): {blob.hex()}")

    # 5. Write blob to YubiKey
    yk_blob.write_blob(cred_id, blob, pin)
    print("Blob written to YubiKey large-blob storage.")

    # 6. Read blob back from YubiKey
    blob2 = yk_blob.read_blob(cred_id, pin)
    print(f"Read blob (hex): {blob2.hex()}")

    # 7. Decrypt the blob
    entropy2 = seed_utils.decrypt_seed(blob2, secret)
    assert entropy2 == entropy, "Decrypted entropy does not match original!"
    print("Decrypted entropy matches original.")

    # 8. Convert entropy back to mnemonic
    words = Mnemonic('english')
    mnemonic2 = words.to_mnemonic(entropy2)
    assert mnemonic2 == mnemonic_str, "Recovered mnemonic does not match!"
    print(f"Recovered mnemonic: {mnemonic2}")
    print("Recovered mnemonic matches original.") 