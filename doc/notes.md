## notes

    pi@raspberrypi:~ $ wmctrl -l -p
    0x00c00001  0 2434   raspberrypi Haussteuerung - Chromium
    ^           ^  ^         ^       ^-- WIndows title
    |           |  |         |-- hostname of X client
    |           |  |-- pid
    |           |- desktop nr (-1 for sticky)
    |-- window id




    wmctrl  -k on   # show desktop


    wmctrl  -a  Haussteuerung - Chromium   # activate window
    wmctrl  -r  Haussteuerung - Chromium  -b add,hidden   # hide window
