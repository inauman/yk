import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import RegisterYubiKey from './RegisterYubiKey'
import LoginYubiKey from './LoginYubiKey'

function App() {
  // Simple navigation state for demo
  const [page, setPage] = useState<'home' | 'register' | 'login'>('home')

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>YubiKey WebAuthn Demo</h1>
      <div className="card">
        <button onClick={() => setPage('register')}>Register YubiKey</button>
        <button onClick={() => setPage('login')} style={{ marginLeft: '1em' }}>Login with YubiKey</button>
      </div>
      <div className="card">
        {page === 'register' && <RegisterYubiKey />}
        {page === 'login' && <LoginYubiKey />}
        {page === 'home' && <p>Select an action above to begin.</p>}
      </div>
    </>
  )
}

export default App
