# Usage Guide & Test Scripts

## Usage Instructions
1. **Testing Your YubiKey**:
   - Use the "Test YubiKey" page to verify that your YubiKey is recognized and works with WebAuthn.
2. **Generating/Importing a Seed**:
   - **Generate**: Click "Generate New Seed" to create a BIP39 seed phrase.
   - **Import**: Select "Import Existing Seed" and enter a valid BIP39 phrase.
3. **Registering a YubiKey**:
   - Enter a username and follow the on-screen prompts to register your YubiKey.
   - Note the generated User ID for future authentication.
4. **Storing a Seed**:
   - Confirm seed details and click "Encrypt and Store with YubiKey."
5. **Retrieving a Seed**:
   - Enter your User ID, authenticate with your YubiKey, and view your seed phrase.
   - The seed is cleared from memory when you log out or after a timeout.

## Test Scenarios
The following consolidated test scenarios cover critical workflows:

### 1. Registration Test
- **Steps**:
  - Initiate registration (enter username, click "Register YubiKey").
  - When prompted, insert and touch your YubiKey.
- **Expected Results**:
  - Successful registration with a generated User ID.
  - Appropriate network calls (`/begin-registration` and `/complete-registration` with 200 status).

### 2. Authentication Test
- **Steps**:
  - Navigate to "Retrieve Seed", enter the valid User ID.
  - Authenticate by inserting and touching your YubiKey.
- **Expected Results**:
  - Successful authentication and seed retrieval.
  - Error cases: invalid User ID, no YubiKey connected, authentication timeout.

### 3. Storage Test
- **Steps**:
  - Store a generated/imported seed.
  - Verify in the SQLite database that the seed record is created and encrypted.
- **Expected Results**:
  - Encrypted seed is stored and linked to the correct user.
  - YubiKey and salt records are properly maintained.

### 4. End-to-End Test
- **Workflow**:  
  - Generate a seed → Register YubiKey → Encrypt and store seed → Log out → Retrieve seed.
- **Expected Results**:
  - The retrieved seed matches the originally generated/imported seed.
  - All API calls complete successfully and sessions are handled correctly.

## Troubleshooting & Reporting
- **Common Issues**:
  - YubiKey not detected: Check device connection and browser support.
  - Session timeouts: Verify cookie/session settings.
- **Documentation**:  
  - Record test outcomes, browser versions, and error messages.
  - Capture screenshots for any failures and update the task tracker accordingly.

[Back to README](../README.md) 