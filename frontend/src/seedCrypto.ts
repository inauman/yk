import { generateMnemonic, entropyToMnemonic as scureEntropyToMnemonic, mnemonicToEntropy } from '@scure/bip39';
import { wordlist } from '@scure/bip39/wordlists/english';

function uint8ToHex(uint8: Uint8Array): string {
  return Array.from(uint8).map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function genSeed(): Promise<{mnemonic: string, entropy: Uint8Array}> {
  const entropy = crypto.getRandomValues(new Uint8Array(32)); // 256-bit
  const mnemonic = scureEntropyToMnemonic(entropy, wordlist);
  return { mnemonic, entropy };
}

export function entropyToMnemonic(entropy: Uint8Array): string {
  return scureEntropyToMnemonic(entropy, wordlist);
}

export async function encryptForBlob(entropy: Uint8Array, salt: Uint8Array, secret: Uint8Array) {
  // 1. random AES-256 key
  const aesKey = crypto.getRandomValues(new Uint8Array(32));

  // 2. C ← AES-GCM(entropy, K)
  const ivC = crypto.getRandomValues(new Uint8Array(12));
  const cipher = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: ivC },
    await crypto.subtle.importKey("raw", aesKey, "AES-GCM", false, ["encrypt"]),
    entropy
  );

  // 3. wrap K with secret (derived from hmac-secret)
  const ivW = crypto.getRandomValues(new Uint8Array(12));
  const wrapped = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: ivW },
    await crypto.subtle.importKey("raw", secret, "AES-GCM", false, ["encrypt"]),
    aesKey
  );

  return new Uint8Array([
    ...salt, ...ivC, ...new Uint8Array(cipher), ...ivW, ...new Uint8Array(wrapped)
  ]);
} 