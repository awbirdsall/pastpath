'''pastpath.route : functions associated with creating routes
'''
from random import shuffle

from openrouteservice import client, directions, distance_matrix, places
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.settings import get_instance_settings


def get_distance_matrix_response(marker_coords):
    ors_clnt = client.Client(key=get_instance_settings().ors_key)

    request = {'locations': marker_coords,
           'profile': 'foot-walking',
           'metrics': ['duration']}
    
    dist_matrix_response = ors_clnt.distance_matrix(**request)
    return dist_matrix_response


def optimal_route_from_matrix(marker_coords, marker_names, dist_matrix, start=0):
    tsp_size = len(marker_names)
    num_routes = 1

    optimal_coords = []
    marker_order = []
    route_str = ''

    if tsp_size > 0:
        # set up the routing model for TSP, see
        # https://developers.google.com/optimization/routing/tsp#python_3
        manager = pywrapcp.RoutingIndexManager(tsp_size, num_routes, start)
        routing = pywrapcp.RoutingModel(manager)
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()

        # Create the distance callback, which takes two arguments (the from and to node indices)
        # and returns the distance between these nodes.
        def dist_callback(from_id, to_id):
            from_node = manager.IndexToNode(from_id)
            to_node = manager.IndexToNode(to_id)
            # solver does all computations with integers, for this application
            # just using int() is fine
            dist = int(dist_matrix[from_node][to_node])
            return dist
        dist_callback_index = routing.RegisterTransitCallback(dist_callback)

        # use the distance callback as the arc cost evaluator
        routing.SetArcCostEvaluatorOfAllVehicles(dist_callback_index)

        # Solve, returns a solution if any.
        solution = routing.SolveWithParameters(search_parameters)
        if solution:
            # helpful for debugging
            # print_solution(manager, routing, solution)
            # assuming single "vehicle", no need for outer loop
            index = routing.Start(start) # Index of the variable for the starting node.

            # construct optimal_coords (coords) and route (names)
            # by looping through nodes in solution
            for node in range(routing.nodes()):
                marker_order.append(manager.IndexToNode(index))
                optimal_coords.append(marker_coords[manager.IndexToNode(index)])
                route_str += str(marker_names[manager.IndexToNode(index)]) + ' -> '
                index = solution.Value(routing.NextVar(index))
            route_str += str(marker_names[manager.IndexToNode(index)])
            optimal_coords.append(marker_coords[manager.IndexToNode(index)])
            
    # helpful for debugging
    # comp = compare_random_optimized(optimal_coords)
    # print(f"random {comp['random_duration']}")
    # print(f"optimized {comp['optimal_duration']}")
    return optimal_coords, marker_order, route_str


def directions_route_duration(route_coords):
    ors_clnt = client.Client(key=get_instance_settings().ors_key)
    request = {'coordinates': route_coords,
               'profile': 'foot-walking',
               'geometry': 'true',
               'format_out': 'geojson',
              }

    route = ors_clnt.directions(**request)
    # duration in minutes
    duration = route['features'][0]['properties']['summary']['duration'] / 60

    return route, duration


def print_solution(manager, routing, solution):
    """Prints solution on console."""
    print('Objective: {} minutes'.format(solution.ObjectiveValue()/60))
    index = routing.Start(0)
    plan_output = 'Route for vehicle 0:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += ' {} ->'.format(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        step_distance = routing.GetArcCostForVehicle(previous_index, index, 0)
        print(f"step distance {step_distance}")
        route_distance += step_distance
    plan_output += ' {}\n'.format(manager.IndexToNode(index))
    print(plan_output)
    plan_output += 'Route distance: {}miles\n'.format(route_distance)


def compare_random_optimized(optimal_coords):
    # NB: assumes not returning to starting point in either case
    # See what a random tour would have been
    tour_start = optimal_coords[0]
    marker_coords_shuffle = optimal_coords[1:].copy()
    shuffle(marker_coords_shuffle)
    marker_coords_shuffle_loop = [tour_start] + marker_coords_shuffle
    request = {'coordinates': marker_coords_shuffle_loop,
               'profile': 'foot-walking',
               'geometry': 'true',
               'format_out': 'geojson',
              }
    random_route, random_duration = directions_route_duration(marker_coords_shuffle_loop)

    optimal_route, optimal_duration = directions_route_duration(optimal_coords)

    return {'random_route': random_route,
            'random_duration': random_duration,
            'optimal_route': optimal_route,
            'optimal_duration': optimal_duration}
