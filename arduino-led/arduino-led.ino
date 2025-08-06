const int led_pin_460 = 11;
const int led_pin_trans = 13;
const int led_pin_535 = 9;
const int led_pin_590 = 12;
const int led_pin_670 = 10;

const int MAX_CHRS = 30;
char commandBuffer[MAX_CHRS];

int LED_TRANS_STATUS = 0;
int LED_460_STATUS = 0;
int LED_535_STATUS = 0;
int LED_590_STATUS = 0;
int LED_670_STATUS = 0;

void setup() {
  Serial.begin(9600);

  pinMode(led_pin_460, OUTPUT);
  pinMode(led_pin_trans, OUTPUT);
  pinMode(led_pin_535, OUTPUT);
  pinMode(led_pin_590, OUTPUT);
  pinMode(led_pin_670, OUTPUT);
}

void loop() {
  handleSerial();  // Check and process serial input

  // Update LED states
  digitalWrite(led_pin_460, LED_460_STATUS == 1 ? HIGH : LOW);
  digitalWrite(led_pin_trans, LED_TRANS_STATUS == 1 ? HIGH : LOW);
  digitalWrite(led_pin_535, LED_535_STATUS == 1 ? HIGH : LOW);
  digitalWrite(led_pin_590, LED_590_STATUS == 1 ? HIGH : LOW);
  digitalWrite(led_pin_670, LED_670_STATUS == 1 ? HIGH : LOW);
}

void handleSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c != ';') {
      c = toupper(c);
      strncat(commandBuffer, &c, 1);
    } else {
      parseCommand(commandBuffer);
      memset(commandBuffer, 0, sizeof(commandBuffer));
    }
  }
}

#define GET_AND_SET(variableName) \
  if (strstr(command, "GET " #variableName) != NULL) { \
    Serial.print(#variableName " "); \
    Serial.println(variableName); \
  } else if (strstr(command, "SET " #variableName " ") != NULL) { \
    variableName = (typeof(variableName)) atof(command + (sizeof("SET " #variableName " ") - 1)); \
    Serial.print(#variableName " "); \
    Serial.println(variableName); \
  }

void parseCommand(char* command) {
  GET_AND_SET(LED_460_STATUS);
  GET_AND_SET(LED_535_STATUS);
  GET_AND_SET(LED_590_STATUS);
  GET_AND_SET(LED_670_STATUS);
  GET_AND_SET(LED_TRANS_STATUS);
}
