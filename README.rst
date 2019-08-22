PyPML - Python Parking Monitor Library for SUMO

Contacts: Lara CODECA [lara.codeca@gmail.com], Jerome HAERRI [haerri@eurecom.fr]

This program and the accompanying materials are made available under the terms of
the Eclipse Public License 2.0 which is available at http://www.eclipse.org/legal/epl-2.0.

This Source Code may also be made available under the following Secondary Licenses when the 
conditions for such availability set forth in the Eclipse Public License, v. 2.0 are satisfied: 
GNU General Public License version 3 <https://www.gnu.org/licenses/gpl-3.0.txt>.

If you use PyPML, cite us with:
L. Codeca; J. Erdmann; J. Härri.
"A SUMO-Based Parking Management Framework for Large-Scale Smart Cities Simulations",
VNC 2018, IEEE Vehicular Networking Conference,
December 5-7, 2018, Taipei, Taiwan.

--------
Reqirements:
* It requires at least [SUMO 1.0.1](https://github.com/eclipse/sumo/tree/v1_0_1).

Tested with:
* Eclipse SUMO Version 1.2.0
 Build features: Linux-4.19.0-4-amd64 x86_64 GNU 8.3.0 Release Proj GUI GDAL FFmpeg OSG GL2PS SWIG
* Eclipse SUMO Version 1.1.0
 Build features: Linux-4.19.0-4-amd64 x86_64 GNU 8.3.0 Release Proj GUI GDAL FFmpeg OSG GL2PS SWIG
* Eclipse SUMO Version 1.0.1
 Build features: Linux-4.19.0-4-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG

--------
Installation:
* Install: `pip3 install .` from the root directory, or `python3 setup.py install`
* Development install: `pip3 install -e .` or `python3 setup.py develop`

--------
Examples:
* Given the ~under development~ status of the project, examples are provided.
  * examples/simple.example.py
  * examples/subscriptions.example.py (Subscription usage)
  * examples/uncert.example.py (Uncertainty usage)
  * examples/random.grid.example.py applies the simple.example.py to random_grid,
    a more complex scenario than test_grid.

--------
Important:
* PyPML behavior in case of multiple TraCI servers is unpredictable due to how the subscriptions are
  implemented, to work around this issue we provide functions to retrieve vehicle and simulation
  subscriptions from the library: `get_traci_vehicle_subscriptions` and
  `get_traci_simulation_subscriptions`
* Due to some changes in the SUMO development version of the TraCI APIs, the master branch is not
compatible with SUMO 1.2.0. Release v0.2 is compatible with SUMO 1.2.0
