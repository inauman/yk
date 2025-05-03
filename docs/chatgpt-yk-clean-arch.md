Here’s a **copy-and-paste task brief for Cursor** that replaces the old “multi-YubiKey multisig” idea with a **minimal Large-Blob POC**.

---

## 🔄 Scope delta (read this first)

* **Keep** the existing WebAuthn **registration / authentication** workflow (already merged).  
* **New** work = **seed → encrypt → Large-Blob write/read → decrypt → print**.  
* **No** multisig, no Shamir, no server-side seed storage.

---

## 0. High-level flow

```text
┌──────────────┐    WebAuthn sign-in (already done)
│  Front-end   │───/api/v1/auth/*─────────────────────────────┐
└──────────────┘                                              │
         │                                                    ▼
         │        1. POST /api/v1/seed/store
         ▼
┌──────────────────────────────────────────────────────────────┐
│        ② backend generates 24-word BIP39 seed               │
│        ③ K ← random 32-byte AES key                         │
│        ④ C ← AES-256-GCM_encrypt(seed, K)                   │
│        ⑤ S ← YubiKey hmac-secret(salt)  (user touch)        │
│        ⑥ W ← AES-256-GCM_encrypt(K, S)  (wrap key)          │
│        ⑦ blob = {salt, nonceC, tagC, C, nonceW, tagW, W}    │
│        ⑧ largeBlobWrite(credId, blob)                       │
└──────────────────────────────────────────────────────────────┘
         │
         │        2. GET /api/v1/seed/retrieve
         ▼
┌──────────────────────────────────────────────────────────────┐
│        get blob → derive same S → decrypt W → get K →       │
│        decrypt C → recover seed → return 24-word mnemonic   │
└──────────────────────────────────────────────────────────────┘
```

---

## 1. Back-end tasks  (Python / Flask)

| # | Task | Hints |
|---|------|-------|
| 1 | **Add deps**: `python-bitcointx` (BIP39), `cryptography`, `fido2`. | pip/uv in `backend/requirements.txt`. |
| 2 | **Utility** `seed_utils.py`<br>• `gen_mnemonic(strength=256) -> (mnemonic, entropy)`<br>• `encrypt_seed(entropy) -> (blob_dict, printable_mnemonic)` | Use `AESGCM` from `cryptography.hazmat.primitives.ciphers.aead`. |
| 3 | **Large-Blob helpers** `yk_blob.py`<br>• `write_blob(cred_id: bytes, blob: bytes)`<br>• `read_blob(cred_id) -> bytes` | Wrap Yubico python-`fido2` high-level API. Accept environment var `YKMAN_CLI_FALLBACK=1` to shell out to `ykman fido2 cred write-large-blob …` if browser write support is missing. |
| 4 | **New routes**<br>• `POST /api/v1/seed/store`  → calls 1-8 above.<br>• `GET  /api/v1/seed/retrieve` → returns JSON `{ mnemonic: "…" }` | Expect `username` in JSON body/query to look up `credential_id`. |
| 5 | **Auth guard**: both routes require a valid WebAuthn assertion **with** `extensions: { largeBlob: { read|write: true }, hmacCreateSecret: true }`. | Already have `webauthn_service`; just extend option structs & verification. |
| 6 | **Unit tests** (`backend/tests/test_seed.py`)<br>Use `fido2.ctap2.virtual.Device` to simulate sign-in + blob write/read round-trip. | Reference FIDO2 python docs. |

---

## 2. Front-end tasks  (React / TypeScript)

| # | Task | Hints |
|---|------|-------|
| 1 | Extend existing `api.ts` with `storeSeed()` and `retrieveSeed()`. | Simple `fetch` wrappers. |
| 2 | Minimal page **SeedVault.tsx**<br>• “Generate & Store Seed” button → hits `/seed/store`, shows success + masked mnemonic.<br>• “Retrieve Seed” button → hits `/seed/retrieve`, shows mnemonic in an alert. | Use `@simplewebauthn/browser` with: <br>`extensions: { hmacCreateSecret: true, largeBlob: { read: true, write: true } }`. |
| 3 | Add a note: “Works in Chrome 123+ or with Yubico Manager fallback.” | Tool-tip in UI. |

---

## 3. Project-plan update (docs/project_plan.md)

* Mark Phase 1 done.  
* Add **Phase 2a: Large-Blob seed POC** with check-boxes for tasks above.

---

## 4. Out-of-scope / Do NOT implement

* Any m-of-n multisig logic, descriptors, PSBT fan-out, Shamir, or Taproot.  
* Server-side seed storage.  
* Backup-key cloning workflow (future story).

---

## 5. Reference snippets (can embed in code)

```python
# seed_utils.py
from bitcointx import mnemonic
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, json

def gen_mnemonic(strength=256):
    words = mnemonic.Mnemonic('english')
    ent   = os.urandom(strength // 8)
    return words.to_mnemonic(ent), ent

def encrypt_seed(entropy: bytes):
    aes_key = os.urandom(32)
    aes     = AESGCM(aes_key)
    nonce_c = os.urandom(12)
    cipher  = aes.encrypt(nonce_c, entropy, None)

    salt    = os.urandom(32)
    secret  = derive_hmac_secret_from_yk(salt)   # wrapper in yk_blob.py
    nonce_w = os.urandom(12)
    wrap    = AESGCM(secret).encrypt(nonce_w, aes_key, None)

    blob = json.dumps({
        "salt": salt.hex(),
        "nonceC": nonce_c.hex(), "tagC": cipher[-16:].hex(), "C": cipher[:-16].hex(),
        "nonceW": nonce_w.hex(), "tagW": wrap[-16:].hex(), "W": wrap[:-16].hex()
    }).encode()
    return blob
```

*(Cursor can refactor, but the structure must stay roughly the same.)*

---

**Hand this brief to Cursor and delete the old multisig tasks.**  
When it finishes you’ll have a one-YubiKey Large-Blob seed vault you can demo end-to-end. 😊