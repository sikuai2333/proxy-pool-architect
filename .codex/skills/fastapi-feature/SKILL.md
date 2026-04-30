---
name: fastapi-feature
description: Use this skill when implementing FastAPI routes, request models, response models, or API tests.
---

# FastAPI Feature Skill

Rules:

1. Put route functions under app/api.
2. Use Pydantic request and response schemas.
3. Keep business logic in app/services, not route handlers.
4. Add tests for success and common error cases.
5. Update README API examples when adding or changing endpoints.
6. Do not expose secrets in responses.
