# Troubleshooting

Common errors and solutions for Nowledge Mem CLI.

## Connection Errors

### Connection Refused

```
API Error: Connection refused
```

**Cause:** API server not running or wrong URL.

**Solution:**
1. Verify API server is running
2. Check `NOWLEDGE_MEM_API_URL` in `.env`
3. Run `km diagnose` to test connectivity

### Request Timeout

```
API Error: Request timeout after 30s
```

**Cause:** Slow network or server overload.

**Solution:**
1. Increase `NOWLEDGE_MEM_TIMEOUT` value in `.env`
2. Check network connectivity
3. Try again later if server is busy

## Authentication Errors

### 401 Unauthorized

```
API error 401: Authentication failed
```

**Cause:** Invalid or expired token.

**Solution:**
1. Check `NOWLEDGE_MEM_AUTH_TOKEN` in `.env`
2. Regenerate token if expired
3. Leave empty if server doesn't require auth

### 403 Forbidden

```
API error 403: Authorization failed
```

**Cause:** Token valid but insufficient permissions.

**Solution:** Contact admin to grant proper permissions.

## Session Errors

### Session Not Found

```
Session Error: No session file found for project
```

**Cause:** No Claude Code session exists for the project.

**Solution:**
1. Ensure you're in the correct project directory
2. Set `PROJECT_PATH` to the actual project path
3. Run a Claude Code session first to generate session file

### Empty Session

```
Extracted 0 messages from session
```

**Cause:** Session file exists but contains no messages.

**Solution:**
1. Have a conversation in Claude Code first
2. Check if session file is corrupted

## Search Errors

### No Results

```
No memories found.
```

**Cause:** Query doesn't match any stored memories.

**Solution:**
1. Try broader search terms
2. Use `--verbose` to see more details
3. Check if memories exist with `km labels`

## Diagnose Command

Run full diagnostics:

```bash
uv run km diagnose
```

This checks:
- Configuration validity
- API connectivity
- Authentication status
- Search functionality
