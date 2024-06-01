# tempest

## Description

This is just a small program which will listen for UDP broadcast messages from the Weatherflow Tempest Hub and produce InfluxDb line protocol, which can afterwards be handeled by Telegraf.

The implementation has been done according the [Weatherflow Tempest UDP Reference v171](https://weatherflow.github.io/Tempest/api/udp/v171/).
Message types irrelevant for the Tempest station (such as obs_air and obs_sky) haven't been implemented.


## Parameters

If needed please change the variables `BROADCAST_IP` as well as `BROADCAST_PORT` within the python script.

When calling the program it needs to have an argument passed for the Hub-SN as well as the location. Whereby `HUBSN` being the serial number of the Hub and `LOCATION` being the corresponding location tag.


## Usage


### Download

Download the python file using: `wget https://raw.githubusercontent.com/mb1979/tempest/main/tempest.py`


### Execute

For production use install and configure Telegraf.

For testing call the program using: `python tempest.py <HUBSN> <LOCATION>`

The program will exit on error or can be exited using `<ctrl>+<c>`.


## Telegraf configuration


### Telegraf input configuration

Create the telegraf input for the python script and set `HUBSN` and `LOCATION` accordingly:
```
cat >/etc/telegraf/telegraf.d/in_execd_tempest.conf <<EOF
[[inputs.execd]]
  command = ["/usr/bin/python", "/<PATH>/tempest.py", "<HUBSN>", "<LOCATION>"]
  # environment = []
  signal = "none"
  restart_delay = "10s"
  # buffer_size = "64Kib"
  # stop_on_error = false
  data_format = "influx"
EOF
```

### Telegraf output configuration

Create the telegraf output or change your existing output, set `INFLUXDB_HOST` accordingly:
```
cat >/etc/telegraf/telegraf.d/out_influx.conf <<EOF
[[outputs.influxdb]]
  urls = ["http://<INFLUXDB_HOST>:8086"]
  database = "tempest"
  timeout = "10s"
  namepass = ["rainstart","lightningstrike","rapidwind","observation","statusdevice","statushub"]

[[outputs.influxdb]]
  urls = ["http://<INFLUXDB_HOST>:8086"]
  database = "telegraf"
  timeout = "10s"
  namedrop = ["rainstart","lightningstrike","rapidwind","observation","statusdevice","statushub"]
EOF
```

*Please note: there's a delay of several minutes for the data to appear in the InfluxDb, even though the python script will provide the data in real-time. I've already tried to change the `buffer_size` parameter in the `inputs.execd` section unsuccessfully. It looks as if it has to do with the `inputs.execd` section as `outputs.influxdb`*
