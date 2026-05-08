<?php
require 'config.php';

$class_id = filter_input(INPUT_GET, 'class_id', FILTER_VALIDATE_INT);
if (!$class_id) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid class_id']);
    exit;
}

$stmt = $db->prepare("SELECT * FROM vehicle_type WHERE class_id=?");
$stmt->execute([$class_id]);

echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));