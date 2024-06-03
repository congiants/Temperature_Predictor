<?php

//Php for inserting max and in temps of a day to a different table. Your path should look like this: C:\xampp\htdocs\temperature_predictor\daily_max_min_temps.php

$hostname = "your_hostname";
$username = "your_username";
$password = "your_password";
$database = "your_database_name";
$sensorTable = "your_sensor_table";
$maxMinTempsTable = "your_max_min_table";

$a=strtotime("yesterday");
$yesterday = date("Y-m-d h:i:sa", $a) . "<br>";
echo $yesterday;

$b=strtotime("tomorrow");
$tomorrow= date("Y-m-d h:i:sa", $b) . "<br>";
echo $tomorrow;

$conn = mysqli_connect($hostname, $username, $password, $database);

if(!$conn){
    die("Connection failed : ".mysqli_connect_error());
}

echo "Connection established with '$database' database";

$sql = "INSERT INTO $maxMinTempsTable (max_temperature, min_temperature, date_time, location)
SELECT MAX(temperature) AS max_temp, MIN(temperature) AS min_temp, date_time, location
FROM $sensorTable 
WHERE date_time BETWEEN '$yesterday' AND '$tomorrow'";

//echo $sql;

if (mysqli_query($conn, $sql)) {
    echo "\r\nNew record inserted at '$maxMinTempsTable'";
}

else{
    echo"Error : ".$sql."<br>".mysqli_error($conn);
}
?>