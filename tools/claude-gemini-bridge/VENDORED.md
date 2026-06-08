# Vendored: claude-gemini-bridge

This directory is a vendored copy of
[**tkaufmann/claude-gemini-bridge**](https://github.com/tkaufmann/claude-gemini-bridge)
(MIT licensed — see `LICENSE`). It lets Claude Code automatically delegate
large, multi-file analysis tasks to Google Gemini via a `PreToolUse` hook.

It is kept here so the setup is durable and version-controlled with TyDez.
See `README.md` in this directory for full documentation.

## Why it wasn't installed automatically

The upstream `install.sh` writes a global `PreToolUse` hook into
`~/.claude/settings.json` that intercepts `Read|Grep|Glob|Task` and pipes them
through the Gemini CLI. It must be run **on the machine where you actually use
Claude Code**, because:

- It requires the **Gemini CLI** (`gemini`) and a configured `GEMINI_API_KEY`.
  See https://github.com/google-gemini/gemini-cli
- It requires `jq` and `bash` 4.0+.
- It is **interactive** (asks for confirmation and which tools to intercept).
- The hook it installs is global and would intercept tool calls in *any*
  Claude Code session, so install it deliberately.

## Install on your machine

```bash
# Prerequisites: claude CLI, gemini CLI (with GEMINI_API_KEY), jq, bash 4+
cd tools/claude-gemini-bridge
./install.sh          # interactive: confirm + pick tools (e.g. Task|Grep)

# IMPORTANT: fully restart Claude Code — hooks load only at startup.

# Verify
./test/test-runner.sh
```

The installer backs up `~/.claude/settings.json` before editing and merges the
hook into any existing config. To remove it later:

```bash
./uninstall.sh
```

## Configuration

Edit `hooks/config/debug.conf` (or override via environment variables) to tune
delegation thresholds, timeouts, caching, and excluded file patterns. Common
knobs:

- `DRY_RUN=true` — log decisions without calling Gemini (good first test).
- `DEBUG_LEVEL=3` — verbose tracing in `logs/debug/`.
- `CLAUDE_TOKEN_LIMIT`, `MIN_FILES_FOR_GEMINI` — when to delegate.

## Updating this vendored copy

```bash
# from a fresh upstream clone:
git -C /tmp/claude-gemini-bridge pull        # or re-clone
git archive HEAD | tar -x -C tools/claude-gemini-bridge
```

Upstream pinned at vendor time:
- Repo: `https://github.com/tkaufmann/claude-gemini-bridge`
- Commit: `e139cf54cd1b5b0cf1074b4cb5c156f1fab13cf9` (2025-08-17)
