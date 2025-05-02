# YubiKey Bitcoin Seed Storage – Proof of Concept

## Overview
This project demonstrates a proof-of-concept for protecting a Bitcoin seed phrase using YubiKeys. The system implements a 2-of-3 multisig scheme where a user can secure their Bitcoin seed by associating one or more YubiKeys along with a software (app) key.

## Key Features
- **Seed Generation & Validation**: Generates BIP39-compliant seed phrases.
- **YubiKey Registration & Authentication**: Uses WebAuthn for secure, hardware-backed key management.
- **Encryption/Decryption**: Implements an encryption flow (AES-256-GCM with envelope encryption) to secure seed data.
- **Modular Architecture**: Clear separation between the Flask backend and React frontend, with well-defined API interfaces.
- **Task Tracking**: A dedicated project plan for managing and updating tasks.

## Documentation
- [Project Requirements](docs/requirements.md) - Project requirements and use-case details
- [Project Plan](docs/project_plan.md) - Task list and milestones
- [Architecture](docs/architecture.md) - System architecture and API interfaces
- [Implementation Plan](docs/implementation_plan.md) - Environment setup, migration, and deployment instructions
- [Usage and Test Guide](docs/usage_and_test_guide.md) - Usage instructions and consolidated test scripts
- [Security](docs/security.md) - Security considerations and recommended enhancements
- [Developer Guide](docs/developer_guide.md) - Coding conventions, API integration details, and guidelines for contributors

## Quick Start
1. **Backend Setup**: Navigate to the `backend` directory, create a virtual environment, install dependencies (using `uv`), and run `python app.py`.
2. **Frontend Setup**: Navigate to the `frontend` directory, install Node.js dependencies, and start the React development server.
3. **Access**: Open your browser and visit `https://localhost:5001`.

For more details, see the individual documentation files linked above. 