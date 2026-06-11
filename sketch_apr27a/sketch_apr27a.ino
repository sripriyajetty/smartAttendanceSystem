#include <LiquidCrystal.h>

#define LED_PIN 7
#define BUZZER 6

LiquidCrystal lcd(8, 9, 10, 11, 12, 13);

String input = "";

void setup() {
  Serial.begin(9600);

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  lcd.begin(16, 2);
  lcd.print("System Ready");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      processInput(input);
      input = "";
    } else {
      input += c;
    }
  }
}

// ---------- PROCESS ----------
void processInput(String msg) {
  msg.trim();

  if (msg.startsWith("MARKED")) {
    String name = msg.substring(7);
    showMessage("Marked:", name);
    successSignal();
  }

  else if (msg.startsWith("ALREADY")) {
    String name = msg.substring(8);
    showMessage("Already:", name);
    alreadySignal();
  }

  else if (msg.startsWith("UNKNOWN")) {
    showMessage("Unknown Face", "");
    errorSignal();
  }
}

// ---------- LCD DISPLAY ----------
void showMessage(String line1, String line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);

  lcd.setCursor(0, 1);
  lcd.print(line2);
}

// ---------- SIGNALS ----------
void successSignal() {
  digitalWrite(LED_PIN, HIGH);
  tone(BUZZER, 1000);
  delay(500);
  noTone(BUZZER);
  digitalWrite(LED_PIN, LOW);
}

void alreadySignal() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}

void errorSignal() {
  tone(BUZZER, 300);
  delay(1000);
  noTone(BUZZER);
}