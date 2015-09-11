#!/usr/bin/env python

import serial
import glob
import time
import sys
import re
import os

# Hostname of the target
hostname = 'hostname'
username = 'username'
password = ''

# Update interval in seconds
update_interval = 1

# Test command
test_timeout = 1530
test_command = ('./stress-ng --cpu 1 --vm 3 --vm-bytes 64M --fork 5 --timeout %d\r' % 
                (test_timeout - 30))

def send_power_command(command):
    pcserial.write('\r%s\r' % command)

def run_test(log_path):
    log = open(log_path, 'w')
    log.write('<---- Test command: ---->\n')
    log.write(test_command + '\n')
    log.write('<---- Test starts %s ---->' % time.ctime())
    log.flush()
    send_power_command('poweron')
    waiting_for_log_in = True
    while waiting_for_log_in:
        consoleserial.write('\r')
        time.sleep(10)
        read = consoleserial.read(consoleserial.inWaiting())
        log.write(read)
        if '%s login:' % hostname in read:
            waiting_for_log_in = False
            log.write('<----- got login %s ----->' % time.ctime())
            print '  > Got login'

    consoleserial.write('%s\r' % username)
    consoleserial.write('%s\r' % password)
    time.sleep(1)
    consoleserial.write(test_command + '\r')
    print('  > Test command started')

    start_time = int(time.time())
    last_command_check = start_time
    while True:
        time.sleep(update_interval)
        read = consoleserial.read(consoleserial.inWaiting())
        log.write(read)
        log.flush()

        elapsed_seconds = int(time.time()) - start_time
        print "  > Elapsed: %02dm %02ds" % (elapsed_seconds / 60,
                                            elapsed_seconds % 60),
        sys.stdout.flush()
        print '\r',

        # Check for early test exit
        # Check for a prompt or login (containing hostname), in the case that
        # the device restarted
        if (int(time.time()) - last_command_check > 300
              and elapsed_seconds < test_timeout - 60):
            last_command_check = int(time.time())

            consoleserial.write('\r')
            time.sleep(1)
            read = consoleserial.read(consoleserial.inWaiting())
            if hostname in read:
                print ''
                print 'Warning: The test may have finished early'
                log.write(read)
                log.write('<---- Test may have finished early %s ---->' % time.ctime())
                log.flush()
                soft_power_off(log)
                return 'failure'
            else:
                log.write(read.rstrip())
                log.flush()

        if elapsed_seconds > test_timeout:
            print ''
            sys.stdout.flush()

            consoleserial.write('\r')
            time.sleep(1)
            read = consoleserial.read(consoleserial.inWaiting())
            log.write(read)
            # If returned to prompt no kernel bug has occurred
            if 'root@%s:' % hostname in read:
                # TODO: Shutdown logging
                soft_power_off(log)
                return 'success'
            else:
                print "  > Test timed out, assuming caught a bug"
                hard_power_off(log)
                return 'failure'

def hard_power_off(log):
    print '  > Hard powering off'
    log.write('<----- hard powering off %s ----->' % time.ctime())
    log.close()
    send_power_command('hardpoweroff')
    time.sleep(60)

def soft_power_off(log):
    print '  > Powering off'
    log.write('<----- powering off %s ----->' % time.ctime())
    log.close()
    send_power_command('poweroff')
    time.sleep(60)

def scan():
    """scan for available ports. return a list of device names."""
    return set(glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))

ports = scan()
ports2 = set()

if len(sys.argv) > 1:
    console_port = sys.argv[1]
else:
    print "Please disconnect console usb cable and press enter"
    raw_input()

    ports = scan()

    print "Please insert console usb cable and press enter"
    raw_input()

    ports2 = scan()
    console_port = next(iter(ports2 - ports))

# Search for the power control device
pcserial = serial.Serial()
pcserial.baudrate = 115200
pcserial.timeout = 1

print "Found serial ports:"

power_port = None
for name in ports:
    print name
    if 'ACM' in name:
        pcserial.port = name
        pcserial.open()
        pcserial.write("ping\r")
        time.sleep(2)
        ret = pcserial.read(pcserial.inWaiting())
        if 'pong' in ret:
            power_port = name
        pcserial.close()

if power_port:
    print "Power control port identified as: %s" % power_port
else:
    print "Couldn't find power control device!"
    exit(1)

print "Console port identified as: %s" % console_port

pcserial.port = power_port
pcserial.open()

consoleserial = serial.Serial()
consoleserial.baudrate = 115200
consoleserial.timeout = 1
consoleserial.port = console_port
consoleserial.open()

print "Please ensure the device is powered off, and press enter"
raw_input()

test_counter = 1
test_counter = int(raw_input("Start counter is %d, change? " % test_counter))
num_success = 0
num_failure = 0
while True:
    log_dir = time.strftime('%Y%m%d')
    try: 
            os.makedirs(log_dir)
    except OSError:
            if not os.path.isdir(log_dir):
                        raise
    
    padded_count = '%03d' % test_counter
    log_path = log_dir + '/' + padded_count + '-' + re.sub(':', '-', re.sub(' ', '_', time.ctime()))
    print "Running test %d" % test_counter
    print " > Writing log to %s" % log_path
    open(log_path, 'a').close()
    result = run_test(log_path)
    print " Result: %s" % result
    test_counter += 1
    if result == 'success':
        with open('successful-tests', 'a') as f:
            f.write(log_path + '\n')
        num_success += 1
    elif result == 'failure':
        with open('failed-tests', 'a') as f:
            f.write(log_path + '\n')
        num_failure += 1
    print (" Summary: %d/%d success/failure ~= %02.1f%% (%02.1f%% failed)" %
           (num_success, num_failure,
            (num_success / (num_failure + num_success) * 100),
            (num_failure / (num_success + num_failure) * 100)))
