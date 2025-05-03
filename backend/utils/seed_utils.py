from mnemonic import Mnemonic
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, json
from backend.utils.yk_blob import derive_hmac_secret_from_yk

def gen_mnemonic(strength=256):
    words = Mnemonic('english')
    ent   = os.urandom(strength // 8)
    return words.to_mnemonic(ent), ent

def encrypt_seed(username: str, entropy: bytes):
    aes_key = os.urandom(32)
    aes     = AESGCM(aes_key)
    nonce_c = os.urandom(12)
    cipher  = aes.encrypt(nonce_c, entropy, None)

    salt    = os.urandom(32)
    secret  = derive_hmac_secret_from_yk(username, salt)   # wrapper in yk_blob.py
    nonce_w = os.urandom(12)
    wrap    = AESGCM(secret).encrypt(nonce_w, aes_key, None)

    blob = json.dumps({
        "salt": salt.hex(),
        "nonceC": nonce_c.hex(), "tagC": cipher[-16:].hex(), "C": cipher[:-16].hex(),
        "nonceW": nonce_w.hex(), "tagW": wrap[-16:].hex(), "W": wrap[:-16].hex()
    }).encode()
    return blob

def decrypt_blob(username: str, blob: bytes) -> bytes:
    d = json.loads(blob)
    salt = bytes.fromhex(d["salt"])
    nonce_c = bytes.fromhex(d["nonceC"])
    tag_c = bytes.fromhex(d["tagC"])
    C = bytes.fromhex(d["C"])
    nonce_w = bytes.fromhex(d["nonceW"])
    tag_w = bytes.fromhex(d["tagW"])
    W = bytes.fromhex(d["W"])

    secret = derive_hmac_secret_from_yk(username, salt)
    aesgcm_wrap = AESGCM(secret)
    aes_key = aesgcm_wrap.decrypt(nonce_w, W + tag_w, None)
    aesgcm = AESGCM(aes_key)
    entropy = aesgcm.decrypt(nonce_c, C + tag_c, None)
    return entropy

def entropy_to_mnemonic(entropy: bytes) -> str:
    words = Mnemonic('english')
    return words.to_mnemonic(entropy) 