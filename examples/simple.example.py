#!/usr/bin/env python3

""" Example of usage of PyPML.

    Python Parking Monitor Library (PyPML)
    Copyright (C) 2018
    Lara CODECA

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import os
import sys
import traceback
from pypml import ParkingMonitor

# """ Import SUMO library """
if 'SUMO_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_TOOLS'])
    import traci
else:
    sys.exit("Please declare environment variable 'SUMO_TOOLS'")

def _main():
    """ Example of parking management in SUMO. """

    ## TESTED WITH: SUMO 1.1.0
    # traci.start(['/home/drone/Applications/SUMO/sumo-1.1.0/bin/sumo',
    #              '-c', 'test_scenario/sumo.simple.cfg'], port=42041)
    ## Running with the last-monday development version
    traci.start(['sumo', '-c', 'test_scenario/sumo.simple.cfg'], port=42041)

    parking_monitor_options = {
        'addStepListener': True,
        'logging': {
            'stdout': False,
            'filename': 'simple.example.log',
            'level': logging.DEBUG,
        },
        'sumo_parking_file': 'test_scenario/parkings.small.add.xml',
        'blacklist': [],
        'vclasses': {'truck', 'passenger', 'motorcycle'},
        'generic_conf': [],
        'specific_conf': {},
        'subscriptions': {
            'only_parkings': True,
        },
    }

    monitor = ParkingMonitor(traci, parking_monitor_options, 0.0)
    # parking travel time structure initialized
    monitor.compute_parking_travel_time()

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        ## PARKING OPTIMIZATION
        for vehicle in monitor.get_vehicle_iterator():
            if vehicle['arrived']:
                ## the vehicle is not in the simulation anymore
                continue
            if not vehicle['edge'] or ':' in vehicle['edge']:
                ## the vehicle is on an intersection and the change would not be safe.
                continue
            if vehicle['stops']:
                _, _, stopping_place, stop_flags, _, _ = vehicle['stops'][0]
                if monitor.is_parking_area(stop_flags):
                    ### OPTIMIZE VEHICLE
                    availability = monitor.get_free_places(stopping_place,
                                                           vclass=vehicle['vClass'],
                                                           with_projections=False,
                                                           with_uncertainty=False)
                    if availability < 1:
                        alternatives = monitor.get_closest_parkings(stopping_place, num=25)
                        for trtime, alt in alternatives:
                            alt_availability = monitor.get_free_places(
                                alt, vclass=vehicle['vClass'],
                                with_projections=False, with_uncertainty=False)
                            print(trtime, alt, alt_availability)
                            if alt_availability > 1:
                                ## reroute vehicle
                                route = None
                                try:
                                    edge = monitor.get_parking_access(alt).split('_')[0]
                                    route = traci.simulation.findRoute(
                                        vehicle['edge'], edge, vType=vehicle['vClass'])
                                except traci.exceptions.TraCIException:
                                    route = None

                                if route and len(route.edges) >= 2:
                                    try:
                                        traci.vehicle.rerouteParkingArea(vehicle['id'], alt)
                                        print("""Vehicle {} is going to be rerouted from {} """
                                              """[{}] to {} [{}].""".format(vehicle['id'],
                                                                            stopping_place,
                                                                            availability, alt,
                                                                            alt_availability))
                                    except traci.exceptions.TraCIException:
                                        print([monitor.get_parking_access(alt), route])
                                        raise
                                    break

if __name__ == '__main__':
    ## ========================              PROFILER              ======================== ##
    import cProfile, pstats, io
    profiler = cProfile.Profile()
    profiler.enable()
    ## ========================              PROFILER              ======================== ##

    try:
        _main()
    except traci.exceptions.TraCIException:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=10, file=sys.stdout)
    finally:
        traci.close()
        ## ========================              PROFILER              ======================== ##
        profiler.disable()
        results = io.StringIO()
        pstats.Stats(profiler, stream=results).sort_stats('cumulative').print_stats(25)
        print(results.getvalue())
        ## ========================              PROFILER              ======================== ##
