import os
from typing import Tuple
from mnemonic import Mnemonic
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import json


def gen_mnemonic(strength: int = 256) -> Tuple[str, bytes]:
    """
    Generate a BIP39 mnemonic and its entropy.
    Args:
        strength: Entropy strength in bits (default 256 for 24 words)
    Returns:
        mnemonic (str), entropy (bytes)
    """
    words = Mnemonic('english')
    ent = os.urandom(strength // 8)
    return words.to_mnemonic(ent), ent


def encrypt_seed(entropy: bytes, secret: bytes, salt: bytes) -> bytes:
    """
    Encrypt the entropy with a random AES key, then wrap the key with the YubiKey-derived secret.
    Args:
        entropy: The BIP39 entropy bytes
        secret: The hmac-secret derived from YubiKey (32 bytes)
        salt: The salt used for hmac-secret derivation (32 bytes)
    Returns:
        blob (bytes): JSON-encoded dict with all encryption fields
    """
    aes_key = os.urandom(32)
    aes = AESGCM(aes_key)
    nonce_c = os.urandom(12)
    cipher = aes.encrypt(nonce_c, entropy, None)

    nonce_w = os.urandom(12)
    wrap = AESGCM(secret).encrypt(nonce_w, aes_key, None)

    blob = json.dumps({
        "salt": salt.hex(),
        "nonceC": nonce_c.hex(), "tagC": cipher[-16:].hex(), "C": cipher[:-16].hex(),
        "nonceW": nonce_w.hex(), "tagW": wrap[-16:].hex(), "W": wrap[:-16].hex()
    }).encode()
    return blob


def decrypt_seed(blob: bytes, secret: bytes) -> bytes:
    """
    Decrypt the blob to recover the original entropy, given the YubiKey-derived secret.
    Args:
        blob: The JSON-encoded blob as bytes
        secret: The hmac-secret derived from YubiKey (32 bytes)
    Returns:
        entropy (bytes)
    """
    data = json.loads(blob)
    nonce_c = bytes.fromhex(data["nonceC"])
    cipher = bytes.fromhex(data["C"]) + bytes.fromhex(data["tagC"])
    nonce_w = bytes.fromhex(data["nonceW"])
    wrap = bytes.fromhex(data["W"]) + bytes.fromhex(data["tagW"])

    # Unwrap AES key
    aes_key = AESGCM(secret).decrypt(nonce_w, wrap, None)
    # Decrypt entropy
    entropy = AESGCM(aes_key).decrypt(nonce_c, cipher, None)
    return entropy 