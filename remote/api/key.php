<?php
require_once dirname(__FILE__) . '/../lib/keypress.php';
header('Content-Type: application/json');

function key_fail($status, $message) {
    header('HTTP/1.1 ' . $status);
    echo json_encode(array('error' => $message));
    exit;
}

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!is_array($data) || !isset($data['key'])) {
    key_fail('400 Bad Request', 'Missing key');
}

$name = $data['key'];
$code = key_code_for($name);
if ($code === null) {
    key_fail('400 Bad Request', 'Unknown key');
}

try {
    send_key_code($code);
    echo json_encode(array('ok' => true));
} catch (Exception $e) {
    key_fail('502 Bad Gateway', $e->getMessage());
}
