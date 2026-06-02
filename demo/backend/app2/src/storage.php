<?php

require "vendor/autoload.php";

use Archive7z\Archive7z;

if(isset($_POST['id']) && isset($_FILES['file'])){
    $storage_dir = __DIR__ . "/storage/" . $_POST['id'];

    if(!is_dir($storage_dir)){
        mkdir($storage_dir);
    }

    $obj = new Archive7z($_FILES["file"]["tmp_name"]);
    $obj->setOutputDirectory($storage_dir);
    $obj->extract();
}


?>