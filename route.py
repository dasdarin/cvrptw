import pandas as pd 
import numpy as np

from customer import Customer
from problem import Problem

class Route:
    
    def __init__(self, problem, customers, get_depot_ = True):
        
        self.problem = problem
        self.depot = self.problem.get_depot()
        self.customers = []
        
        if get_depot_:            
            self.customers = [self.depot, *customers, self.depot]
            
        else:
            self.customers = customers
            
        self.max_capacity = self.problem.get_capacity()
        self.calculate_capacity()
        self.calculate_cost()
        
    def get_problem(self):
        return self.problem
    
    def get_depot(self):
        return self.depot
    
    def get_customers(self):
        return self.customers
    
    def get_max_capacity(self):
        return self.max_capacity
    
    def get_remaining_capacity(self):
        return self.capacity
    
    def get_cost(self):
        return self.cost
    
    def get_n_customers(self):
        return len(self.customers)-2
    
    def is_empty(self):
        return len(self.customers) == 2
    
    def calculate_capacity(self):
        self.capacity = self.max_capacity        
        for customer in self.customers[1:-1]:
            self.capacity -= customer.demand
    
    def calculate_cost(self, update = True):
        total_cost = 0.0
        for departing, arriving in zip(self.customers[:-1], self.customers[1:]):
            travel_distance = self.problem.get_distance(departing.id, arriving.id)
            total_cost +=travel_distance
        if update:
            self.cost = total_cost
        return total_cost
    
    def find_best_position(self, customer): ##cost, position = return
        #put in position
        #check if it's valid        
        #find all possible positions
        
        if customer.get_demand()>self.get_remaining_capacity():
            return 999999999, -1            
        

        n = len(self.customers)
        
        b_position = -1
        b_cost = 999999999
        cost_before = self.calculate_cost(update= False)
        if self.cost != cost_before:
            pass
            #print("ERROR WRONG COST BEFORE AFTER YOU FEEL ME LOOK UP FIND BEST IN ROUTE SEE YA")
        
        for position in range(1,n-1):
        
            trial_route = self.customers[:]
            trial_route.insert(position, customer)            
            trial_route = Route(self.problem, trial_route, get_depot_=False)
            possible, cost = trial_route.is_valid()
            
            if possible and cost < b_cost:
                b_position = position
                b_cost = cost
                
        b_cost = b_cost - cost_before
            
        return b_cost, b_position
        



    def insert(self, position, customer, extra_cost = None, called_from = "dunno"):

        cost_before_real = self.calculate_cost(update=False)
        if not np.isclose(self.cost, cost_before_real, rtol = 1e-05, atol=1e-08):
            print("cost before insertion was wrong, f called from {}".format(called_from) )

        self.customers.insert(position, customer)
        self.capacity -= customer.demand

        if extra_cost:
            self.cost+= extra_cost
        else:
            #update cost

            new_cost = cost_before_real

            prev_customer = self.customers[position-1]
            following_customer = self.customers[position+1]

            new_cost -= self.problem.get_distance(prev_customer.id, following_customer.id)
            new_cost += self.problem.get_distance(customer.id, prev_customer.id)
            new_cost += self.problem.get_distance(customer.id, following_customer.id)

            calc_cost = self.calculate_cost(update = True)
            if not np.isclose(new_cost, calc_cost, rtol = 1e-05, atol=1e-08):
                print(self)
                print("-------\n Cost before inserting {} was {}, cost after wrongly calculated {}, correct one {}".format(customer, cost_before_real, new_cost, calc_cost))


        
    def remove(self, customer, by_id = True):
        
        if by_id:
            customer = Customer.from_id(customer, self.problem)
        
        if customer in self.customers:
            
            self.customers.remove(customer)
            self.capacity += customer.demand
            self.calculate_cost()

            return True
        #print("ERROR TRYING TO REMOVE CUStOMER WHO IS NOT IN THIS ROUTE")
        return False            
        
    def is_valid(self):
        
        time = 0
        cost = 0.0
        capacity = self.problem.capacity #promjenit mozda 
        
        for departing, arriving in zip(self.customers[:-1], self.customers[1:]):
            
            travel_distance = self.problem.get_distance(departing.id, arriving.id)
            start_servicing = np.maximum( arriving.ready_time,
                                         time + np.ceil(travel_distance) )
            if start_servicing > arriving.due_date:
                return (False, -1)
            cost += travel_distance
            time = start_servicing + arriving.service_time
            capacity -= arriving.demand
        if time > self.depot.due_date or capacity < 0:
            return (False, -1)
        return (True, cost)
    
    @staticmethod 
    def route_from_indexes( problem, indexes):
        customers = []
        for index in indexes:
            customer = Customer.from_series( problem.customers.iloc[index] )

            customers.append(customer)
            
        route = Route(problem, customers, get_depot_= False)
        route.calculate_cost()
        return route
    
    def to_str(self):
        time = 0
        output = "0(0)"

        for departing, arriving in zip(self.customers[:-1], self.customers[1:]):
        
            travel_time = np.ceil(self.problem.get_distance(departing.id, arriving.id))
            service_start = np.maximum( arriving.ready_time, time+travel_time )
            service_start = int(service_start)
            time = service_start + arriving.service_time
            
            output += "->{}({})".format(arriving.id, service_start)
        
        return output
    
    def __repr__(self):
         return self.to_str()
        
    def __str__(self):
         return self.to_str()  