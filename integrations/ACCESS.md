# Local sponsor service access

The current deployment is local to the lead's Mac. No shared AWS endpoint is delivered.
These URLs are loopback addresses, not internet-accessible team endpoints.

| Service | Local setting |
| --- | --- |
| Zetaris UI proxy | ZETARIS_API_MODE=proxy, ZETARIS_BASE_URL=http://localhost:3000 |
| Zetaris direct REST alternative | ZETARIS_API_MODE=direct, ZETARIS_REST_URL=http://localhost:8888/api/v1.0 |
| Meterless engines | ENGINES_URL=http://127.0.0.1:8790 |
| Nightshift default runtime | METERLESS_BASE_URL=http://127.0.0.1:8088/v1 |

Use the actual Nightshift endpoint displayed by the installed edition if it differs.
Zetaris's API key and numeric organization ID remain in the user's ignored environment file.
Nightshift authentication comes from METERLESS_TOKEN_FILE pointing at its private proxy-token
file. ENGINES_TOKEN is optional for the loopback-only local Compose service. No real token,
organization ID, account name or password belongs in this document.

See [MAC_LIVE_SETUP.md](MAC_LIVE_SETUP.md) for credential-safe service checks and the full
live acceptance command. The explicit env-file loader reads configuration as data; it never
executes a shell command. Existing process values take precedence.

Running the main core/web Compose stack is separate from starting the standalone engine
Compose project. The documented Mac path runs the Python core on the host, which can reach
all three services on loopback. A core inside another Docker project needs explicit network
configuration; its localhost does not refer to the host or the other containers.
