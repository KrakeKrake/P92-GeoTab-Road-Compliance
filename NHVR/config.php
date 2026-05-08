<?php
$db = new PDO('sqlite:vehicle.db');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);