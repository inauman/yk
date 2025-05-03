import React, { useState } from 'react';
import { storeSeed, retrieveSeed } from './api';

const SeedVault: React.FC = () => {
  const [status, setStatus] = useState<string | null>(null);
  const [mnemonic, setMnemonic] = useState<string | null>(null);
  const [masked, setMasked] = useState(true);
  const [seedStored, setSeedStored] = useState(false);

  const handleStoreSeed = async () => {
    setStatus('Storing seed...');
    const res = await storeSeed();
    if (res.status === 'success') {
      setStatus('Seed generated and stored successfully!');
      setSeedStored(true);
    } else {
      setStatus('Error: ' + (res.error || res.message));
    }
  };

  const handleRetrieveSeed = async () => {
    setStatus('Retrieving seed...');
    const res = await retrieveSeed();
    if (res.status === 'success') {
      setMnemonic(res.mnemonic);
      setStatus('Seed retrieved!');
    } else {
      setStatus('Error: ' + (res.error || res.message));
    }
  };

  return (
    <div className="seed-vault">
      <h2>Seed Vault</h2>
      <button onClick={handleStoreSeed} disabled={seedStored} className="btn">
        Generate & Store Seed
      </button>
      <button onClick={handleRetrieveSeed} className="btn">
        Retrieve Seed
      </button>
      {status && <div className="status">{status}</div>}
      {mnemonic && (
        <div className="mnemonic-display">
          <label>Mnemonic:</label>
          <div style={{ fontFamily: 'monospace', margin: '8px 0' }}>
            {masked ? '••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••' : mnemonic}
          </div>
          <button onClick={() => setMasked(m => !m)} className="btn">
            {masked ? 'Show' : 'Hide'}
          </button>
        </div>
      )}
      <div style={{ marginTop: 16, fontSize: 12, color: '#888' }}>
        Works in Chrome 123+ or with Yubico Manager fallback.
      </div>
    </div>
  );
};

export default SeedVault; 