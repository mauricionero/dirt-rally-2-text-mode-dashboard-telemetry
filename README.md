Single file python3 script to run a curses in text mode interface for a Dirt Rally 2 dashboard. It runs in any command line.

The advantage of this is that you can easily run in any device through SSH, including iPhone and Android.

The buttons on the right are to be implemented yet.


This features:
* RPM horizontal display in colors
* Big red shiftlight on top for high RPM
* GEAR display in ascii bigger numbers
* Small minor informations like
  * Speed
  * Lap time
  * Total time
  * Current lap / Total laps


I only tested this in Linux (yes, I'm running Dirt Rally 2 with a logitech G923 on linux flawlessly)

To enable telemetry readings for Dirt Rally 2, at least in Linux, go to some folder like this:
`~/.local/share/Steam/steamapps/compatdata/690790/pfx/drive_c/users/steamuser/Documents/My Games/DiRT Rally 2.0/hardwaresettings/hardware_settings_config.xml`
and look for the udp tag and enable it, also change extradata to 3
```
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

RUNNING: 
```
python3 telemetry_read.py
```
