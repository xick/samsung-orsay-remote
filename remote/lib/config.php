<?php
// TV-hosted settings.
//
// The renderer path comes from the TV's device descriptions (smp_1_..smp_30_);
// smp_13_ is the RenderingControl service on this UE48J5248.  If a firmware
// update moves it, scan the descriptions again and update this constant.
define('RENDERER_PATH', '/smp_13_');
define('RENDERER_PORT', 7676);
define('RENDERER_SERVICE', 'urn:schemas-upnp-org:service:RenderingControl:1');

// Full paths: SGO.env does not extend PATH for CGIs.
define('RC_BIN', '/mnt/opt/privateer/usr/bin/samyGOrc');
define('RC_FALLBACK', '/mnt/opt/privateer/usr/schedulepvr/libs/samyGOrc');
