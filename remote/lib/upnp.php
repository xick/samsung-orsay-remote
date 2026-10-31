<?php
// UPnP RenderingControl reads for the TV's own DLNA renderer.
//
// Verified on this set: GetVolume/GetMute work from the TV itself, while
// SetVolume/SetMute are silently ignored when the source IP is the TV's own.
// Writes therefore live in api/volume.php and go through samyGOrc keys.
require_once dirname(__FILE__) . '/config.php';

function renderer_host() {
    $host = isset($_SERVER['SERVER_ADDR']) ? $_SERVER['SERVER_ADDR'] : '';
    if ($host === '' || $host === '127.0.0.1' || $host === '::1') {
        $host = gethostbyname(gethostname());
    }
    return $host;
}

function upnp_soap($action, $extra = '') {
    $host = renderer_host();
    $body = '<?xml version="1.0" encoding="utf-8"?>'
        . '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        . 's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
        . '<u:' . $action . ' xmlns:u="' . RENDERER_SERVICE . '">'
        . '<InstanceID>0</InstanceID><Channel>Master</Channel>' . $extra
        . '</u:' . $action . '></s:Body></s:Envelope>';
    $url = 'http://' . $host . ':' . RENDERER_PORT . RENDERER_PATH;

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 2);
    curl_setopt($ch, CURLOPT_TIMEOUT, 3);
    curl_setopt($ch, CURLOPT_HTTPHEADER, array(
        'Content-Type: text/xml; charset="utf-8"',
        'SOAPAction: "' . RENDERER_SERVICE . '#' . $action . '"',
    ));
    $reply = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    if ($reply === false) {
        throw new Exception('renderer unreachable: ' . $error);
    }
    return array($status, $reply);
}

function upnp_get_volume() {
    list($status, $reply) = upnp_soap('GetVolume');
    if ($status != 200 || !preg_match('/<CurrentVolume>(\d+)<\/CurrentVolume>/', $reply, $m)) {
        throw new Exception('GetVolume failed: HTTP ' . $status);
    }
    return intval($m[1]);
}

function upnp_get_mute() {
    list($status, $reply) = upnp_soap('GetMute');
    if ($status != 200 || !preg_match('/<CurrentMute>(\d+)<\/CurrentMute>/', $reply, $m)) {
        throw new Exception('GetMute failed: HTTP ' . $status);
    }
    return $m[1] === '1';
}

function upnp_state() {
    return array('volume' => upnp_get_volume(), 'mute' => upnp_get_mute());
}
