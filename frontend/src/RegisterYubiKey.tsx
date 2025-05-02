import { useState } from 'react';

function base64urlToUint8Array(base64url: string): Uint8Array {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  const pad = base64.length % 4 === 0 ? '' : '='.repeat(4 - (base64.length % 4));
  const binary = atob(base64 + pad);
  return Uint8Array.from(binary, c => c.charCodeAt(0));
}

function bufferToBase64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function serializeCredential(cred: any) {
  return {
    id: cred.id,
    rawId: bufferToBase64url(cred.rawId),
    type: cred.type,
    response: {
      clientDataJSON: bufferToBase64url(cred.response.clientDataJSON),
      attestationObject: bufferToBase64url(cred.response.attestationObject),
    },
    ...(cred.getClientExtensionResults && Object.keys(cred.getClientExtensionResults()).length > 0
      ? { clientExtensionResults: cred.getClientExtensionResults() }
      : {}),
  };
}

const RegisterYubiKey = () => {
  const [username, setUsername] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  const handleRegister = async () => {
    setStatus('Starting registration...');
    try {
      // 1. Begin registration (get options from backend)
      const res = await fetch('/api/v1/auth/begin-registration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, displayName: username }),
      });
      const data = await res.json();
      if (data.status !== 'success') throw new Error(data.error?.message || 'Failed to start registration');
      let publicKey = data.data.publicKey;
      if (typeof publicKey === 'string') {
        publicKey = JSON.parse(publicKey);
      }
      console.log('publicKey from backend:', publicKey);

      // Defensive checks for required fields
      if (!publicKey) throw new Error('Missing publicKey from backend');
      if (!publicKey.challenge) throw new Error('Missing challenge from backend');
      if (!publicKey.user || !publicKey.user.id) throw new Error('Missing user.id from backend');
      if (typeof publicKey.challenge !== 'string') throw new Error('Challenge must be a base64url string');
      if (typeof publicKey.user.id !== 'string') throw new Error('user.id must be a base64url string');

      // Decode required fields
      publicKey.challenge = base64urlToUint8Array(publicKey.challenge);
      publicKey.user.id = base64urlToUint8Array(publicKey.user.id);
      if (publicKey.excludeCredentials) {
        publicKey.excludeCredentials = publicKey.excludeCredentials.map((cred: any) => {
          if (!cred.id || typeof cred.id !== 'string') throw new Error('excludeCredentials[].id must be a base64url string');
          return {
            ...cred,
            id: base64urlToUint8Array(cred.id),
          };
        });
      }

      // Ensure parameter names match WebAuthn spec
      // https://www.w3.org/TR/webauthn-2/#dictdef-publickeycredentialcreationoptions
      // Required: challenge, rp, user, pubKeyCredParams
      // Optional: timeout, excludeCredentials, authenticatorSelection, attestation, extensions
      // user: id, name, displayName
      if (!publicKey.rp || !publicKey.rp.name || !publicKey.rp.id) throw new Error('Missing rp, rp.name, or rp.id from backend');
      if (!publicKey.user.name || !publicKey.user.displayName) throw new Error('Missing user.name or user.displayName from backend');
      if (!Array.isArray(publicKey.pubKeyCredParams)) throw new Error('Missing pubKeyCredParams from backend');

      // 2. Call WebAuthn API
      // @ts-ignore
      const cred = await window.navigator.credentials.create({ publicKey });
      const serializedCred = serializeCredential(cred);
      console.log('Serialized credential sent to backend:', serializedCred);
      console.log('Payload sent to backend:', { credential: serializedCred, username });
      // 3. Complete registration (send attestation to backend, include username at top level)
      const completeRes = await fetch('/api/v1/auth/complete-registration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...serializedCred, username }),
      });
      const completeData = await completeRes.json();
      if (completeData.status !== 'success') throw new Error(completeData.error?.message || 'Failed to complete registration');
      setUserId(completeData.data.credentialId);
      setStatus('Registration successful! Your User ID: ' + completeData.data.credentialId);
    } catch (err: any) {
      setStatus('Registration failed: ' + err.message);
    }
  };

  return (
    <div>
      <h2>Register YubiKey</h2>
      <input
        type="text"
        placeholder="Enter username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        className="border rounded px-2 py-1 mr-2"
      />
      <button onClick={handleRegister} className="bg-blue-600 text-white px-4 py-1 rounded">Register</button>
      {status && <p className="mt-2">{status}</p>}
      {userId && <p className="mt-2 font-mono">User ID: {userId}</p>}
    </div>
  );
};

export default RegisterYubiKey; 