# Developer Guide & Module Integration

## Coding Conventions & Module Organization
- **Backend (Flask)**:
  - Organize code into `api`, `services`, `models`, and `utils`.
  - **API Endpoints**: Defined in separate modules (e.g., `auth.py`, `seeds.py`, `yubikeys.py`).
  - **Services**: Encapsulate business logic (e.g., `bitcoin_service.py`, `webauthn_service.py`, `encryption_service.py`).
  - **Models**: Define data schemas and handle database interactions.
  - **Utils**: Include common helper functions (e.g., validation, security, configuration loading).

- **Frontend (React)**:
  - Organize code into `components`, `pages`, `hooks`, `services`, and `types`.
  - **API Services**: Use Axios to communicate with the Flask backend. Follow the provided API contracts.
  - **Component Design**: Reusable components should reside in the `common` folder.
  - **State Management**: Use React hooks (e.g., `useAuth`, `useWizard`) for managing component state and flows.

## API Interface Documentation
- Each API endpoint is documented with:
  - **Endpoint URL & HTTP method**
  - **Request Body/Parameters**
  - **Response Format** (including success and error responses)
  - **Authentication Requirements**
- This documentation should be maintained in-line with code changes to ensure consistency.

## Integration Guidelines
- **Frontend-Backend Communication**:  
  - Ensure that all API calls are made over HTTPS.
  - Validate responses and handle errors gracefully.
- **Testing**:  
  - Follow the consolidated usage and test guide.
  - Write unit tests for individual modules and integration tests for end-to-end workflows.
- **Documentation Updates**:
  - All changes should be reflected in the project documentation.
  - Maintain a change log for updates to API interfaces or module functionalities.

## How to Update the Project Plan
- Use the provided `project_plan.md` as the central reference.
- When new tasks are added or completed, update the checkboxes accordingly.
- This file is integrated with your agent's workflow to mark tasks as complete.

[Back to README](../README.md) 