# Auth Feature

The auth feature owns email/password registration and login, first-party JWT session cookies,
logout, and current-user lookup.

Boundaries:

- Routers translate HTTP requests/responses only.
- Services orchestrate password hashing, user persistence, credential verification, and session
  issuance.
- Repositories own database access.
- JWT creation/verification is isolated in core security infrastructure.

Product uploads and AI listing generation must not be added to this feature.
