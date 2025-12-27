# Usage Patterns

Common usage scenarios and query mappings for Nowledge Mem.

## User Query Mapping

### Search Queries

| User Input | Command |
|------------|---------|
| "搜索 Python 相关的记忆" | `nm search "Python"` |
| "查找之前关于 API 设计的讨论" | `nm search "API design"` |
| "我之前记录过什么关于 Docker?" | `nm search "Docker"` |
| "Find my notes about authentication" | `nm search "authentication"` |

### Add Queries

| User Input | Command |
|------------|---------|
| "记住这个配置" | `nm add "配置内容" --importance 0.7` |
| "保存这段代码到记忆" | `nm add "代码内容" --labels "code"` |
| "这很重要，记下来" | `nm add "内容" --importance 0.9` |
| "Remember this for later" | `nm add "content"` |

### Session Queries

| User Input | Command |
|------------|---------|
| "保存当前会话" | `nm persist` |
| "记录这次对话" | `nm persist --title "对话主题"` |
| "persist this conversation" | `nm persist` |
| "存一下会话" | `nm persist` |

## Time Range Patterns

For search context:

| Input | Interpretation |
|-------|----------------|
| "上周" / "last week" | Recent 7 days |
| "本周" / "this week" | Since Monday |
| "上月" / "last month" | Previous calendar month |
| "最近" / "recently" | Last 7-14 days |

## Importance Guidelines

| Scenario | Importance | Example |
|----------|------------|---------|
| Critical configs, credentials | 0.9-1.0 | API keys, deployment configs |
| Important decisions | 0.7-0.8 | Architecture choices |
| Regular notes | 0.5-0.6 | Meeting notes, ideas |
| Background info | 0.3-0.4 | References, links |

## Label Conventions

Recommended label patterns:

| Category | Labels |
|----------|--------|
| Technology | `python`, `docker`, `kubernetes`, `api` |
| Type | `config`, `code`, `note`, `decision` |
| Project | `project-name`, `feature-name` |
| Status | `todo`, `done`, `blocked` |

## Output Formats

### Default (Rich)
Human-readable with colors and formatting.

### JSON (--json)
Machine-readable for piping to other tools:
```bash
nm search "query" --json | jq '.memories[0].content'
```
