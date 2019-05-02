# Chatroom By Tornado

Chat room is implemented by Python2.7, tornado module and Tcl/Tk .



## Installation

#### Windows

Download and install  ActiveTcl  version8.6

`pip install -r requirements.txt`



#### Linux

`sudo apt-get install tk8.6`

`export PIP_REQUIRE_VIRTUALENV=false`

`pip install -r requirements.txt`



## Usage

#### server

`python server.py --bind-ip 0.0.0.0 --bind-port 8000`

#### client

`python connect.py --host host_ip --port 8000 --handle "foo"`

