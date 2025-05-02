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

function serializeAssertion(assertion: any) {
  return {
    id: assertion.id,
    rawId: bufferToBase64url(assertion.rawId),
    type: assertion.type,
    response: {
      clientDataJSON: bufferToBase64url(assertion.response.clientDataJSON),
      authenticatorData: bufferToBase64url(assertion.response.authenticatorData),
      signature: bufferToBase64url(assertion.response.signature),
      userHandle: assertion.response.userHandle ? bufferToBase64url(assertion.response.userHandle) : undefined,
    },
    ...(assertion.getClientExtensionResults && Object.keys(assertion.getClientExtensionResults()).length > 0
      ? { clientExtensionResults: assertion.getClientExtensionResults() }
      : {}),
  };
}

const LoginYubiKey = () => {
  const [username, setUsername] = useState('');
  const [status, setStatus] = useState<string | null>(null);

  const handleLogin = async () => {
    setStatus('Starting authentication...');
    try {
      // 1. Begin authentication (get options from backend)
      const res = await fetch('/api/v1/auth/begin-authentication', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username }),
      });
      const data = await res.json();
      if (data.status !== 'success') throw new Error(data.error?.message || 'Failed to start authentication');
      let publicKey = data.data.publicKey;
      if (typeof publicKey === 'string') {
        publicKey = JSON.parse(publicKey);
      }
      console.log('publicKey from backend:', publicKey);
      console.log('typeof publicKey.challenge:', typeof publicKey.challenge);
      console.log('publicKey.challenge (again):', publicKey.challenge);
      console.log('publicKey.allowCredentials:', publicKey.allowCredentials);
      // Defensive checks for required fields
      if (!publicKey.challenge) throw new Error('Missing challenge from backend');
      if (typeof publicKey.challenge !== 'string') throw new Error('Challenge must be a base64url string');
      console.log('publicKey.challenge:', publicKey.challenge);
      if (publicKey.allowCredentials) {
        publicKey.allowCredentials.forEach((cred: any, idx: number) => {
          if (!cred.id || typeof cred.id !== 'string') throw new Error(`allowCredentials[${idx}].id must be a base64url string`);
        });
      }

      // Decode required fields
      publicKey.challenge = base64urlToUint8Array(publicKey.challenge);
      if (publicKey.allowCredentials) {
        publicKey.allowCredentials = publicKey.allowCredentials.map((cred: any) => ({
          ...cred,
          id: base64urlToUint8Array(cred.id),
        }));
      }

      // Ensure parameter names match WebAuthn spec
      // https://www.w3.org/TR/webauthn-2/#dictdef-publickeycredentialrequestoptions
      // Required: challenge
      // Optional: timeout, rpId, allowCredentials, userVerification, extensions
      if (publicKey.rpId && typeof publicKey.rpId !== 'string') throw new Error('rpId must be a string if present');

      // 2. Call WebAuthn API
      // @ts-ignore
      const assertion = await window.navigator.credentials.get({ publicKey });
      const serializedAssertion = serializeAssertion(assertion);
      // 3. Complete authentication (send assertion to backend)
      const completeRes = await fetch('/api/v1/auth/complete-authentication', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...serializedAssertion, username }),
      });
      const completeData = await completeRes.json();
      if (completeData.status !== 'success') throw new Error(completeData.error?.message || 'Failed to complete authentication');
      setStatus('Authentication successful!');
    } catch (err: any) {
      setStatus('Authentication failed: ' + err.message);
    }
  };

  return (
    <div>
      <h2>Login with YubiKey</h2>
      <input
        type="text"
        placeholder="Enter Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        className="border rounded px-2 py-1 mr-2"
      />
      <button onClick={handleLogin} className="bg-green-600 text-white px-4 py-1 rounded">Login</button>
      {status && <p className="mt-2">{status}</p>}
    </div>
  );
};

export default LoginYubiKey; 