graph TD
    Client -->|HTTP| API-Gateway
    API-Gateway --> Auth-Service
    API-Gateway --> User-Service