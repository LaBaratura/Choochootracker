# XF40H ArkOS4Clone (experimental, opt-in)

This is an optional PortMaster compatibility layer, disabled by default.
It targets XF40H (aarch64) with a GO-Super Gamepad, SDL GUID
`1900bb3e4b4800000011000000010000` (START b13, SELECT b12).

After confirming matching hardware, enable it with:

    mkdir -p /roms/ports/choochootracker/conf
    touch /roms/ports/choochootracker/conf/xf40h-arkos4clone.enabled

Delete that marker to return to the standard PortMaster launcher.

The wrapper sets a local SDL mapping and gptokeyb profile, suspends
oga_events.service so SELECT+D-pad does not change volume or brightness,
and restores the service when the wrapper exits.

Hold SELECT+START for two seconds to terminate the tracker process.
Save your project first: SIGTERM may lose unsaved edits.

An abnormal SIGKILL of the launcher may prevent service restoration.
Recover using: sudo systemctl start oga_events.service

Requires Python 3, SDL2, /opt/fake08/gptokeyb, /dev/uinput,
and passwordless sudo for service control.

Status: the four input support files SHA-matched an XF40H installation.
The newly repackaged official PortMaster ZIP is not yet hardware-tested.

No user samples, personal projects, ROMs or credentials are included.
