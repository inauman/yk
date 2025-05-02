# System Architecture & API Interfaces

## High-Level Overview
The application is divided into two main components:
- **Backend**: A Flask application that handles business logic, encryption, seed management, and API endpoints.
- **Frontend**: A React application that provides a wizard-style user interface, interacts with the backend via REST APIs, and manages user sessions.

## Component Diagram
```
┌────────────────────┐                  ┌────────────────────┐
│   React Frontend   │  ← REST APIs →   │   Flask Backend    │
│ (UI, State Mgmt,   │                  │ (Business Logic,   │
│  API Services)     │                  │  Encryption, DB)   │
└────────────────────┘                  └────────────────────┘
```

## API Interface Design

### 1. Authentication APIs
- **Begin Registration**  
  **Endpoint**: `POST /api/v1/auth/begin-registration`  
  **Request Body**:
  ```json
  {
    "username": "string",
    "displayName": "string"
  }
  ```  
  **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "publicKey": { /* WebAuthn registration options */ }
    }
  }
  ```

- **Complete Registration**  
  **Endpoint**: `POST /api/v1/auth/complete-registration`  
  **Request Body**:
  ```json
  {
    "id": "base64url-encoded-string",
    "rawId": "base64url-encoded-string",
    "response": {
      "clientDataJSON": "base64url-encoded-string",
      "attestationObject": "base64url-encoded-string"
    },
    "type": "public-key"
  }
  ```  
  **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "credentialId": "base64url-encoded-string",
      "userId": "string",
      "created": "ISO-8601-date-string"
    }
  }
  ```

### 2. Seed Management APIs
- **Generate New Seed**  
  **Endpoint**: `POST /api/v1/seeds`  
  **Request Body**:
  ```json
  {
    "strength": 256,
    "yubikeys": ["credentialId1", "credentialId2"]
  }
  ```  
  **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "seedId": "string",
      "created": "ISO-8601-date-string"
    }
  }
  ```

- **Retrieve Seed**  
  **Endpoint**: `GET /api/v1/seeds/{seedId}`  
  **Response**: Returns the decrypted seed if correct keys are provided.

### 3. YubiKey Management APIs
- **List Registered YubiKeys**  
  **Endpoint**: `GET /api/v1/yubikeys`  
  **Response**:
  ```json
  {
    "status": "success",
    "data": {
      "yubikeys": [
        {
          "credentialId": "string",
          "nickname": "string",
          "registered": "ISO-8601-date-string"
        }
      ]
    }
  }
  ```

## Error Handling
All API responses follow a standardized format:
```json
{
  "status": "error",
  "error": {
    "code": "error_code",
    "message": "Human-readable message"
  }
}
```

## Integration Points
- **Frontend to Backend**: Communication occurs over HTTPS using RESTful API endpoints.
- **Database Interaction**: The backend interacts with a SQLite database for persistent storage.
- **Encryption/Decryption**: Uses envelope encryption with separate keys for data encryption and wrapping.

[Back to README](../README.md) 