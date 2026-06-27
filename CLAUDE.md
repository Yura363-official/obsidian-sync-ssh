# CLAUDE.md — Obsidian Sync SSH

This file documents the project for AI assistants working in this repository.

## Project Overview

**obsidian-sync-ssh** is a desktop GUI application that synchronises Obsidian Markdown vaults:

- **SSH Sync** — pulls/pushes `.md` files between the local machine and a remote server via SSH on a configurable schedule (hours/minutes/seconds interval).
- **Cloud Backup** — backs up `.md` files to Google Drive, Yandex.Disk, Microsoft OneDrive, and/or iCloud Drive.
- **App Dep** — mirrors the local Obsidian folder into a per-computer subfolder (`App Dep/<ComputerName>/`) on each connected cloud service, enabling multi-machine setups under a single cloud account.
- **Config persistence** — can save and restore its own configuration to/from cloud storage (currently Google Drive).

The user-facing documentation (bilingual Russian/English) lives in `README.md`. Source code is distributed separately (see the Google Drive link in the README).

---

## Repository Layout

```
obsidian-sync-ssh/
├── README.md      # Bilingual (RU + EN) user-facing setup guide
└── CLAUDE.md      # This file — AI assistant context
```

No source code is committed here yet. When source files are added, update the layout above and fill in the sections below accordingly.

---

## Application Architecture (Inferred from Docs)

| Layer | Notes |
|---|---|
| GUI | Desktop window with a gear icon (⚙) for settings |
| SSH transport | Key-based or password auth; configurable host, port, user, remote path, local path, poll interval |
| OAuth server | Local HTTP server on `http://localhost:3333` handles OAuth redirect callbacks for Google, Yandex, and Microsoft |
| Cloud adapters | Google Drive API, Yandex.Disk WebDAV/API, Microsoft Graph API, iCloud (local folder via iCloud for Windows) |
| Scheduler | Single configurable interval drives both SSH sync and cloud backup |

### OAuth Redirect URIs (do not change these without updating cloud app registrations)

| Service | Callback URI |
|---|---|
| Google | `http://localhost:3333/oauth/google/callback` |
| Yandex | `http://localhost:3333/oauth/yandex/callback` |
| Microsoft | `http://localhost:3333/oauth/microsoft/callback` |

---

## Key Conventions

### Language
- Documentation is bilingual: Russian section first, English section second, separated by `---`.
- Keep both sections in sync when editing `README.md`.

### Cloud folder naming
- Backup destination: `Obsidian Backup/` (root of each cloud service).
- Multi-machine sync destination: `App Dep/<ComputerName>/` (root of each cloud service).
- These folder names are shown in the UI and described in docs — do not rename them without updating both the code and README.

### SSH defaults
- Default port: `22`.
- Key file is optional; password may be left blank when key auth is used.

### Scheduler interval format
- Expressed as `h / m / s` (hours / minutes / seconds) — three separate numeric fields in the UI.

---

## Development Workflow

### Branch strategy
- `main` — stable, documentation and releases only.
- Feature branches — use descriptive names (e.g. `feature/yandex-disk-adapter`).

### Commits
- Write commit messages in English.
- Prefix with a short type: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.
- Example: `feat: add Yandex.Disk OAuth flow`

### Adding a new cloud provider
1. Register a local OAuth callback route at `http://localhost:3333/oauth/<provider>/callback`.
2. Implement the adapter behind a common interface (connect, backup, app-dep-sync, save-config, load-config).
3. Add UI section in settings following the existing pattern (Client ID + Client Secret fields, Sign-in button, status email display).
4. Document the setup steps in `README.md` (both RU and EN sections).

---

## Security Notes

- OAuth credentials (Client ID, Client Secret) are entered by the user and stored locally — never hardcode or log them.
- SSH passwords and private key paths are user-supplied and sensitive — treat accordingly.
- The local OAuth server on port 3333 must only accept loopback connections.

---

## What Is Not in This Repository

- Application source code (distributed separately via Google Drive — see README link).
- Build scripts, package files, or CI configuration.
- Test suite.

When these are added, document: build command, test command, linter/formatter, and any required environment variables in this file.
