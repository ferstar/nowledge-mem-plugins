# Command Reference

Complete parameter documentation for all Nowledge Mem `nm` commands.

## add - Add Memory

```bash
uv run nm add "Content to remember" [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--title` | `-t` | string | auto | Memory title |
| `--importance` | `-i` | float | 0.5 | Importance level (0.0-1.0) |
| `--labels` | `-l` | string | - | Comma-separated labels |
| `--event-start` | - | string | - | Event start date (YYYY, YYYY-MM, YYYY-MM-DD) |
| `--event-end` | - | string | - | Event end date |
| `--temporal` | - | choice | - | Temporal context: past, present, future, timeless |

**Importance Levels:**
- `0.8-1.0`: critical (red) - Must remember
- `0.6-0.8`: high (yellow) - Important
- `0.4-0.6`: medium (blue) - Normal
- `0.0-0.4`: low (dim) - Background info

## search - Search Memories

```bash
uv run nm search "query" [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--limit` | `-n` | int | 10 | Max memories to return |
| `--threads` | `-t` | int | 5 | Max related threads |
| `--verbose` | `-v` | flag | false | Show more content (300 chars vs 150) |
| `--no-threads` | - | flag | false | Skip thread search |
| `--json` | - | flag | false | Output as JSON |

## expand - View Thread

```bash
uv run nm expand <thread_id>
```

Displays full thread content with all messages formatted as markdown.

## update - Update Memory

```bash
uv run nm update <memory_id> [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--content` | `-c` | string | New content |
| `--title` | `-t` | string | New title |
| `--importance` | `-i` | float | New importance (0.0-1.0) |
| `--labels` | `-l` | string | Replace labels (comma-separated) |

At least one option must be specified.

## delete - Delete Memory

```bash
uv run nm delete <memory_id> [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--yes` | `-y` | Skip confirmation prompt |

## labels - List Labels

```bash
uv run nm labels [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--limit` | `-n` | int | 50 | Max labels to show |

## persist - Save Session

```bash
uv run nm persist [OPTIONS]
```

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--title` | `-t` | string | auto | Custom thread title |
| `--project-path` | `-p` | path | cwd | Project directory path |
| `--source` | - | choice | auto | Session source: auto, claude, codex |
| `--debug` | - | flag | false | Enable debug logging |

**Environment Variable:** Set `PROJECT_PATH` before running if not using `-p`.

## diagnose - Check Connectivity

```bash
uv run nm diagnose [OPTIONS]
```

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--project-path` | `-p` | path | Project directory path |

Checks:
1. Configuration validity
2. API health endpoint
3. Authentication
4. Memory search functionality
