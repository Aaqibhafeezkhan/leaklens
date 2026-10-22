# Security policy

## Supported versions
Only the latest release on PyPI (`leaklens-ml`) receives fixes.

## Reporting a vulnerability
Please do not open a public issue. Use GitHub's private reporting: the repository's **Security** tab, then **Report a vulnerability**. You can expect an acknowledgement within a few days.

## Scope notes
- `leaklens --scan` parses code with `ast` and never executes it.
- The API (`leaklens.api`) loads model files with `joblib` from a caller-supplied path. Only load models you trust and do not expose `/predict` to untrusted users.