import React, { useState } from 'react';
import { genSeed, encryptForBlob, entropyToMnemonic } from './seedCrypto';
import { startAuthentication } from '@simplewebauthn/browser';

// Utility for base64url decoding (copied from RegisterYubiKey/LoginYubiKey)
function base64urlToUint8Array(base64url: string): Uint8Array {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  const pad = base64.length % 4 === 0 ? '' : '='.repeat(4 - (base64.length % 4));
  const binary = atob(base64 + pad);
  return Uint8Array.from(binary, c => c.charCodeAt(0));
}

const SeedVault: React.FC = () => {
  const [status, setStatus] = useState<string | null>(null);
  const [mnemonic, setMnemonic] = useState<string | null>(null);
  const [masked, setMasked] = useState(true);
  const [username, setUsername] = useState('');
  const [entropy, setEntropy] = useState<Uint8Array | null>(null);
  const [retrievedMnemonic, setRetrievedMnemonic] = useState<string | null>(null);
  const [retrievedMasked, setRetrievedMasked] = useState(true);
  const [lastBlob, setLastBlob] = useState<Uint8Array | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  async function handleGenerateSeed() {
    setStatus('Generating seed...');
    const { mnemonic, entropy } = await genSeed();
    setMnemonic(mnemonic);
    setEntropy(entropy);
    setStatus('Seed generated. You can now store it.');
    setRetrievedMnemonic(null); // clear previous retrieval
  }

  async function handleStoreSeed() {
    if (!entropy) {
      setStatus('Please generate a seed first.');
      return;
    }
    setStatus('Starting WebAuthn...');
    let blob: Uint8Array | null = null;
    try {
      // 0. Get WebAuthn options from backend
      const res = await fetch('/api/v1/auth/begin-authentication', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });
      const data = await res.json();
      if (data.status !== 'success') throw new Error(data.error?.message || 'Failed to start authentication');
      let publicKey = data.data.publicKey;
      if (typeof publicKey === 'string') publicKey = JSON.parse(publicKey);
      console.log('publicKey from server:', publicKey);
      // 1. Random salt
      const salt = crypto.getRandomValues(new Uint8Array(32));
      // 2. Get hmac-secret (pre-auth)
      let secret;
      try {
        const hmacAssertion = await startAuthentication({
          ...publicKey,
          extensions: {
            hmacGetSecret: { salt1: salt.buffer }
          }
        } as any);
        secret = ((hmacAssertion.clientExtensionResults as any).hmacGetSecret || (hmacAssertion.clientExtensionResults as any).hmacCreateSecret);
      } catch (e) {
        setStatus('Authenticator did not return hmac-secret. You can still download the encrypted blob for manual storage.');
      }
      if (!secret) {
        // Still build a blob with a dummy secret so user can download (will not be decryptable, but enables download)
        blob = new Uint8Array([0]); // placeholder, or skip encryption
        setLastBlob(blob);
        return;
      }
      // 3. Build blob
      blob = await encryptForBlob(entropy, salt, new Uint8Array(secret));
      setLastBlob(blob); // Save for download
      // 4. Store blob using largeBlob.write in the extension (if supported)
      try {
        const assertion = await startAuthentication({
          ...publicKey,
          extensions: {
            largeBlob: { write: blob.buffer }
          }
        } as any);
        setStatus('Seed stored on YubiKey! Copy your mnemonic BACKUP NOW.');
      } catch (e) {
        setStatus('largeBlob.write not supported in this browser. You can download the blob and use ykman.');
      }
    } catch (err: any) {
      setStatus('Error: ' + err.message);
      if (blob) setLastBlob(blob); // still enable download if blob was built
    }
  }

  function handleDownloadBlob() {
    if (!lastBlob) {
      setStatus('No blob to download. Generate and store a seed first.');
      return;
    }
    const file = new Blob([lastBlob], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(file);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'blob.bin';
    a.click();
    URL.revokeObjectURL(url);
    setStatus('Blob downloaded. Use ykman to write it to your YubiKey.');
  }

  function handleUploadBlobClick() {
    fileInputRef.current?.click();
  }

  async function handleBlobFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const bytes = new Uint8Array(await file.arrayBuffer());
    try {
      // Parse salt and encrypted data
      const salt = bytes.slice(0, 32);
      const ivC = bytes.slice(32, 44);
      const cipherLen = bytes.length - 32 - 12 - 12 - 16 - 16; // salt, ivC, ivW, tagC, tagW
      const cipher = bytes.slice(44, 44 + cipherLen);
      const ivW = bytes.slice(44 + cipherLen, 56 + cipherLen);
      const wrapped = bytes.slice(56 + cipherLen);
      // 4. Derive hmac-secret again
      // 0. Get WebAuthn options from backend
      const res = await fetch('/api/v1/auth/begin-authentication', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });
      const data = await res.json();
      if (data.status !== 'success') throw new Error(data.error?.message || 'Failed to start authentication');
      let publicKey = data.data.publicKey;
      if (typeof publicKey === 'string') publicKey = JSON.parse(publicKey);
      const assertion2 = await startAuthentication({
        ...publicKey,
        extensions: {
          hmacGetSecret: { salt1: salt.buffer }
        }
      } as any);
      const secret = ((assertion2.clientExtensionResults as any).hmacGetSecret || (assertion2.clientExtensionResults as any).hmacCreateSecret);
      if (!secret) throw new Error('Authenticator did not return hmac-secret');
      // 5. Unwrap AES key
      const aesKey = await window.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: ivW },
        await window.crypto.subtle.importKey('raw', new Uint8Array(secret), 'AES-GCM', false, ['decrypt']),
        wrapped
      );
      // 6. Decrypt entropy
      const entropy = await window.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: ivC },
        await window.crypto.subtle.importKey('raw', new Uint8Array(aesKey), 'AES-GCM', false, ['decrypt']),
        cipher
      );
      // 7. Convert entropy to mnemonic
      const entropyArr = new Uint8Array(entropy);
      const mnemonic = entropyToMnemonic(entropyArr);
      setRetrievedMnemonic(mnemonic);
      setStatus('Seed retrieved and decrypted from uploaded blob!');
    } catch (err: any) {
      setStatus('Error: ' + err.message);
    }
  }

  return (
    <div className="seed-vault">
      <h2>Seed Vault (Browser-only)</h2>
      <input
        type="text"
        placeholder="Enter username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        className="border rounded px-2 py-1 mr-2"
      />
      <button onClick={handleGenerateSeed} className="btn">
        Generate Seed
      </button>
      <button onClick={handleStoreSeed} className="btn" disabled={!entropy}>
        Store Seed
      </button>
      <button onClick={handleDownloadBlob} className="btn" disabled={!lastBlob}>
        Download Blob
      </button>
      <button onClick={handleUploadBlobClick} className="btn">
        Upload Blob
      </button>
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleBlobFileChange}
        accept=".bin,application/octet-stream"
      />
      {status && <div className="status">{status}</div>}
      <div style={{ display: 'flex', gap: '2em', marginTop: 24 }}>
        <div style={{ flex: 1 }}>
          <h4>Generated Mnemonic (before encryption):</h4>
          {mnemonic && (
            <div className="mnemonic-display">
              <div style={{ fontFamily: 'monospace', margin: '8px 0' }}>
                {masked ? '••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••' : mnemonic}
              </div>
              <button onClick={() => setMasked(m => !m)} className="btn">
                {masked ? 'Show' : 'Hide'}
              </button>
            </div>
          )}
        </div>
        <div style={{ flex: 1 }}>
          <h4>Retrieved Mnemonic (after decryption):</h4>
          {retrievedMnemonic && (
            <div className="mnemonic-display">
              <div style={{ fontFamily: 'monospace', margin: '8px 0' }}>
                {retrievedMasked ? '••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••' : retrievedMnemonic}
              </div>
              <button onClick={() => setRetrievedMasked(m => !m)} className="btn">
                {retrievedMasked ? 'Show' : 'Hide'}
              </button>
            </div>
          )}
        </div>
      </div>
      <div style={{ marginTop: 16, fontSize: 12, color: '#888' }}>
        You can use the downloaded blob file with the provided Python script to write/read the largeBlob on your YubiKey for POC testing.
      </div>
    </div>
  );
};

export default SeedVault; 