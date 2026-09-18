# Codex integration

All project-specific Codex instructions, skills, helpers and migration notes
live in this folder. The Claude setup remains available to Claude.

## Native loading

- `.agents/skills/` is Codex's repository skill discovery directory.
- `AGENTS.md` holds the project conventions in Codex form.
- `python .agents/scripts/configure_codex.py` adds `.agents/AGENTS.md` to the
  user configuration's `project_doc_fallback_filenames`. It preserves other
  settings and saves a backup beside the user config. No root document is needed.
- On another machine, run that setup command once. It honours `CODEX_HOME`.
  Run it with `--check` to inspect the setting without writing.
- Start a new Codex session after setup. Invoke `$onboard`, `$handoff` or
  `$project-report`, or describe the relevant task. Automatic selection is enabled.

The project instruction file applies through the native fallback mechanism.
An `AGENTS.md` or `AGENTS.override.md` in the same directory takes precedence.
This is a user-level discovery setting, so other repositories that use the same
nested filename can also benefit from it.

## Adaptations

| Source | Codex form |
|---|---|
| Project conventions | `.agents/AGENTS.md`, loaded as project instructions |
| `onboard` | Native skill; Codex choice tools and process sessions |
| `handoff` | Native skill; explicit scope, PR preflight, body files and bounded watches |
| `project-report` | Native skill; staged references, four helper scripts, delegation within available slots |
| Claude question and monitor tools | Available Codex question tools and shell process sessions |
| Report design dependencies absent here | Available `frontend-design` and `browser-harness` skills |
| Claude session and tool hooks | Shared git hooks/CI plus explicit Codex startup and handoff checks |

Claude `PreToolUse` hooks and its sandbox settings do not execute in Codex.
The native instructions require the document checks before PR creation or edits.
The tracked `.githooks/commit-msg` and CI retain their enforcement. The active
Codex client's permission settings govern execution. No Claude JSON payload
emulator or tool-name shim is used.

The report helpers are complete native resources, with their usage paths updated.
When a source workflow changes, review the matching Codex skill and helper diff;
do not overwrite adaptations with a blind copy. `migration.json` records source
hashes so later updates can detect drift.

## Global skills and MCPs

The global Codex directory already contains adaptations of all installed Claude
skills: `browser-harness`, `ste-writing`, and the enabled `frontend-design`
plugin skill. The STE reference dictionary and frontend licence are preserved.
Existing additional Codex skills remain available.

The user-level `config.toml` already registers all four global Claude MCPs:
`my-browser`, `context7`, `hostinger-domains`, and `hostinger-dns`. Global skills
stay in the user's Codex skill directory; they are not copied into this project.
Credentials remain in user configuration and are never part of this folder.

`browser-harness` is a skill. `my-browser` is the Playwright MCP server it uses.
The configured Chrome CDP endpoint is `http://localhost:9223`. The native browser
skill uses its actual MCP schemas and a dedicated browser profile, with one
browser operator at a time. A configured MCP server and a reachable browser are
separate checks.

## Verification and references

`validation.json` records checks performed during this migration. Temporary
verification files and report inputs stay in the ignored `.local/` directory.

- [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills)
- [Native configuration settings](https://learn.chatgpt.com/docs/config-file/config-reference)
- [MCP configuration](https://developers.openai.com/codex/mcp/)

Use `codex debug prompt-input` to inspect the installed client's effective
instructions and skill catalog without running a model turn. Treat its complete
output as local context; print only the fields needed for verification.
