<?php
// SamyGO wiki samyGOrc **Index** column, decimal values (Orsay build).
// Keep in sync with tvbridge.KEY_CODES; tests/test_remote.py enforces it.
$KEY_CODES = array(
    // power / source
    'KEY_SOURCE' => 1,
    'KEY_POWER' => 2,
    'KEY_POWER_OFF' => 152,
    'KEY_POWER_ON' => 153,
    'KEY_SLEEP' => 3,
    // digits (volume up/down sit at 7 and 11 in the index, so digits skip them)
    'KEY_1' => 4,
    'KEY_2' => 5,
    'KEY_3' => 6,
    'KEY_4' => 8,
    'KEY_5' => 9,
    'KEY_6' => 10,
    'KEY_7' => 12,
    'KEY_8' => 13,
    'KEY_9' => 14,
    'KEY_0' => 17,
    // volume / channel
    'KEY_VOLUP' => 7,
    'KEY_VOLDOWN' => 11,
    'KEY_MUTE' => 15,
    'KEY_CHUP' => 18,
    'KEY_CHDOWN' => 16,
    'KEY_PRECH' => 19,
    'KEY_CH_LIST' => 107,
    // navigation
    'KEY_UP' => 96,
    'KEY_DOWN' => 97,
    'KEY_LEFT' => 101,
    'KEY_RIGHT' => 98,
    'KEY_ENTER' => 104,
    'KEY_RETURN' => 88,
    'KEY_EXIT' => 45,
    // menus / info
    'KEY_MENU' => 26,
    'KEY_INFO' => 31,
    'KEY_TOOLS' => 75,
    'KEY_GUIDE' => 79,
    'KEY_TV' => 27,
    'KEY_ASPECT' => 62,
    'KEY_PMODE' => 40,
    // Smart Hub
    'KEY_CONTENTS' => 121,
    'KEY_HOME' => 118,
    'KEY_APP_LIST' => 143,
    'KEY_ENTERTAINMENT' => 148,
    'KEY_HDMI' => 139,
    // media
    'KEY_PLAY' => 71,
    'KEY_PAUSE' => 74,
    'KEY_STOP' => 70,
    'KEY_REWIND' => 69,
    'KEY_FF' => 72,
    'KEY_REC' => 73,
    // colour buttons
    'KEY_RED' => 108,
    'KEY_GREEN' => 20,
    'KEY_YELLOW' => 21,
    'KEY_CYAN' => 22,
);
