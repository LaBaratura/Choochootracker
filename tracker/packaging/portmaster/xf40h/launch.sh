#!/usr/bin/env bash
set -Eeuo pipefail
APP="/roms/ports/choochootracker"
cd "$APP"
mkdir -p "$APP/conf" "$APP/conf/.choochootracker"
export HOME="$APP/conf"
export XDG_DATA_HOME="$APP/conf"
export XDG_CONFIG_HOME="$APP/conf"
export SDL_VIDEODRIVER=KMSDRM
if [[ ! -x /opt/fake08/gptokeyb || ! -w /dev/uinput ]]; then
  echo 'XF40H: gptokeyb or uinput unavailable' >&2
  exit 86
fi
python3 -B "$APP/xf40h/car194_hold_select_start_2s.py" --probe || exit 87
sudo -n true || {
  echo 'XF40H: sudo -n unavailable' >&2
  exit 88
}
# Audio device/driver are left on system defaults unless explicitly configured.
# CAR-194: per-app GO-Super START/BACK SDL mapping; keep SELECT free of gptokeyb hotkeys.
export SDL_GAMECONTROLLERCONFIG_FILE="$APP/xf40h/CAR194_GO-Super_Gamepad.gamecontrollerdb.txt"
export SDL_GAMECONTROLLERCONFIG="$(cat "$SDL_GAMECONTROLLERCONFIG_FILE")"
export HOTKEY=guide
# CAR-194: pause ArkOS4Clone Ogage while ChooChooTracker is open.
# Ogage uses SELECT+D-Pad for system volume/brightness; the tracker uses them for navigation.
# System service state is restored on every normal exit or app crash.
CAR194_OGA_EVENTS_WAS_ACTIVE=0
car194_cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  # CAR-194: stop our own hold-to-exit input monitor before restoring system hotkeys.
  if [[ -n "${CAR194_EXIT_MONITOR_PID:-}" ]]; then
    kill "$CAR194_EXIT_MONITOR_PID" 2>/dev/null || true
    wait "$CAR194_EXIT_MONITOR_PID" 2>/dev/null || true
  fi
  if [[ -n "${KEY_PID:-}" ]]; then
    kill "$KEY_PID" 2>/dev/null || true
    wait "$KEY_PID" 2>/dev/null || true
  fi
  if [[ "$CAR194_OGA_EVENTS_WAS_ACTIVE" == 1 ]]; then
    if ! sudo -n systemctl start oga_events.service; then
      printf '%s\n' 'CAR194_ERROR: Could not restore oga_events.service; run sudo systemctl start oga_events.service' >&2
      rc=91
    fi
  fi
  exit "$rc"
}
trap car194_cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if systemctl is-active --quiet oga_events.service; then
  # Mark for restoration BEFORE attempting to stop: even a partially failed stop must be undone.
  CAR194_OGA_EVENTS_WAS_ACTIVE=1
  if ! sudo -n systemctl stop oga_events.service; then
    printf '%s\n' 'CAR194_ERROR: Cannot pause oga_events; refusing to launch with conflicting hotkeys' >&2
    exit 90
  fi
  if systemctl is-active --quiet oga_events.service; then
    printf '%s\n' 'CAR194_ERROR: oga_events did not stop' >&2
    exit 92
  fi
fi
if [[ "${CHOO_USE_GPTOKEYB:-1}" == '1' ]] && [[ -x /opt/fake08/gptokeyb ]]; then
  /opt/fake08/gptokeyb choochootracker.aarch64 -c ./xf40h/choochootracker.gptk &
  KEY_PID=$!
  # gptokeyb is cleaned by car194_cleanup
fi
# CAR-194: run tracker as an explicit child so hold-to-exit signals only this PID.
./choochootracker.aarch64 >> "$APP/conf/launch.log" 2>&1 &
CAR194_TRACKER_PID=$!
python3 -B "$APP/xf40h/car194_hold_select_start_2s.py" "$CAR194_TRACKER_PID" >> "$APP/conf/launch.log" 2>&1 &
CAR194_EXIT_MONITOR_PID=$!
wait "$CAR194_TRACKER_PID"
