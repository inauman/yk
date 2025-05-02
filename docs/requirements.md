# Project Requirements & Use Case

## Project Goals
- **Demonstrate Secure Bitcoin Seed Storage**: Use YubiKeys (via WebAuthn) to secure a Bitcoin seed phrase.
- **Simplify User Experience**: Provide a guided, wizard-style flow that is more user-friendly than traditional hardware wallets.
- **Establish Modular Architecture**: Clearly separate backend and frontend concerns with well-defined API contracts.

## Technology Stack
- **Backend**: Python Flask application, SQLite database, HTTPS (self-signed for local testing)
- **Frontend**: React with TypeScript, Tailwind CSS, Axios for API communication
- **Security**: WebAuthn for hardware-backed authentication, AES-256-GCM for encryption, and proper session management

## Use Case
- **2-of-3 Multisig Setup**: 
  - A user can secure their Bitcoin seed using a combination of YubiKeys and an app key.
  - The seed is encrypted so that any two of the three registered keys (or combinations such as 1 YubiKey + 1 hardware wallet) can decrypt it.
  - This design offers a balance between security and usability, making it easier for new users to protect their assets.

[Back to README](../README.md) 