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
from tqdm import tqdm
from pypml import ParkingMonitor

# """ Import SUMO library """
if 'SUMO_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_TOOLS'])
    import traci
else:
    sys.exit("Please declare environment variable 'SUMO_TOOLS'")

def _main():
    """ Live monitor for SUMO simulations. """
    _begin_sec = 0
    _end_sec = 8000

    traci.start(['sumo', '-c', 'test_scenario/sumo.cfg'], port=42042)

    parking_monitor_options = {
        'addStepListener': True,
        'logging': {
            'stdout': False,
            'filename': 'lib.example.log',
            'level': logging.DEBUG,
        },
        'sumo_parking_file': 'test_scenario/parkings.add.xml',
        'blacklist': [],
        'vclasses': {'truck', 'passenger', 'motorcycle'},
        'generic_conf': [],
        'specific_conf': {},
        'subscriptions': {
            'only_parkings': True,
        },
    }

    monitor = ParkingMonitor(traci, parking_monitor_options, _begin_sec)
    # parking travel time structure initialized
    monitor.compute_parking_travel_time()

    _time = _begin_sec
    try:
        for step in tqdm(range(_begin_sec, _end_sec, 1)):
            _time = step
            traci.simulationStep()

            ## PARKING OPTIMIZATION
            for vehicle in monitor.get_vehicle_iterator():
                if not vehicle['edge'] or ':' in vehicle['edge']:
                    ## the vehicle is on an intersection and the change would not be safe.
                    continue
                if vehicle['stops']:
                    _, _, stopping_place, stop_flags, _, _ = vehicle['stops'][0]
                    if monitor.is_parking_area(stop_flags):
                        ### OPTIMIZE VEHICLE
                        availability = monitor.get_free_places(stopping_place,
                                                               vclass=vehicle['vClass'],
                                                               with_projections=True,
                                                               with_uncertainty=True)
                        if availability < 10:
                            alternatives = monitor.get_closest_parkings(stopping_place, num=25)
                            for trtime, alt in alternatives:
                                alt_availability = monitor.get_free_places(
                                    alt, vclass=vehicle['vClass'],
                                    with_projections=True, with_uncertainty=True)
                                print(step, trtime, alt, alt_availability)
                                if alt_availability > 10:
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
                                            pprint.pprint([monitor.get_parking_access(alt), route])
                                            raise
                                        break

    except traci.exceptions.TraCIException:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.fatal('Fatal error at timestamp %d', _time)
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=10, file=sys.stdout)

    finally:
        for parking in monitor.get_parking_iterator():
            print(parking)
        traci.close()

if __name__ == '__main__':

    ## ========================              PROFILER              ======================== ##
    import cProfile, pstats, io
    profiler = cProfile.Profile()
    profiler.enable()
    ## ========================              PROFILER              ======================== ##

    try:
        _main()
    finally:
        ## ========================              PROFILER              ======================== ##
        profiler.disable()
        results = io.StringIO()
        pstats.Stats(profiler, stream=results).sort_stats('cumulative').print_stats(25)
        print(results.getvalue())
        ## ========================              PROFILER              ======================== ##