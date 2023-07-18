const int TEMP_SIG = 0;
void setup()
{
	pinMode(TEMP_SIG, INPUT);
  	Serial.begin(9600);
}

void loop()
{ 
  float reading = analogRead(TEMP_SIG);
  float voltage = (reading * 5.0) / 1024;
  float temp = (voltage - 0.5) * 100;
  Serial.print("TEMPERATURE = ");
  Serial.print(temp);
  Serial.print("*C");
  Serial.println();
  delay(2000);
}