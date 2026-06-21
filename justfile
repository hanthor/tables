# Tables — build & run as a Flatpak using the org.flatpak.Builder flatpak.
# Designed to run on the `himachal` build host (no system flatpak-builder needed).

app_id := "io.github.hanthor.tables"
manifest := app_id + ".json"

default:
    @just --list

# Fetch the suite-common subproject (offline-safe; flatpak build sandbox has no net).
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p subprojects
    if [ -d subprojects/suite-common/.git ]; then
        git -C subprojects/suite-common fetch --depth 1 origin main
        git -C subprojects/suite-common reset --hard origin/main
    else
        rm -rf subprojects/suite-common
        git clone --depth 1 https://github.com/hanthor/suite-common.git subprojects/suite-common
    fi

# Build the Flatpak and install it to the user installation.
# Build artifacts live outside the source tree so `type: dir` only copies sources.
build: setup
    #!/usr/bin/env bash
    set -euo pipefail
    # org.flatpak.Builder is sandboxed: pin its cwd to this project and give it
    # host fs access. Run from a path under $HOME (flatpaks get a private /tmp).
    state="$HOME/.cache/tables-flatpak"
    mkdir -p "$state"
    flatpak run --cwd="$PWD" --filesystem=host org.flatpak.Builder \
        --force-clean --user --install --install-deps-from=flathub \
        --state-dir="$state/state" \
        --repo="$state/repo" \
        "$state/build" "{{manifest}}"

# Run the installed Flatpak. Inherits the caller's Wayland/X session.
run:
    flatpak run {{app_id}}

# Build, then launch headlessly for a few seconds to confirm it doesn't crash.
smoke: build
    #!/usr/bin/env bash
    set -euo pipefail
    timeout 8 flatpak run {{app_id}} >/tmp/tables-run.log 2>&1 &
    pid=$!
    sleep 6
    if kill -0 "$pid" 2>/dev/null; then echo "OK: still running"; kill "$pid" 2>/dev/null || true; else wait "$pid"; fi
    echo "--- log ---"; cat /tmp/tables-run.log || true

clean:
    rm -rf subprojects/suite-common "$HOME/.cache/tables-flatpak"
