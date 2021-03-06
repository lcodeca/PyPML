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
        description='PyPML Random Grid Scenario Example')
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

    traci.start(['sumo', '-c', 'random_grid/random.sumocfg'])

    parking_monitor_options = {
        'seed': 42,
        'addStepListener': True,
        'logging': {
            'stdout': False,
            'filename': 'random.example.log',
            'level': logging.DEBUG,
        },
        'sumo_parking_file': 'random_grid/parkingArea.add.xml',
        'blacklist': [],
        'vclasses': {'delivery', 'motorcycle', 'passenger'},
        'generic_conf': [],
        'specific_conf': {},
        'subscriptions': {
            'only_parkings': True,
        },
    }

    monitor = ParkingMonitor(traci, parking_monitor_options)
    # parking travel time structure initialized
    monitor.compute_parking_travel_time()

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        ## PARKING OPTIMIZATION
        for vehicle in monitor.get_vehicle_iterator():
            if vehicle['arrived']:
                ## the vehicle is not in the simulation anymore
                continue
            if vehicle['stopped']:
                ## the vehicle is stopped and it does not require additional
                ## parking changes at least for the moment
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
                                        pprint.pprint([vehicle,
                                                       monitor.get_parking_access(alt),
                                                       route])
                                        raise
                                    break

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
