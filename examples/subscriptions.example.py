#!/usr/bin/env python3

""" Example of usage of PyPML.

    Python Parking Monitor Library (PyPML)

    Author: Lara CODECA

    This program and the accompanying materials are made available under the
    terms of the Eclipse Public License 2.0 which is available at
    http://www.eclipse.org/legal/epl-2.0.
"""

import argparse
import logging
import os
import pprint
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

def _args():
    """
    Argument Parser
    ret: parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='{}'.format(sys.argv[0]),
        usage='%(prog)s',
        description='PyPML Subscriptions Example')
    parser.add_argument(
        '--profiling', dest='profiling', action='store_true',
        help='Enable Python3 cProfile feature.')
    parser.add_argument(
        '--no-profiling', dest='profiling', action='store_false',
        help='Disable Python3 cProfile feature.')
    parser.set_defaults(profiling=False)
    return parser.parse_args()

def _main():
    """ Example of parking management in SUMO. """

    traci.start(['sumo', '-c', 'test_scenario/sumo.subscriptions.cfg'])

    parking_monitor_options = {
        'seed': 42,
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

    monitor = ParkingMonitor(traci, parking_monitor_options)
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
            if vehicle['stopped']:
                ## the vehicle is stopped and it does not require additional
                ## parking changes at least for the moment
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

            for v_type, free_spaces in availability.items():
                if free_spaces >= 0:
                    continue

                projections = parking['projections_by_class'][v_type]
                _, subscriptions = parking['subscriptions_by_class'][v_type]
                candidates = projections - subscriptions

                ## redistribute the problem
                to_reroute = random.sample(candidates, min(abs(free_spaces), len(candidates)))

                for vid in to_reroute:
                    is_rerouted = False

                    vehicle = monitor.get_vehicle(vid)
                    if not vehicle['edge'] or ':' in vehicle['edge']:
                        ## the vehicle is on an intersection and the change would not be safe.
                        continue
                    if vehicle['stopped']:
                        ## the vehicle is stopped and it does not require additional
                        ## parking changes at least for the moment
                        continue
                    _, _, stopping_place, stop_flags, _, _ = vehicle['stops'][0]
                    if not monitor.is_parking_area(stop_flags):
                        ## the next stop is not associated to a parking area
                        continue

                    alternatives = monitor.get_closest_parkings(stopping_place, num=25)
                    for trtime, alt in alternatives:
                        alt_availability = monitor.get_free_places(
                            alt, vclass=vehicle['vClass'],
                            with_subscriptions=True, with_uncertainty=True)
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
                                    pprint.pprint([vehicle,
                                                   monitor.get_parking_access(alt),
                                                   route])
                                    raise
                                break
                    if not is_rerouted:
                        print("Vehicle {} failed to reroute".format(vehicle['id']))


if __name__ == '__main__':

    args = _args()

    ## ========================              PROFILER              ======================== ##
    if args.profiling:
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

        ## ====================              PROFILER              ======================== ##
        if args.profiling:
            profiler.disable()
            results = io.StringIO()
            pstats.Stats(profiler, stream=results).sort_stats('cumulative').print_stats(25)
            print(results.getvalue())
        ## ====================              PROFILER              ======================== ##

        traci.close()
