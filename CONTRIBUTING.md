# Contributing

Thanks for improving the starter.

## Scope

Keep changes generic and self-hostable. Do not add real credentials, private hostnames, personal contact data, proprietary model configuration, or assumptions about a particular agent framework.

## Local checks

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
python -m compileall -q app.py
```

## Change expectations

- Keep the browser untrusted and credentials server-side.
- Add or update tests for changed server behavior.
- Preserve the loopback-first deployment default.
- Document changed environment variables and upstream contracts.
- Keep error messages safe for browser display.
- Do not commit `.env`, generated audio, recordings, or local virtual environments.

## Pull requests

Describe the problem, implementation, tests run, and any deployment or security implication. Small focused pull requests are easier to review and safer to operate.
