# Nowledge Mem Plugins

Claude Code plugin marketplace for personal knowledge base management with [Nowledge Mem](https://github.com/ferstar/nowledge-mem).

## Features

- Search memories with semantic similarity
- Add new memories with metadata (labels, importance, temporal context)
- Persist Claude Code/Codex CLI sessions to knowledge base
- Expand and view full thread content
- Update and delete memories
- List all labels

## Installation

### Via Plugin Manager

```bash
# Add marketplace
/plugin marketplace add ferstar/nowledge-mem-plugins

# Install plugin
/plugin install nm
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/ferstar/nowledge-mem-plugins.git

# Test locally
claude --plugin-dir ./nowledge-mem-plugins
```

## Configuration

Create a `.env` file in the skill directory with:

```bash
NOWLEDGE_MEM_API_URL=https://your-api-endpoint
NOWLEDGE_MEM_AUTH_TOKEN=your-auth-token
```

Or set environment variables directly.

## Usage

Once the plugin is loaded, the skill triggers automatically based on keywords like:
- 记忆, 知识库, 保存会话, 搜索记忆
- memory, knowledge, save, search, persist, recall

### Quick Commands

```bash
# Search memories
nm search "Python async patterns"

# Add a memory
nm add "Content to remember" --title "Title" --labels "tag1,tag2"

# Persist current session
PROJECT_PATH=/path/to/project nm persist

# View full thread
nm expand <thread_id>

# Check connectivity
nm diagnose
```

## Repository Structure

```
nowledge-mem-plugins/
├── .claude-plugin/
│   ├── marketplace.json      # Marketplace catalog
│   └── plugin.json           # Plugin manifest
├── skills/
│   └── nowledge-mem/
│       ├── SKILL.md          # Skill definition
│       ├── scripts/          # CLI source code
│       │   ├── cli.py
│       │   ├── api.py
│       │   ├── config.py
│       │   ├── search.py
│       │   └── session.py
│       ├── references/       # Documentation
│       │   ├── command_reference.md
│       │   ├── configuration.md
│       │   ├── troubleshooting.md
│       │   └── usage_patterns.md
│       ├── pyproject.toml
│       └── .env.example
├── README.md
└── .gitignore
```

## License

MIT
