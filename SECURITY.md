# Security Policy

## Secrets

Never commit:

- Google OAuth client credentials;
- refresh/access tokens;
- private calendar exports;
- audio recordings;
- personal task databases.

The default `.gitignore` excludes `.secrets/`, `.env`, and local databases.

## Calendar writes

Automatic deletion is restricted to events with the private property:

```text
aca_managed=true
```

Protected calendars are treated as read-only constraints.

## Reporting

Please report security problems privately to the repository maintainer before opening a public issue.
