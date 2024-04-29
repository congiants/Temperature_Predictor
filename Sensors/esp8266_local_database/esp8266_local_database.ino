//Code of NodeMcu Lua ESP8266 WIFI Board for sending weather data to your php script

#include <ESP8266httpUpdate.h>
#include <ESP8266WiFi.h>
#include <DHT.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

const String URL = "Your_local_PC_IP:your_port/temperature_predictor/data_test.php";

const char* ssid = "Your_ssid";
const char* password = "Your_wifi_password";

#define DHT_SENSOR_PIN D7
#define DHT_SENSOR_TYPE DHT22

DHT dht_sensor(DHT_SENSOR_PIN, DHT_SENSOR_TYPE);

void setup() {  
  pinMode(LED_BUILTIN, OUTPUT);

  dht_sensor.begin();

  Serial.begin(9600);

  connectWifi();
}

void connectWifi(){
  Serial.println();
  Serial.println("WiFi connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  Serial.print("Connecting");
  
  while (WiFi.status() != WL_CONNECTED){
    digitalWrite(LED_BUILTIN, LOW);
    delay(500);
    digitalWrite(LED_BUILTIN, HIGH);
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.println("NodeMCU IP Address: ");
  Serial.print(WiFi.localIP());

  digitalWrite(LED_BUILTIN, LOW);
  //delay(5000);
  //digitalWrite(LED_BUILTIN, HIGH);
}

// the loop function runs over and over again forever
void loop() {
  if (WiFi.status() != WL_CONNECTED){
    connectWifi();
  }

  float humi = dht_sensor.readHumidity();
  float tempC = dht_sensor.readTemperature();

  if(isnan(humi) || isnan(tempC)){
    Serial.println("DHT error");
  }
  else{
    String postData = "temperature="+String(tempC) + "&humidity="+String(humi);

    HTTPClient http;
    WiFiClient wifiClient;

    http.begin(wifiClient, URL);

    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    int httpCode = http.POST(postData);

    String payload = http.getString();

    Serial.println("----------------");
    Serial.println("DHT22:");
    Serial.print("Humidity: ");
    Serial.println(humi);
    Serial.print("C: ");
    Serial.println(tempC);
    Serial.println("----------------");
    Serial.print("URL: ");
    Serial.println(URL);
    Serial.print("Post Data: ");
    Serial.println(postData);
    Serial.print("httpCode: "); //200 = ok
    Serial.println(httpCode);
    Serial.print("Payload: ");
    Serial.println(payload);

  }
  delay(500);
  ESP.deepSleep(2e6);
}
