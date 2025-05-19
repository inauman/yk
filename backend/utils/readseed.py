import seed_utils
from mnemonic import Mnemonic

# 1. Read the blob from file
with open("1blob.bin", "rb") as f:
    blob = f.read()

# 2. Enter the secret (must be the same 32 bytes used for encryption)
import os
secret_hex = input("Enter the 32-byte secret (hex, as printed in your test): ").strip()
secret = bytes.fromhex(secret_hex)

# 3. Decrypt the blob to get entropy
entropy = seed_utils.decrypt_seed(blob, secret)

# 4. Convert entropy to mnemonic
mnemo = Mnemonic("english")
mnemonic_words = mnemo.to_mnemonic(entropy)
print("Recovered mnemonic:", mnemonic_words)