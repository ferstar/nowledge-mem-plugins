# Claude Code Instructions

## Release Process

When releasing a new version, update version numbers in **all** these files:

1. `.claude-plugin/marketplace.json` - `metadata.version` and `plugins[0].version`
2. `.claude-plugin/plugin.json` - `version`

Then create and push the git tag:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z: Brief description"
git push origin vX.Y.Z
```

## Project Structure

- `skills/nowledge-mem/` - Main skill implementation
  - `scripts/` - Python CLI source code
  - `references/` - Documentation for the skill
  - `SKILL.md` - Skill definition and trigger keywords
- `.claude-plugin/` - Plugin manifest files

## Configuration

The `.env` file must be placed in the **cache directory** at runtime:
```
~/.claude/plugins/cache/nowledge-mem-plugins/nm/<version>/skills/nowledge-mem/.env
```

Not in the marketplaces directory.
