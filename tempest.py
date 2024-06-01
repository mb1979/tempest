#!/usr/bin/env python3

# Description  : listen for UDP messages from the Weatherflow Tempest Hub and produce InfluxDb line protocol
# Author       : mb
# Created      : 2024-05-30
# Dependencies : python 3.9+ needed
# Documentation: see README.md (https://github.com/mb1979/tempest)

import sys
import socket
import select
import time
import struct
import json
import requests

BROADCAST_IP = '239.255.255.250'
BROADCAST_PORT = 50222

# argument checks (first argument will be the name of this file)
if len(sys.argv) != 3:
    print("Error: Invalid number of arguments given, please consult the documentation", file=sys.stderr)
    sys.exit(1)

HUBSN = sys.argv[1]
LOCATION = sys.argv[2]

# create broadcast listener socket
def create_broadcast_listener_socket(broadcast_ip, broadcast_port):

    b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    b_sock.bind(('', broadcast_port))

    mreq = struct.pack("4sl", socket.inet_aton(broadcast_ip), socket.INADDR_ANY)
    b_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    return b_sock

# influx line protocol output
def influx_output(hubsn, measurement, fields, timestamp):

    if hubsn == HUBSN:
        influx_line = measurement + ",Hub=" + hubsn + ",Loc=" + LOCATION + " " + fields + " " + timestamp + "000000000"
        print(influx_line)
    else:
        influx_line = measurement + ",Hub=" + hubsn + " " + fields + " " + timestamp + "000000000"
        print("Unknown Hub: " + hubsn + " (" + influx_line + ")", file=sys.stderr)

    return

# create the listener socket
sock_list = [create_broadcast_listener_socket(BROADCAST_IP, BROADCAST_PORT)]

while True:
    # sleep to reduce cpu usage
    time.sleep(0.01)

    # wait until there is a message to read
    readable, writable, exceptional = select.select(sock_list, [], sock_list, 0)

    # for each socket with a message
    for s in readable:
        data, addr = s.recvfrom(4096)

        # convert data to json
        data_json = json.loads(data)

        if data_json['type'] == 'evt_precip':
            hubsn = str(data_json['hub_sn'])
            fields = "value=1"
            timestamp = str(data_json['evt'][0])
            influx_output(hubsn, "rainstart", fields, timestamp)
        elif data_json['type'] == 'evt_strike':
            hubsn = str(data_json['hub_sn'])
            fields = "DistanceKM=" + str(data_json['evt'][1]) + "i,Energy=" + str(data_json['evt'][2]) + "i"
            timestamp = str(data_json['evt'][0])
            influx_output(hubsn, "lightningstrike", fields, timestamp)
        elif data_json['type'] == 'rapid_wind':
            hubsn = str(data_json['hub_sn'])
            fields = "WindSpeedMPS=" + str(data_json['ob'][1]) + ",WindDirection=" + str(data_json['ob'][2]) + "i"
            timestamp = str(data_json['ob'][0])
            influx_output(hubsn, "rapidwind", fields, timestamp)
        elif data_json['type'] == 'obs_st':
            hubsn = str(data_json['hub_sn'])
            fields = "WindLullMPS=" + str(data_json['obs'][0][1]) + ",WindAvgMPS=" + str(data_json['obs'][0][2]) + ",WindGustMPS=" + str(data_json['obs'][0][3]) + ",WindDirection=" + str(data_json['obs'][0][4]) + "i,WindSampleIntervalS=" + str(data_json['obs'][0][5]) + "i,StationPressureMB=" + str(data_json['obs'][0][6]) + ",AirTemperatureC=" + str(data_json['obs'][0][7]) + ",RelativeHumidityPct=" + str(data_json['obs'][0][8]) + ",IlluminanceLux=" + str(data_json['obs'][0][9]) + "i,UVIndex=" + str(data_json['obs'][0][10]) + ",SolarRadiationWPSQM=" + str(data_json['obs'][0][11]) + "i,RainAmountOverPreviousMinuteMM=" + str(data_json['obs'][0][12]) + ",PrecipitationType=" + str(data_json['obs'][0][13]) + "i,LightningStrikeAvgDistanceKm=" + str(data_json['obs'][0][14]) + "i,LightningStrikeCount=" + str(data_json['obs'][0][15]) + "i,BatteryV=" + str(data_json['obs'][0][16]) + ",ReportIntervalMin=" + str(data_json['obs'][0][17]) + "i"
            timestamp = str(data_json['obs'][0][0])
            influx_output(hubsn, "observation", fields, timestamp)
        elif data_json['type'] == 'device_status':
            hubsn = str(data_json['hub_sn'])
            fields = "Uptime=" + str(data_json['uptime']) + "i,BatteryV=" + str(data_json['voltage']) + ",FirmwareVersion=" + str(data_json['firmware_revision']) + "i,RSSI=" + str(data_json['rssi']) + "i,HubRSSI=" + str(data_json['hub_rssi']) + ",SensorStatus=" + str(data_json['sensor_status']) + "i,Debug=" + str(data_json['debug']) + "i"
            timestamp = str(data_json['timestamp'])
            influx_output(hubsn, "statusdevice", fields, timestamp)
        elif data_json['type'] == 'hub_status':
            hubsn = str(data_json['serial_number'])
            fields = "FirmwareRevision=\"" + str(data_json['firmware_revision']) + "\",Uptime=" + str(data_json['uptime']) + "i,RSSI=" + str(data_json['rssi']) + "i,ResetFlags=\"" + str(data_json['reset_flags']) + "\""
            timestamp = str(data_json['timestamp'])
            influx_output(hubsn, "statushub", fields, timestamp)
        else:
            print("Not yet implemented ( JSON:", data_json, ")", file=sys.stderr)
