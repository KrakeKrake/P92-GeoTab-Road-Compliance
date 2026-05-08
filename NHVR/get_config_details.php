<?php
require 'config.php';

$axle_id = filter_input(INPUT_GET, 'axle_id', FILTER_VALIDATE_INT);
if (!$axle_id) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid axle_id']);
    exit;
}

$stmt = $db->prepare("SELECT tare_weight, gml_tonnes, cml_tonnes, hml_tonnes, max_length_m, axle_count FROM axle_configuration WHERE axle_id=?");
$stmt->execute([$axle_id]);
$row = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$row) {
    http_response_code(404);
    echo json_encode(['error' => 'Configuration not found']);
    exit;
}

$stmt2 = $db->prepare("SELECT group_name, group_limit FROM axle_config_group WHERE axle_id=? ORDER BY group_id");
$stmt2->execute([$axle_id]);
$groups = $stmt2->fetchAll(PDO::FETCH_ASSOC);

echo json_encode([
    'tare'       => $row['tare_weight'],
    'gml'        => $row['gml_tonnes'],
    'cml'        => $row['cml_tonnes'],
    'hml'        => $row['hml_tonnes'],
    'max_length' => $row['max_length_m'],
    'axle_count' => $row['axle_count'],
    'groups'     => $groups,
]);