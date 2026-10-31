<?php
// Local samyGOrc key path.  The key code is always an int from keys.php; the
// request never reaches the shell.
require_once dirname(__FILE__) . '/config.php';
require_once dirname(__FILE__) . '/keys.php';

function tv_pid() {
    $out = trim(shell_exec('pidof exeTV || pidof exeAPP || pidof exeDSP'));
    if ($out === '' || $out === null) {
        return '';
    }
    $pids = preg_split('/\s+/', $out);
    return $pids[0];
}

function samygorc_path() {
    if (is_executable(RC_BIN)) {
        return RC_BIN;
    }
    if (is_executable(RC_FALLBACK)) {
        return RC_FALLBACK;
    }
    throw new Exception('samyGOrc not found');
}

function key_code_for($name) {
    global $KEY_CODES;
    if (!is_string($name) || !isset($KEY_CODES[$name])) {
        return null;
    }
    return $KEY_CODES[$name];
}

function send_key_code($code) {
    $pid = tv_pid();
    if ($pid === '') {
        throw new Exception('exeTV/exeAPP/exeDSP not running');
    }

    $lock = @fopen('/tmp/samygo-key.lock', 'c');
    if ($lock) {
        @flock($lock, LOCK_EX);
    }

    $cmd = samygorc_path() . ' -p ' . escapeshellarg($pid) . ' ' . intval($code) . ' 2>&1';
    $out = array();
    $rc = 0;
    exec($cmd, $out, $rc);

    if ($lock) {
        @flock($lock, LOCK_UN);
        @fclose($lock);
    }

    if ($rc !== 0) {
        throw new Exception('samyGOrc failed: ' . implode(' ', $out));
    }
}
