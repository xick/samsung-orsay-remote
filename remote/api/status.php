<?php
require_once dirname(__FILE__) . '/../lib/config.php';
header('Content-Type: application/json');

$pid = trim(shell_exec('pidof exeTV || pidof exeAPP || pidof exeDSP'));
$host = isset($_SERVER['SERVER_ADDR']) ? $_SERVER['SERVER_ADDR'] : '';

echo json_encode(array(
    'ok' => true,
    'host' => $host,
    'pid' => $pid,
    'php' => PHP_VERSION,
));
