<?php
//Php for inserting weather data to your local database (with the use of xampp). Your path should look like this: C:\xampp\htdocs\temperature_predictor\data_test.php

$hostname = "localhost";
$username = "your_username";
$password = "your_password";
$database = "your_database";
$loc = 'your_location';

$conn = mysqli_connect($hostname, $username, $password, $database);

if(!$conn){
    die("Connection failed : ".mysqli_connect_error());
}

echo "Database connection established";

print_r($_POST);

if(!empty($_POST['temperature']) && !empty($_POST['humidity'])){
	$temp = $_POST["temperature"];
	$humi = $_POST["humidity"];


    $sql = "INSERT INTO `dht22`(`temperature`, `humidity`, `location`) VALUES (".$temp.", ".$humi.", '.$loc.')";

    if (mysqli_query($conn, $sql)) {
        echo "\r\nNew record inserted";
    }

    else{
        echo"Error : ".$sql."<br>".mysqli_error($conn);
    }
}
?>