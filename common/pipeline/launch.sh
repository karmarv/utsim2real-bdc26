#!/usr/bin/env bash
# Run a pipeline script detached from the terminal (survives SSH loss), from a snapshot copy so that editing the
# repository never breaks a running job (bash reads scripts incrementally).
#   bash common/pipeline/launch.sh <run_dir> <name> <script> [args...]
# Writes <run_dir>/bin/<name>.sh (the snapshot), <run_dir>/<name>.log, a line in <run_dir>/pids.txt and a LAUNCH event.
set -euo pipefail
RUN=$1; NAME=$2; SRC=$3; shift 3
mkdir -p "$RUN/bin"
# the snapshot runs outside the repository, so it gets the repository root from here
export BDC_REPO="${BDC_REPO:-$(git -C "$(dirname "$SRC")" rev-parse --show-toplevel 2>/dev/null || pwd)}"
cp "$SRC" "$RUN/bin/$NAME.sh"
for f in "$(dirname "$SRC")"/*.sh; do [ -e "$RUN/bin/lib_$(basename "$f")" ] || cp "$f" "$RUN/bin/lib_$(basename "$f")"; done
setsid nohup bash "$RUN/bin/$NAME.sh" "$@" > "$RUN/$NAME.log" 2>&1 < /dev/null &
sleep 1
PID=$(pgrep -f "$RUN/bin/$NAME[.]sh" | head -n 1 || true)
echo "$(date '+%F %T') $NAME pid ${PID:-?} : $SRC $*" >> "$RUN/pids.txt"
echo "$(date '+%F %T') LAUNCH $NAME pid ${PID:-?}" >> "$RUN/events.txt"
echo "launched $NAME (pid ${PID:-?}); log $RUN/$NAME.log"
