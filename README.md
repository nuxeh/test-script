Automated testing and power control script
==========================================

This is a Python script used to automatically run tests to find kernel issues
on an embedded device running Linux. It's hacky and probably won't work without
modification for a given device or situation.

It controls power, logs in, issues a test command, and logs all kernel messages
over a serial connection.  In the original testing it was used to run stress-ng
to look for rarely occurring virtual memory issues. In this case, stress-ng is
run for half an hour, before restarting and running the test again. While the
script is running it posts its status at various stages, and and elapsed timer
for each test.

A successful test is one where the stress-ng command times out and returns to
the command prompt. A failed test is where a kernel oops has occurred and the
system crashes. The script looks for a prompt over the serial connection to
determine the status of a test. It also tests to see if the test task ended
before the timeout.

All output is logged to disk, numbered, and crudely time-stamped. Two files,
'failed-tests' and 'successful-tests' contain a list of all logs categorised
for success or failure.

Power control hardware
----------------------

In the original application of this script, the device under test had
unconventional power control, meaning that the only way to trigger shutdown or
restart was via a physical power button. To remedy this, an Arduino is used to
control power, via a CMOS inverting buffer with open-drain outputs, mimicking
pressing the power button. The open drain outputs of the buffer essentially
function like a switch, presenting a high impedance to ground when the output
is high, and low impedance to ground when the output is low.

This is wired to test points on the device, where an active low signal coming
from the power button is exposed. The schematic below illustrates the required
circuit. The inverter input is connected to pin 5 on the Arduino.

![schematic]
(https://raw.githubusercontent.com/nuxeh/test-script/master/schematic.png)

The power is controlled by the script over a USB-serial connection to the
Arduino, the code for which can also be found in this repository.
