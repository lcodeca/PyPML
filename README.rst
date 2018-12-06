PyPML - Python Parking Monitor Library for SUMO

Contacts: Lara CODECA [codeca@eurecom.fr], A-Team [a-team@eurecom.fr]
This project is licensed under the terms of the GPLv3 license.

If you use PyPML, cite us with:
L. Codeca; J. Erdmann; J. Härri.
"A SUMO-Based Parking Management Framework for Large-Scale Smart Cities Simulations",
VNC 2018, IEEE Vehicular Networking Conference,
December 5-7, 2018, Taipei, Taiwan.

--------
Reqirements:
* It requires at least [SUMO 1.0](https://github.com/eclipse/sumo/tree/v1_0_0).
* Due to [Issue #4518](https://github.com/eclipse/sumo/issues/4518) it requires the development
  version of [SUMO](https://github.com/eclipse/sumo.git) in order to use multi-threading.

Tested with:
* Eclipse SUMO Version Development 5345f89a38 (Build features: Linux-4.18.0-1-amd64 x86_64 GNU 8.2.0 Proj GUI GDAL FFmpeg OSG GL2PS SWIG)
* Eclipse SUMO Version 1.0.1 ( Build features: Linux-4.18.0-1-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG)

Installation:
* Install: `pip3 install .` from the root directory, or `python3 setup.py install`
* Development install: `pip3 install -e .` or `python3 setup.py develop`

Examples:
* Given the ~under development~ status of the project, examples are provided.
  * examples/simple.example.py
  * examples/subscriptions.example.py

Important:
* PyPML behavior in case of multiple TraCI servers is umpredictable due to how the subscription are
  implemented, to work around this issue we provide functions to retrieve vehicle and simulation
  subscriptions from the library: `get_traci_vehicle_subscriptions` and
  `get_traci_simulation_subscriptions`
