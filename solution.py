import pandas as pd 
import numpy as np


from customer import Customer
from problem import Problem
from route import Route


class Solution:
    def __init__(self, problem, routes = None):
        
        self.problem = problem
        self.unassigned = []
        
        if routes == None:
            self.routes = []
            self.unassigned = self.put_customers_to_unassigned()
            self.cost = 0.0
        else:
            self.routes = routes
            self.update_cost()
            
    def get_problem(self):
        return self.problem
    
    def get_unassigned(self):
        return self.unassigned
    
    def get_routes(self):
        return self.routes
    
    def get_cost(self):
        return self.cost

    def get_n_of_routes(self):
        return len(self.routes)
    
    def get_n_of_assigned_customers(self):
        
        return sum([c.get_n_customers() for c in self.routes])
        
    def put_customers_to_unassigned(self):
        
        customers = [] 
        customers_values = self.problem.customers[1:].iterrows()
        for _, cs in customers_values:
            customers.append( Customer.from_series(cs) )
        return customers

    def update_cost(self, update = True):
        cost = 0.0
        for route in self.routes:
            cost += route.calculate_cost()
        if update:
            self.cost = cost
        return cost
    
    def add_new_route(self, route):
        self.routes.append(route)
        self.cost += route.get_cost()
        #self.update_cost()
        
    def remove_route(self, route):
        self.routes.remove(route)
        self.cost -= route.get_cost()
        #self.update_cost()
        
    def remove_from_unassigned(self, cs):
        self.unassigned.remove(cs)        
  
    def to_str(self):
        
        number_routes = len(self.routes)
        output = ""
        output += str(number_routes) +"\n"
        route_number = 1

        self.update_cost()
        calc_cost = self.update_cost(update=False)
        if self.cost != calc_cost:
            print("Invalid cost in solution")

        for route in self.routes:
            
            route_str = route.to_str()
            output += "{}: {}\n".format(str(route_number), route_str )
            route_number += 1
        output += "{:.2f}".format(self.cost)
        return output

    def __repr__(self):
         return self.to_str()
        
    def __str__(self):
         return self.to_str()
        
    def save_to_file(self, file_location):
        
        with open(file_location, "w") as out:
            out.write(self.to_str())
            out.close() 