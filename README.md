# mcpanel

A small web panel for Minecraft servers running in Docker with
[itzg/minecraft-server](https://github.com/itzg/docker-minecraft-server) and
[itzg/mc-backup](https://github.com/itzg/docker-mc-backup).

- Start, stop and restart servers; see players, version, CPU and memory.
- Back up now, or restore a backup (current files are moved aside first).
- Change a server's type (Vanilla, Paper, Fabric, Forge, NeoForge or your own jar),
  version, Java and memory. A running server is backed up first, and the old settings
  come back if the new ones don't start.
- Add servers, new or copied from an existing server folder.
- Choose whether each server starts at boot.

Every change runs as a background job with its log shown on the page.

## How it works
`servers.yml` in `MC_DIR` lists the servers and is the source of truth. The panel
generates `docker-compose.yml` next to it (a server plus a backup container for each)
and runs `docker compose` on it. You can edit `servers.yml` by hand too; the panel picks
up the change on its next action. Each server's files live in `MC_DIR/<name>/`.

## Setup
All machine-specific settings are in `docker-compose.yml`:

| Setting | |
|---|---|
| `MC_DIR` | Folder with `servers.yml` and the server folders |
| `BACKUP_DIR` | Backups go to `BACKUP_DIR/<server>/` |
| `IMPORT_DIR` | Optional. Folders under it with a `server.properties` can be copied when adding a server |
| `PUID`, `PGID` | Owner of the server files and backups |
| `TZ` | Time zone |
| `COMPOSE_PROJECT` | Project name of the generated compose file |
| `NETWORK` | Optional. External Docker network a server joins when it has `network: true` |
| `PANEL_URL` | Optional. Shown in the generated files' headers |
| `FORWARD_TO` | Optional. Where to forward ports, shown after adding a server |

Mount `MC_DIR`, `BACKUP_DIR` and `IMPORT_DIR` at the same path inside the container as
on the host, so the compose commands the panel runs point at the real folders.
`MC_DIR` also needs a `.env` with `RCON_PASSWORD`, and a `servers.yml`
(it can start as `servers: {}`).

The panel uses the Docker socket, which is equivalent to root on the host. It has no
published port: put it behind a reverse proxy with a login, and keep it off the internet.

Then `docker compose up -d --build`.
