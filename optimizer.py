import pandas as pd 
import numpy as np
import random
import copy
import time

from customer import Customer
from solution import Solution
from problem import Problem
from route import Route

from collections import deque

from tqdm import tqdm



class Optimizer:
    
    def __init__(self, solution, delete_method = "default",
                 construct_method = "default"):
        
        self.solution = solution
        self.problem = self.solution.problem
        self.delete_method = delete_method
        self.construct_method = construct_method
    
    def destroy_randomly(self, solution_orig=None, n=10, inplace = False):
        
        if solution_orig is None:
            solution_orig = self.solution
        
        if not inplace:
            solution = copy.deepcopy(solution_orig)
        else:
            solution = solution_orig        
        
        to_be_removed = random.sample(self.problem.customers.customer.tolist(), n)
        
        for route in solution.routes:
            
            for cs in to_be_removed:
                
                if route.remove(cs):
                    to_be_removed.remove(cs)
                    solution.unassigned.append(Customer.from_id(cs, self.problem))
                    
            if route.is_empty():
                solution.remove_route(route)
                    
        solution.update_cost()
        return solution
    
    
    def destroy_1_random_and_neighbours(self, solution_orig=None, n = 10, inplace=False):
        
        if solution_orig is None:
            solution_orig = self.solution
        
        if not inplace:
            solution = copy.deepcopy(solution_orig)
        else:
            solution = solution_orig
            
        to_be_removed = random.choice(self.problem.customers.customer.tolist())
        neighbours = self.problem.get_neighbours(to_be_removed, n = n)
        to_be_removed = np.append(neighbours, to_be_removed).tolist()
        
        for route in solution.routes:
            
            for cs in to_be_removed:
                
                if route.remove(cs):
                    to_be_removed.remove(cs)
                    solution.unassigned.append(Customer.from_id(cs, self.problem))
                    
            if route.is_empty():
                solution.remove_route(route)
                    
        solution.update_cost()
        return solution
    
    
    def destroy_n_shortest_routes(self, solution_orig=None, n = 3, randomize = False,  inplace = False):
        
        if solution_orig is None:
            solution_orig = self.solution
        
        if not inplace:
            solution = copy.deepcopy(solution_orig)
        else:
            solution = solution_orig          
        
        
        solution.routes = sorted(solution.routes, key=lambda x: len(x.customers),
                                 reverse=True)
        if randomize:
            values = [c.get_n_customers() for c in solution.routes]
            max_value = np.max(values) +1
            values = [max_value - x for x in values]
            summ = sum( values )
            probabilites = [x/summ for x in values]
            routes_to_delete = np.random.choice(solution.routes, size = n, p = probabilites, replace = False)
        else:
            
            routes_to_delete = solution.routes[-n:]
            #print(routes_to_delete)
        
        for route in routes_to_delete:
            
            for cs in route.customers[1:-1]:
                solution.unassigned.append(cs)
                
            solution.remove_route(route)

        solution.update_cost()
        
        return solution
    
    
    def greedy_recreate_extensive(self, solution_orig=None, inplace = False ):
        
        if solution_orig is None:
            solution_orig = self.solution
        
        if not inplace:
            solution = copy.deepcopy(solution_orig)
        else:
            solution = solution_orig 
            
        
        while(len(solution.unassigned)>0):
            
            routes_metadata = []

            for route in solution.routes:

                
                results = self.check_cost_customers_route(route, solution.unassigned)
                
                best_for_route = min(results, key = lambda t: t[0])####

                
                routes_metadata.append( best_for_route )
                
            cost, route, position, customer = min(routes_metadata, key = lambda t: t[0])####
            if position >0:
                route.insert(position, customer, extra_cost = cost, called_from = "greedy, sami dodajemo extra cost")
                solution.unassigned.remove(customer)
                
            else:
                #print("nove rute")
                new_route = Route(solution.problem, [solution.unassigned[-1]]) #problem, customers, get_depot_ = True):
                solution.add_new_route(new_route)                
                solution.unassigned = solution.unassigned[:-1]
                
        return solution        
    
    def find_best_position(self, route, customer): ##cost, position = return
        #put in position
        #check if it's valid
        
        #find all possible positions
        cost_before = route.cost
        if route.calculate_cost(update=True) != cost_before:
            print("ERROR MY DAWG COST BEFORE FINDB BEST IN OPTI NEEDS SOME LOOKY LOOK")


        customers_copy = route.customers[:]
        n = len(customers_copy)
        b_position = -1
        b_cost = 999999999
        
        for position in range(1,n-1):
        
            trial_route = customers_copy[:]
            trial_route.insert(position, customer)
            
            trial_route_ = Route(self.problem, trial_route, get_depot_=False)
            possible, cost = trial_route_.is_valid()
            
            if possible and cost < b_cost:
                b_position = position
                b_cost = cost

        b_cost = b_cost - cost_before
            
        return b_cost, b_position
   
    
    def get_initial_solution_routes_seed(self, number_of_routes = "auto", percent = 1.0):
        
        #new_route(self, solution,method = "far")        
        if number_of_routes == "auto":
            
            min_n_of_routes = np.floor(percent * self.problem.get_total_demand()/self.problem.get_capacity())
        
        seeds = [self.problem.get_depot()]

        while len(self.solution.routes) < min_n_of_routes:
            
            seed = self.find_furthest_from( seeds, self.solution.unassigned)
            
            new_route = Route(self.problem, [seed], get_depot_=True)
            self.solution.add_new_route(new_route)
            seeds.append(seed)
            self.solution.remove_from_unassigned(seed)


    def choose_routes(self, n):

        return self.solution.routes[-n:]




    def get_initial_solution(self, k = 10, r = 5, score_type ="regret"):

        if score_type == "regret":
            f = max

        else:
            f = min
        
        n = len(self.solution.unassigned)
        pbar = tqdm(total = n )

        while( n>0 ):
            
            if n%5==0:
                pbar.update(5)

            k = min(n, k)

            considered = random.sample( self.solution.unassigned, k )

            rotues = self.choose_routes(r)
            costs_and_regrets = []

            for customer in considered:

                route_results_by_customer = []

                for route in rotues:

                    cost, position = self.find_best_position( route, customer )

                    if position > 0:

                        route_results_by_customer.append(  [cost, position, route]  )


                #process results by the customer, and keep the best one

                #regret version
                if score_type == "regret":
                    route_results_by_customer = sorted(route_results_by_customer, key= lambda x: x[0] )
                    if len(route_results_by_customer) >1:
                        
                        best = route_results_by_customer[0]
                        second = route_results_by_customer[1]

                        regret = second[0] - best[0]
                        costs_and_regrets.append(  [regret, best, customer]  )


                    elif len(route_results_by_customer) == 1:
                        best = route_results_by_customer[0]
                        regret = 999999999 - best[0]
                        costs_and_regrets.append( [regret, best, customer] )

                #greedy version
                elif score_type == "greedy":

                    if len(route_results_by_customer) > 0:
                        best = min(route_results_by_customer, key = lambda x: x[0])
                        cost = best[0]
                        costs_and_regrets.append( [cost, best, customer] )                

            #compare results of all customers
            if len(costs_and_regrets) > 0:
                
                _, route_info, customer = f( costs_and_regrets, key = lambda x: x[0] )
                _, position, route = route_info
                route.insert( position, customer , called_from = "get intiial solution optimizer")
                self.solution.remove_from_unassigned(customer)

            else:

                self.new_route(self.solution)

            n -= 1
        pbar.update(5)    
            
            
    def random_destroy_method(self,  solution ):
        choice = np.random.choice([0,1,2,3])

        if choice == 0:
            return self.destroy_randomly( solution, n=14 ) 
        elif choice == 1:
            return self.destroy_1_random_and_neighbours( solution, n=12 )
        elif choice == 2:
            return self.destroy_n_shortest_routes( solution, n=4 ,randomize = False )
        elif choice == 3:
            return self.destroy_n_shortest_routes( solution, n=4, randomize = True )



    def random_construct_method (self,  solution ):
        choice = np.random.choice([True, False])

        if choice:
            new_s =  self.regret(solution)
            print("regret")
        else:
            new_s = self.basic_greedy( solution )

        return new_s
    
    
    
    def late_acceptance(self, late_acceptance_size=5, max_iter = 50, max_no_improvement = 15, start_time  = None, duration = None):
        
        s = self.solution
        
        L = deque()
        
        for i in range(0, late_acceptance_size):
            L.append([s.cost, s])
     
        stuck_counter = 0
        #pbar = tqdm(total = max_iter)
        for i in range(max_iter):
            
                print("Current iteration is {}".format(i))
            
                s = self.random_destroy_method( s )
                print("Destroyed")
                s = self.random_construct_method( s )         
                print("Rebuilt")
                
                #pbar.update(1)
                last_best = L[0]

                if len(last_best[1].routes) > len(s.routes):
                    print("New accepted solution. Number of routes: {}, cost is {:.2f}".format(s.get_n_of_routes(), s.get_cost() ))
                    L.append([s.cost, s])
                    L.popleft()
                    stuck_counter = 0

                elif s.cost<= last_best[0] and len(last_best[1].routes) == len(s.routes):
                    print("New accepted solution. Number of routes: {}, cost is {:.2f}".format(s.get_n_of_routes(), s.get_cost() ))
                    L.append([s.cost, s])
                    L.popleft()
                    stuck_counter = 0
                    
                else:
                    stuck_counter += 1
                    if stuck_counter >= max_no_improvement:
                        break

                if start_time and duration:
                    if time.time()-start_time > duration*60:
                        break
                    

        L = sorted( L, key = lambda t: (t[1].get_n_of_routes(), t[1].cost)  )
        _, best_solution =  L[0]

        return best_solution
                
        
    def basic_greedy(self, solush):
        
        s = copy.deepcopy(solush)        
        while( len(s.unassigned)>0 ):

            
            considered_customers = s.unassigned

            costs_and_all = []

            for customer in considered_customers:

                b_cost, b_route, b_pos = 999999999999999,-1,-1

                for route in s.routes:

                    if customer.demand > route.capacity:
                        continue

                    cost, position = route.find_best_position(customer) ####

                    if position > 0 and cost < b_cost:

                        b_cost = cost
                        b_route = route
                        b_pos = position
                        costs_and_all.append( (b_cost, b_route, b_pos, customer) )

                costs_and_all.append( (b_cost, b_route, b_pos, customer) )

            next_customer = min(costs_and_all, key = lambda t: t[0])####

            if next_customer[2] < 0:

                #print(next_customer)
                closest_to_depot = self.find_closest_to( [s.problem.depot ], considered_customers )

                if closest_to_depot is None:
                    print("Cant find anybody close to depot, error")
                    print( considered_customers)

                new_route = Route( s.problem, [closest_to_depot] )
                #print(new_route)
                s.add_new_route(new_route)
                s.unassigned.remove(closest_to_depot)

            else:

                cost = next_customer[0]
                route = next_customer[1]
                position = next_customer[2]
                customer = next_customer[3]

                route.insert( position, customer, called_from = "kad smjestamo novog"   )          
                s.unassigned.remove(customer)
                s.update_cost()
                
        return s
    
    def regret(self, s, inplace = False, new_routes_auto = False):
        
        if inplace:
            solution = s
        else:
            solution = copy.deepcopy(s)
            
        while len(solution.unassigned)>0:
            
            customer_regrets = []

            for customer in solution.unassigned:

                route_costs = []

                for route in solution.routes:

                    cost, position = self.find_best_position(route, customer)

                    if position > 0:
                        route_costs.append( [cost, route, position] )

                n = len(route_costs)
                if n>1:
                    route_costs = sorted(route_costs, key=lambda x: x[0],
                                         reverse=True)

                    best = route_costs[0]
                    second_best = route_costs[1]
                    regret = second_best[0] - best[0]

                    customer_regrets.append( (regret, customer, best ) )

                elif n == 1:
                    only_possible = route_costs[0]
                    regret = 100000 - only_possible[0]
                    customer_regrets.append( (regret, customer, only_possible ) )

                else:
                    #za ovog customera ne postoji nijedna moguca ruta
                    #ili odma dodat novu rutu i ubacit ga tamo
                    #ili nista... parametar algoritma
                    if new_routes_auto:

                        new_route = Route(solution.problem, [customer])
                        solution.add_new_route(new_route)
                        solution.unassigned.remove(customer)


            if len(customer_regrets)> 0:

                _, next_customer, info = max(customer_regrets, key = lambda t: t[0])

                cost, route, position = info
                route.insert(position, next_customer, called_from = "regret")
                solution.unassigned.remove(next_customer)
                solution.update_cost()

            else:
                self.new_route(solution)
         
        return solution
        
        
    def new_route(self, solution, method = "far"):
        # far, close and random available methods
        unassigned = solution.unassigned
        depo = self.problem.get_depot()
        
        if method == "far":        
            customer_in_route = self.find_furthest_from([depo], unassigned)
        elif method == "close":
            customer_in_route = self.find_closest_to([depo], unassigned)
        elif "random":
            if bool(random.getrandbits(1)):
                customer_in_route = self.find_furthest_from([depo], unassigned)
            else:
                customer_in_route = self.find_closest_to([depo], unassigned)                
            
        new_route = Route( self.solution.problem, [customer_in_route] )
        solution.unassigned.remove(customer_in_route)
        solution.add_new_route(new_route)

        
    def check_cost_customers_route(self, route, customers):
        
        results = []
        #print(route.customers)
        
        for cs in customers:
            
            cost_inc, position = self.find_best_position(route, cs)
            cost_inc -= route.cost 
            results.append([cost_inc, route, position, cs])
        
        return results
        
    def find_closest_to(self, close_to, candidates):
        
        closest_distance = 999999
        closest = None
        
        for candidate in candidates:
            
            summ = 0.0

            for xy in close_to:
                
                distance = self.problem.get_distance( candidate.id, xy.id )
                summ += distance
            
            if summ < closest_distance:
                closest = candidate
                closest_distance = summ
                
        return closest
        
    
    def find_furthest_from(self, further_from, candidates):
        
        furthest_length = -1
        furthest = None
        
        for candidate in candidates:
            
            summ = 0.0
            for xy in further_from:
                
                distance = self.problem.get_distance( candidate.id, xy.id )
                summ += distance
            
            if summ > furthest_length:
                furthest = candidate
                furthest_length = summ
                
        return furthest
        


if __name__ == "__main__":

    from tqdm import tqdm

    random.seed(44)

    pb = Problem("/home/darin/Desktop/ds/Instances/i1.TXT")
    s = Solution(pb)
    opt = Optimizer(s)
    opt.get_initial_solution_routes_seed()
    print(opt.solution)
    opt.get_initial_solution(score_type="regret", k = 15, r = 7)
    print(opt.solution)