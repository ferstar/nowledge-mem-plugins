# Configuration

Environment variables for Nowledge Mem CLI.

## Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOWLEDGE_MEM_API_URL` | `http://localhost:14243` | API endpoint URL |
| `NOWLEDGE_MEM_AUTH_TOKEN` | (empty) | Bearer token. When empty, no Authorization header is sent |
| `NOWLEDGE_MEM_TIMEOUT` | `30` | Request timeout in seconds |
| `NOWLEDGE_MEM_TIMEOUT_HEALTH` | `5` | Health check timeout in seconds |
| `NOWLEDGE_MEM_MAX_MESSAGES` | `0` | Max messages for persist (0=unlimited) |
| `NOWLEDGE_MEM_SESSION_SOURCE` | `auto` | Session source for persist (auto/claude/codex) |
| `PROJECT_PATH` | current directory | Project path for persist command |

## Configuration File

Create `.env` file in the skill directory:

```bash
# ~/.claude/skills/nowledge-mem/.env
NOWLEDGE_MEM_API_URL=http://localhost:14243
NOWLEDGE_MEM_AUTH_TOKEN=
NOWLEDGE_MEM_TIMEOUT=30
NOWLEDGE_MEM_MAX_MESSAGES=0
NOWLEDGE_MEM_SESSION_SOURCE=auto
```

## Troubleshooting

### Connection Refused
```
API Error: Connection refused
```
Solution: Verify `NOWLEDGE_MEM_API_URL` and ensure the API server is running.

### Timeout Errors
```
API Error: Request timeout
```
Solution: Increase `NOWLEDGE_MEM_TIMEOUT` value or check network connectivity.
