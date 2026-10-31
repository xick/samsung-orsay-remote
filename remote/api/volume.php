<?php
require_once dirname(__FILE__) . '/../lib/upnp.php';
require_once dirname(__FILE__) . '/../lib/keypress.php';
header('Content-Type: application/json');

function volume_fail($status, $message) {
    header('HTTP/1.1 ' . $status);
    echo json_encode(array('error' => $message));
    exit;
}

function send_volume_key($name) {
    $code = key_code_for($name);
    if ($code === null) {
        throw new Exception('Missing key code for ' . $name);
    }
    send_key_code($code);
}

function start_volume_sweep($code, $count) {
    $script = dirname(__FILE__) . '/../lib/volume_sweep.sh';
    if (!is_file($script)) {
        throw new Exception('volume sweep script is missing');
    }
    // One sweep at a time.  The script also takes the lock itself.
    $out = array();
    $rc = 0;
    exec('/dtv/bin/flock -n /tmp/samygo-volume.lock true', $out, $rc);
    if ($rc !== 0) {
        volume_fail('409 Conflict', 'A volume sweep is already running');
    }
    exec('/bin/sh ' . escapeshellarg($script) . ' ' . intval($code) . ' ' . intval($count) . ' >/dev/null 2>&1 &');
}

try {
    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        echo json_encode(upnp_state());
        exit;
    }

    $raw = file_get_contents('php://input');
    $data = json_decode($raw, true);
    $action = isset($data['action']) ? $data['action'] : '';
    $state = null;

    if ($action === 'up') {
        send_volume_key('KEY_VOLUP');
        usleep(250000);
    } elseif ($action === 'down') {
        send_volume_key('KEY_VOLDOWN');
        usleep(250000);
    } elseif ($action === 'toggle_mute') {
        send_volume_key('KEY_MUTE');
        usleep(250000);
    } elseif ($action === 'set') {
        $value = isset($data['volume']) ? $data['volume'] : null;
        if (!is_int($value) && !(is_string($value) && ctype_digit($value))) {
            volume_fail('400 Bad Request', 'volume must be an integer 0..100');
        }
        $target = intval($value);
        if ($target < 0 || $target > 100) {
            volume_fail('400 Bad Request', 'volume must be an integer 0..100');
        }
        $now = upnp_get_volume();
        $diff = $target - $now;
        if ($diff !== 0) {
            $name = $diff > 0 ? 'KEY_VOLUP' : 'KEY_VOLDOWN';
            start_volume_sweep(key_code_for($name), abs($diff));
        }
        // The sweep runs in the background; return the requested value and let
        // the 3 s poll show the ramp.
        $state = array('volume' => $target, 'mute' => upnp_get_mute());
    } else {
        volume_fail('400 Bad Request', 'Unknown action');
    }

    if ($state === null) {
        usleep(150000);
        $state = upnp_state();
    }
    echo json_encode($state);
} catch (Exception $e) {
    volume_fail('502 Bad Gateway', $e->getMessage());
}
