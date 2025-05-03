# Project Plan & Task Tracking

> **Note**: All task statuses are reset for the new project.
> **Last updated: 05/02/2025**

## Milestones & Tasks

### Phase 1: YubiKey Registration & Authentication
- [x] Set up persistent SQLite database for user, credential, and challenge storage (replace in-memory storage)
- [x] Verify YubiKey recognition and WebAuthn capabilities
- [x] Implement backend API endpoints for YubiKey registration and authentication (/auth/begin-registration, /auth/complete-registration, /auth/begin-authentication, /auth/complete-authentication)
- [x] Implement client-side registration and authentication flows in React
- [x] Test YubiKey registration and authentication (unit/integration)

### Phase 2a: Large-Blob Seed POC (Single YubiKey, No Multisig)
- [ ] **Backend**
  - [ ] Add dependencies: `python-bitcointx` (BIP39), `cryptography`, `fido2`
  - [ ] Utility module `seed_utils.py`:
    - [ ] `gen_mnemonic(strength=256) -> (mnemonic, entropy)`
    - [ ] `encrypt_seed(entropy) -> (blob_dict, printable_mnemonic)`
  - [ ] Large-Blob helpers `yk_blob.py`:
    - [ ] `write_blob(cred_id: bytes, blob: bytes)`
    - [ ] `read_blob(cred_id) -> bytes`
  - [ ] New routes:
    - [ ] `POST /api/v1/seed/store` (generate, encrypt, write blob)
    - [ ] `GET /api/v1/seed/retrieve` (read blob, decrypt, return mnemonic)
  - [ ] Auth guard: require valid WebAuthn assertion with `largeBlob` and `hmacCreateSecret` extensions
  - [ ] Unit tests: use `fido2.ctap2.virtual.Device` to simulate sign-in + blob write/read round-trip
- [ ] **Frontend**
  - [ ] Extend `api.ts` with `storeSeed()` and `retrieveSeed()`
  - [ ] Minimal page `SeedVault.tsx`:
    - [ ] "Generate & Store Seed" button (calls `/seed/store`, shows masked mnemonic)
    - [ ] "Retrieve Seed" button (calls `/seed/retrieve`, shows mnemonic)
    - [ ] Use `@simplewebauthn/browser` with `extensions: { hmacCreateSecret: true, largeBlob: { read: true, write: true } }`
    - [ ] Add note: "Works in Chrome 123+ or with Yubico Manager fallback."

### (Legacy/Future) - Multisig, Shamir, Server-side Storage (DEPRECATED for POC)
- [ ] (No longer in scope for this POC; see chatgpt-yk-clean-arch.md for details)

### Phase 3+: (For future expansion, keep for reference)
- [ ] Seed Encryption & Storage (envelope encryption, HKDF, etc.)
- [ ] Seed Retrieval & Decryption
- [ ] YubiKey Management
- [ ] User Interface (Wizard Flow)
- [ ] Security & Session Management
- [ ] Integration Testing & Validation
- [ ] Documentation & Developer Guides

[Back to README](../README.md) 