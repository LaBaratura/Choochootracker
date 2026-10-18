#!/usr/bin/env python3
# CAR-194 XF40H: SDL2 raw-button exit chord. Run only as a ChooChooTracker child.
# Requires simultaneous uninterrupted SELECT b12 + START b13 for 2.0 seconds.
import ctypes as C
import os
import signal
import sys
import time

LIB='/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0.3200.10'
TARGET='/roms/ports/choochootracker/choochootracker.aarch64'
BUTTON_SELECT=12
BUTTON_START=13
HOLD_SECONDS=2.0
POLL_SECONDS=0.04

def proc_is_tracker(pid):
    try:
        return os.readlink('/proc/{}/exe'.format(pid)) == TARGET
    except (OSError, ValueError):
        return False

def run(argv):
    sdl=C.CDLL(LIB)
    sdl.SDL_SetHint.argtypes=[C.c_char_p,C.c_char_p]
    sdl.SDL_SetHint.restype=C.c_int
    sdl.SDL_Init.argtypes=[C.c_uint32]
    sdl.SDL_Init.restype=C.c_int
    sdl.SDL_Quit.restype=None
    sdl.SDL_PumpEvents.restype=None
    sdl.SDL_NumJoysticks.restype=C.c_int
    sdl.SDL_JoystickNameForIndex.argtypes=[C.c_int]
    sdl.SDL_JoystickNameForIndex.restype=C.c_char_p
    sdl.SDL_JoystickOpen.argtypes=[C.c_int]
    sdl.SDL_JoystickOpen.restype=C.c_void_p
    sdl.SDL_JoystickNumButtons.argtypes=[C.c_void_p]
    sdl.SDL_JoystickNumButtons.restype=C.c_int
    sdl.SDL_JoystickGetButton.argtypes=[C.c_void_p,C.c_int]
    sdl.SDL_JoystickGetButton.restype=C.c_uint8
    sdl.SDL_JoystickClose.argtypes=[C.c_void_p]
    sdl.SDL_GetError.restype=C.c_char_p
    sdl.SDL_SetHint(b'SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS',b'1')
    if sdl.SDL_Init(0x200):
        print('CAR194_EXIT_MONITOR_SDL_INIT_ERROR='+repr(sdl.SDL_GetError()),flush=True)
        return 3
    joy=None
    try:
        if sdl.SDL_NumJoysticks()!=1:
            print('CAR194_EXIT_MONITOR_GAMEPAD_COUNT_UNEXPECTED',flush=True)
            return 4
        name=sdl.SDL_JoystickNameForIndex(0)
        if name!=b'GO-Super Gamepad':
            print('CAR194_EXIT_MONITOR_GAMEPAD_UNEXPECTED='+repr(name),flush=True)
            return 5
        joy=sdl.SDL_JoystickOpen(0)
        if not joy or sdl.SDL_JoystickNumButtons(joy)<14:
            print('CAR194_EXIT_MONITOR_JOYSTICK_OPEN_FAILED',flush=True)
            return 6
        if argv==['--probe']:
            print('CAR194_EXIT_MONITOR_SDL_PROBE=PASS',flush=True)
            return 0
        if len(argv)!=1 or not argv[0].isdigit():
            print('CAR194_EXIT_MONITOR_INVALID_ARGS',flush=True)
            return 7
        pid=int(argv[0])
        # At launch, allow the child process time to exec the tracker binary.
        for _ in range(80):
            if proc_is_tracker(pid): break
            try: os.kill(pid,0)
            except OSError: return 0
            time.sleep(POLL_SECONDS)
        if not proc_is_tracker(pid):
            print('CAR194_EXIT_MONITOR_WRONG_EXECUTABLE',flush=True)
            return 8
        print('CAR194_HOLD_SELECT_START_ARMED=PASS',flush=True)
        held_from=None
        while proc_is_tracker(pid):
            sdl.SDL_PumpEvents()
            select=bool(sdl.SDL_JoystickGetButton(joy,BUTTON_SELECT))
            start=bool(sdl.SDL_JoystickGetButton(joy,BUTTON_START))
            if select and start:
                if held_from is None:
                    held_from=time.monotonic()
                elif time.monotonic()-held_from>=HOLD_SECONDS:
                    if proc_is_tracker(pid):
                        print('CAR194_EXIT_CHORD_TRIGGERED=PASS',flush=True)
                        os.kill(pid,signal.SIGTERM)
                    return 0
            else:
                held_from=None
            time.sleep(POLL_SECONDS)
        return 0
    finally:
        if joy: sdl.SDL_JoystickClose(joy)
        sdl.SDL_Quit()

if __name__=='__main__':
    sys.exit(run(sys.argv[1:]))
