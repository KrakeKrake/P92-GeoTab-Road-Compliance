<?php
require 'config.php';

$vehicle_id = filter_input(INPUT_GET, 'vehicle_id', FILTER_VALIDATE_INT);
if (!$vehicle_id) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid vehicle_id']);
    exit;
}

$stmt = $db->prepare("SELECT * FROM axle_configuration WHERE vehicle_id=?");
$stmt->execute([$vehicle_id]);

echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));