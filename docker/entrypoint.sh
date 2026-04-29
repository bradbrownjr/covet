#!/bin/sh
# Covet container entrypoint.
#
# Responsibilities:
#   1. Apply UMASK
#   2. Reconcile container user with PUID/PGID (Unraid-style)
#   3. Ensure /data and /config are writable by that user
#   4. Drop privileges via gosu and exec covet
#
# If the image is started as a non-root user (e.g. compose `user:` directive),
# we skip the chown/step-down dance and exec directly — this lets advanced
# users opt out of root entirely.
set -eu

umask "${UMASK:-0022}"

DATA_DIR="${COVET_DATA_DIR:-/data}"
CONFIG_DIR="${COVET_CONFIG_DIR:-/config}"

if [ "$(id -u)" = "0" ]; then
    PUID="${PUID:-1000}"
    PGID="${PGID:-1000}"

    # Ensure the covet group has the requested GID
    current_gid="$(getent group covet | cut -d: -f3 || echo '')"
    if [ -n "$current_gid" ] && [ "$current_gid" != "$PGID" ]; then
        # If another group already owns this GID (common on Unraid: 100=users), reuse it
        existing="$(getent group "$PGID" | cut -d: -f1 || true)"
        if [ -n "$existing" ] && [ "$existing" != "covet" ]; then
            usermod -g "$existing" covet
        else
            groupmod -o -g "$PGID" covet
        fi
    fi

    # Ensure the covet user has the requested UID
    current_uid="$(id -u covet 2>/dev/null || echo '')"
    if [ -n "$current_uid" ] && [ "$current_uid" != "$PUID" ]; then
        usermod -o -u "$PUID" covet
    fi

    mkdir -p "$DATA_DIR" "$CONFIG_DIR"
    # Best-effort chown — silently skip files we don't own (e.g. read-only mounts)
    chown -R "$PUID:$PGID" "$DATA_DIR" "$CONFIG_DIR" 2>/dev/null || true

    exec gosu "$PUID:$PGID" covet "$@"
fi

# Already non-root: just exec
exec covet "$@"
