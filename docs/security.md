# Security Considerations & Recommendations

## Current Security Measures
- **WebAuthn Authentication**: Ensures that only the registered YubiKey can authenticate.
- **Seed Protection**: BIP39 seed phrases are generated with secure entropy and are displayed only momentarily.
- **Transport Security**: All interactions occur over HTTPS.
- **Memory Handling**: Sensitive data is cleared from memory after a timeout.

## Limitations & Areas for Improvement
- **Encryption**:  
  - The current implementation uses simplified encoding.  
  - Upcoming improvements (MVP2) will implement AES-256-GCM with proper key derivation (HKDF-SHA256).
- **Key Management**:  
  - Support for multiple YubiKeys and credential revocation is planned.
- **Storage**:  
  - Although data is now stored in a SQLite database, additional measures (such as database encryption) are recommended for production.
- **Session Management**:  
  - Enhanced session handling (timeouts, rate limiting) is needed.

## Best Practices
- Keep your YubiKey physically secure.
- Use HTTPS at all times, even in development (self-signed certificates are acceptable locally).
- Regularly update and audit your dependencies.
- Follow secure coding practices as outlined in the developer guide.

[Back to README](../README.md) 