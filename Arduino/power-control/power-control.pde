#include <Cmd.h>

// Uses the CmdArduino library:
// https://github.com/fakufaku/CmdArduino

int digital_output = 5;
int status_led = 13;

void setup(){
  pinMode(digital_output, OUTPUT);
  digitalWrite(digital_output, LOW);

  pinMode(status_led, OUTPUT);

  cmdInit(115200);
  cmdAdd("ping", ping);
  cmdAdd("triggeron", trigger_on);
  cmdAdd("triggeroff", trigger_off);
  cmdAdd("poweron", power_on);
  cmdAdd("poweroff", power_off);
  cmdAdd("hardpoweroff", hard_power_off);

  for (int i=0; i<5; i++){
    digitalWrite(status_led, HIGH);
    delay(200);
    digitalWrite(status_led, LOW);
    delay(200);
  }
}

// Negotiation

void ping(int argc, char **argv){
  Serial.println("pong");
}

// Basic Commands

void turn_on(){
  digitalWrite(digital_output, HIGH);
  digitalWrite(status_led, HIGH);
}

void turn_off(){
  digitalWrite(digital_output, LOW);
  digitalWrite(status_led, LOW);
}

// Derived commands

void trigger_on(int argc, char **argv){
  turn_on();
}

void trigger_off(int argc, char **argv){
  turn_off();
}

void power_on(int argc, char **argv){
  turn_on();
  delay(1000);
  turn_off();
}

void power_off(int argc, char **argv){
  turn_on();
  delay(4000);
  turn_off();
}

void hard_power_off(int argc, char **argv){
  turn_on();
  delay(20000);
  turn_off();
}

void loop(){
  cmdPoll();
}
