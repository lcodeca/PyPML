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
import random
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

    ## TESTED WITH: SUMO 1.0.1
    # traci.start(['/home/drone/Applications/SUMO/sumo-1.0.1/bin/sumo',
    #              '-c', 'test_scenario/sumo.subscriptions.cfg'], port=42042)
    ## Running with the last-monday development version
    traci.start(['sumo', '-c', 'test_scenario/sumo.subscriptions.cfg'], port=42042)

    parking_monitor_options = {
        'addStepListener': True,
        'logging': {
            'stdout': False,
            'filename': 'subscriptions.example.log',
            'level': logging.DEBUG,
        },
        'sumo_parking_file': 'test_scenario/parkings.big.add.xml',
        'blacklist': [],
        'vclasses': {'truck', 'passenger', 'motorcycle'},
        'generic_conf': [
            {
                'cond': ['=', 1, 1],
                'set_to': [
                    ['capacity_by_class', {'truck': 15,
                                           'passenger': 50,
                                           'motorcycle': 35,}],
                    ['subscriptions_by_class', {'truck': [5, set()],
                                                'passenger': [15, set()],
                                                'motorcycle': [10, set()]}],
               ],
           },
        ],
        'specific_conf': {},
        'subscriptions': {
            'only_parkings': True,
        },
    }

    monitor = ParkingMonitor(traci, parking_monitor_options, 0.0)
    # parking travel time structure initialized
    monitor.compute_parking_travel_time()

    vehicles_with_subscriptions = set()

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        ## PARKING SUBSCRIPTION
        for vehicle in monitor.get_vehicle_iterator():
            if vehicle['arrived']:
                ## the vehicle is not in the simulation anymore
                continue
            if vehicle['id'] in vehicles_with_subscriptions:
                # nothing to be done here
                continue
            if not vehicle['edge'] or ':' in vehicle['edge']:
                # the vehicle is not yet inserted or in an intersection
                # and the change would not be safe.
                continue
            if vehicle['stops']:
                _, _, stopping_place, stop_flags, _, _ = vehicle['stops'][0]
                if monitor.is_parking_area(stop_flags):
                    ### TRY TO SUBSCRIBE TO YOUR PARKING
                    subscriptions = monitor.get_parking_subscriptions(stopping_place)
                    capacity, vehicles = subscriptions[vehicle['vClass']]
                    free_spots = capacity - len(vehicles)
                    # print(capacity, free_spots, vehicles)
                    if free_spots >= 1:
                        res = monitor.subscribe_vehicle_to_parking(
                            stopping_place, vehicle['vClass'], vehicle['id'])
                        if res:
                            vehicles_with_subscriptions.add(vehicle['id'])
                            print(vehicle['id'], 'subscribed to parking', stopping_place)
                            continue

        ## CENTRALIZED PARKING OPTIMIZATION
        for parking in monitor.get_parking_iterator():

            availability = monitor.get_free_places(
                parking['sumo']['id'], with_subscriptions=True, with_projections=True,
                with_uncertainty=False)

            # print(parking['sumo']['id'], availability)

            for v_type, free_spaces in availability.items():
                if free_spaces >= 0:
                    continue

                projections = parking['projections_by_class'][v_type]
                # print(projections)
                _, subscriptions = parking['subscriptions_by_class'][v_type]
                # print(subscriptions)
                candidates = projections - subscriptions

                ## redistribute the problem
                to_reroute = random.sample(candidates, min(abs(free_spaces), len(candidates)))
                print(to_reroute)

                for vid in to_reroute:
                    is_rerouted = False
                    vehicle = monitor.get_vehicle(vid)
                    if not vehicle['edge'] or ':' in vehicle['edge']:
                        ## the vehicle is on an intersection and the change would not be safe.
                        continue
                    _, _, stopping_place, _, _, _ = vehicle['stops'][0]

                    alternatives = monitor.get_closest_parkings(stopping_place, num=25)
                    for trtime, alt in alternatives:
                        alt_availability = monitor.get_free_places(
                            alt, vclass=vehicle['vClass'],
                            with_subscriptions=True, with_uncertainty=True)
                        print(trtime, alt, alt_availability)
                        if alt_availability > 0:
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
                                    is_rerouted = True
                                    print("""Vehicle {} is going to be rerouted from {} """
                                            """to {} [{}].""".format(vehicle['id'], stopping_place,
                                                                    alt, alt_availability))
                                except traci.exceptions.TraCIException:
                                    print([monitor.get_parking_access(alt), route])
                                    raise
                                break
                    if not is_rerouted:
                        print("Vehicle {} failed to reroute".format(vehicle['id']))


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
