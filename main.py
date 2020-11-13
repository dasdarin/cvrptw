import pandas as pd 
import numpy as np
import scipy as sp
import random
import sys
import time
import copy
import re

from customer import Customer
from solution import Solution
from problem import Problem
from route import Route
from optimizer import Optimizer

from collections import deque
from tqdm import tqdm
from scipy.spatial.distance import pdist, squareform


def initialize_customers(problem):
    unassigned = []
    depot = Customer.from_series(problem.customers.iloc[0])
    for customer_id in range(1,problem.customers.shape[0]):
        
        customer = Customer.from_series(problem.customers.iloc[customer_id])
        unassigned.append(customer)
        
    return depot, unassigned

def find_closest(problem, customer, possible_customers):
    min = 9999999999
    best_customer = None
    
    for c in possible_customers:
        
        distance = problem.get_distance(customer.id, c.id)
        if distance<min:
            min = distance
            best_customer = c
    
    return best_customer    

def find_initial_solution(problem, routes = [], unassigned = None, neighbourhood_size = 8, routes_to_consider = 5):


    depot, unassigned_customers = initialize_customers(problem)
    if unassigned is not None:
        unassigned_customers = unassigned

    if len(routes) == 0:
        #choose random customers
        neighbourhood_size = np.minimum(len(unassigned_customers), neighbourhood_size)
        considered_customers = random.sample(unassigned_customers, neighbourhood_size)

        #pronadi najblizeg depotu
        closest_to_depot = find_closest(problem, depot, considered_customers)
        first_route = Route( problem, [closest_to_depot] )
        unassigned_customers.remove(closest_to_depot)
        routes.append(first_route)

    start_time = time.time()
    pbar_1 = tqdm(total = len(unassigned_customers))


    while( len(unassigned_customers)>0 ):

            pbar_1.update(1)

            neighbourhood_size = np.minimum(len(unassigned_customers), neighbourhood_size)
            considered_customers = random.sample(unassigned_customers, neighbourhood_size)

            costs_and_all = []


            for customer in considered_customers:

                b_cost, b_route, b_pos = 999999999999999,-1,-1

                for route in routes[-routes_to_consider:]:

                    if customer.demand > route.capacity:
                        continue

                    cost, position = route.find_best_position(customer) ####

                    if position > 0 and cost < b_cost:

                        b_cost = cost
                        b_route = route
                        b_pos = position
                        costs_and_all.append( (b_cost, b_route, b_pos, customer) )
                        break

                costs_and_all.append( (b_cost, b_route, b_pos, customer) )

            next_customer = min(costs_and_all, key = lambda t: t[0])####

            if next_customer[2] < 0:

                closest_to_depot = find_closest(problem, depot, considered_customers)
                new_route = Route( problem, [closest_to_depot] )
                routes.append(new_route)
                unassigned_customers.remove(closest_to_depot)

            else:

                cost = next_customer[0]
                route = next_customer[1]
                position = next_customer[2]
                customer = next_customer[3]

                route.insert( position, customer   )  
                unassigned_customers.remove(customer)

    pbar_1.update(5)
    
    print( "time to construct initial solution {:.1f}".format((time.time()- start_time)))
    return Solution(problem, routes)


def inital_regret(opty, duration=5, neighbourhood_size = 8, routes_to_consider = 5):
    
    problem = opty.problem
    depot = problem.get_depot()
    unassigned_customers = opty.solution.unassigned
    
    routes = []

    #choose random customers
    neighbourhood_size = np.minimum(len(unassigned_customers), neighbourhood_size)
    considered_customers = random.sample(unassigned_customers, neighbourhood_size)

    start_time = time.time()

    pbar = tqdm(total = len(unassigned_customers))

    while( len(unassigned_customers)>0 ):

            if len(unassigned_customers)%5==0:
                pbar.update(5)

            neighbourhood_size = np.minimum(len(unassigned_customers), neighbourhood_size)
            considered_customers = random.sample(unassigned_customers, neighbourhood_size)

            costs_and_all = []
            regrets_and_all = []

            for customer in considered_customers:

                b_cost, b_route, b_pos = 999999999999999,-1,-1
                
                costs_routes = []

                for route in routes[-routes_to_consider:]:

                    if customer.demand > route.capacity:
                        continue

                    cost, position = route.find_best_position(customer) ####

                    if position > 0:
                        
                        costs_routes.append([cost, route, position])
                        
                        if cost < b_cost:

                            b_cost = cost
                            b_route = route
                            b_pos = position
                            costs_and_all.append( (b_cost, b_route, b_pos, customer) )
                            break
                
                costs_and_all.append( (b_cost, b_route, b_pos, customer) )
                
                costs_routes = sorted( costs_routes , key=lambda x: x[0],
                                 reverse=True ) 
                
                if len( costs_routes ) >= 2:
                    
                    best = costs_routes[0]
                    follow_up = costs_routes[1]
                    
                    regret = follow_up[0] - best[0]
                    
                    regrets_and_all.append( [regret, best[1], best[2], customer] )
                elif len(costs_routes) == 1:
                    
                    cost, route, position = costs_routes[0]
                    regrets_and_all.append( [999999-cost, route, position, customer])                    
                
                
                
            #next_customer_greedy = min(costs_and_all, key = lambda t: t[0])
            
            if len(regrets_and_all)==0:
                
                closest_to_depot = find_closest(problem, depot, considered_customers)
                new_route = Route( problem, [closest_to_depot] )
                routes.append(new_route)
                unassigned_customers.remove(closest_to_depot)
                
                continue
                
            else:
            
                next_customer_regret = max(regrets_and_all, key = lambda t: t[0])
        
            
            if next_customer_regret[2] < 0:

                closest_to_depot = find_closest(problem, depot, considered_customers)
                new_route = Route( problem, [closest_to_depot] )
                routes.append(new_route)
                unassigned_customers.remove(closest_to_depot)
                print("ERRRRRORRR")
                continue

            else:

                regret = next_customer_regret[0]
                route = next_customer_regret[1]
                position = next_customer_regret[2]
                customer = next_customer_regret[3]

                route.insert( position, customer)
                unassigned_customers.remove(customer)


    pbar.update(5)
    
    print( "time to construct initial solution {:.1f}".format((time.time()- start_time)))
    return Solution(problem, routes)

def route_from_str(problem, text):
    regex = r"\>(.*?)\("
    matches = re.finditer(regex, text, re.MULTILINE)
    route = [0]

    for _, match in enumerate(matches, start=1):

        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1

            route.append(int(match.group(groupNum)))
    
    return Route.route_from_indexes(problem, route)


def solution_from_str(problem, text):
    
    solution = text.split("\n")[1:-1]
    solution = [route_from_str(problem, x) for x in solution]
    
    return Solution(problem, routes=solution)





text_solution = """15
1: 0(0)->89(9)->27(30)->69(48)->28(69)->53(87)->40(104)->2(124)->95(147)->13(163)->58(180)->26(200)->0(222)
2: 0(0)->94(13)->92(30)->37(43)->98(55)->59(69)->99(82)->6(99)->96(114)->60(133)->18(150)->82(169)->7(185)->52(205)->0(227)
3: 0(0)->31(18)->1(39)->50(56)->76(72)->3(89)->79(103)->24(129)->68(149)->29(168)->80(188)->12(205)->0(230)
4: 0(0)->21(19)->72(34)->73(48)->57(71)->87(89)->91(113)->16(129)->61(144)->93(169)->85(182)->97(202)->0(230)
5: 0(0)->48(28)->19(47)->62(67)->88(84)->0(114)
6: 0(0)->33(27)->51(45)->20(64)->9(87)->78(107)->34(122)->35(143)->81(167)->77(189)->0(219)
7: 0(0)->83(22)->45(41)->46(62)->8(85)->84(108)->17(147)->86(170)->5(197)->0(228)
8: 0(0)->54(23)->30(69)->32(90)->90(105)->63(120)->10(140)->70(168)->0(200)
9: 0(0)->42(26)->43(46)->14(67)->44(83)->75(132)->74(146)->100(185)->0(220)
10: 0(0)->15(51)->41(87)->22(102)->56(121)->55(146)->4(165)->0(200)
11: 0(0)->47(35)->36(53)->11(82)->0(126)
12: 0(0)->39(34)->23(58)->67(80)->25(156)->0(200)
13: 0(0)->65(50)->66(117)->71(137)->0(187)
14: 0(0)->38(73)->0(126)
15: 0(0)->64(63)->49(98)->0(152)
1583.41"""

bad_init = """20
1: 0(0)->21(19)->2(40)->98(67)->59(81)->99(94)->6(111)->5(131)->17(151)->93(176)->95(193)->94(207)->0(230)
2: 0(0)->89(9)->18(27)->60(44)->53(85)->87(111)->57(129)->74(154)->75(168)->73(186)->58(209)->0(229)
3: 0(0)->52(12)->69(40)->1(55)->30(77)->10(114)->90(132)->32(147)->70(171)->31(189)->0(217)
4: 0(0)->7(22)->19(44)->62(64)->88(81)->12(121)->54(141)->68(162)->3(179)->50(198)->0(225)
5: 0(0)->20(32)->51(51)->9(87)->71(106)->35(133)->81(157)->77(179)->80(196)->0(228)
6: 0(0)->48(28)->47(45)->36(63)->46(85)->49(116)->63(148)->82(184)->0(218)
7: 0(0)->39(34)->29(75)->55(126)->4(145)->25(165)->72(194)->0(227)
8: 0(0)->96(16)->34(78)->79(99)->78(115)->0(157)
9: 0(0)->42(26)->14(46)->86(70)->44(89)->0(131)
10: 0(0)->26(12)->28(31)->27(48)->0(63)
11: 0(0)->33(27)->24(58)->76(86)->0(112)
12: 0(0)->16(30)->43(62)->15(80)->0(121)
13: 0(0)->83(22)->45(41)->85(70)->38(101)->0(154)
14: 0(0)->37(22)->61(41)->40(80)->84(120)->0(155)
15: 0(0)->64(63)->11(86)->0(130)
16: 0(0)->97(18)->92(32)->91(50)->8(85)->0(122)
17: 0(0)->65(50)->66(117)->0(168)
18: 0(0)->67(73)->41(109)->56(132)->13(169)->100(193)->0(228)
19: 0(0)->23(58)->0(105)
20: 0(0)->22(87)->0(124)
2021.50"""

#random.seed(321)
start_time = time.time()
pb = Problem("/home/darin/Desktop/ds/Instances/instanca_predaja.TXT")
#default results = 30s - 19 routes, cost 2133
s = find_initial_solution(pb, neighbourhood_size=3, routes_to_consider=2)
#s = solution_from_str(pb, bad_init)
print(s)
opt = Optimizer(s)
s = opt.late_acceptance(max_iter=15, max_no_improvement=9, start_time=start_time, duration = 5)
print("time to run this algorithm: {:.2f}".format((time.time()-start_time)/60.0))
print(s)

