# NM Plugin

A Claude Code plugin for personal knowledge base management with Nowledge Mem.

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
# In Claude Code
/plugin install <marketplace-url>
```

### Manual Installation

```bash
# Clone the repository
git clone <repo-url> ~/myprojects/nm-plugin

# Test locally
claude --plugin-dir ~/myprojects/nm-plugin
```

## Configuration

Create a `.env` file in the skill directory with:

```bash
MEM_API_URL=https://your-api-endpoint
MEM_AUTH_TOKEN=your-auth-token
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

## Plugin Structure

```
nm-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── nowledge-mem/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       └── pyproject.toml
├── README.md
└── .gitignore
```

## License

MIT
