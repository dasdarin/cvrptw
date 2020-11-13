import pandas as pd 
import numpy as np
import sys

from customer import Customer

from scipy.spatial.distance import pdist, squareform


class Problem:
    def __init__(self, source_file):
        
        with open(source_file) as f:
            
            content = f.readlines()
        
        vehicle_capacity_line = content[2].split()
        
        self.n_vehicles = int(vehicle_capacity_line[0])
        self.capacity = int(vehicle_capacity_line[1])        
        
        customers = content[7:]
        customers = np.array([x.split() for x in customers],dtype=float)
        column_names = ["customer",'X', 'Y', 'DEMAND', 'READY TIME', 'DUE DATE',
       'SERVICE TIME']
        customers = pd.DataFrame(customers, columns = column_names)
        customers.customer = customers.customer.astype(int)
        
        distances = pdist( customers[["X","Y"]] ,"euclidean")
        distances = pd.DataFrame(squareform(distances))
        
        time_distances = pdist( customers[['READY TIME', 'DUE DATE']] ,"euclidean")
        time_distances = pd.DataFrame(squareform(time_distances))
        
        
        self.customers = customers
        self.distances = distances
        self.time_distances = time_distances
        
        self.depot = Customer.from_series(self.customers.iloc[0])
        
    def get_neighbours(self, neighbour, n, a=1.0, b=1.0, g=1.0):
        
        dist = self.distances.drop(columns = [0, neighbour])
        time = self.distances.drop(columns = [0, neighbour])
        n_demand = self.customers.iloc[neighbour].DEMAND
        demands = self.customers.drop(index = [0, neighbour]).DEMAND
        demands = (n_demand - demands).apply(abs)

        similarity = a*dist.iloc[neighbour] + b*time.iloc[neighbour] + g*demands
        
        return similarity.sort_values()[:n].index.values        
        
    def get_depot(self):
        return self.depot
        
    def get_n_of_customers(self):
        return len(self.customers)
    
    def get_distance(self, customer_a, customber_b):
        return self.distances.iloc[customer_a][customber_b]
    
    def get_capacity(self):
        return self.capacity
    
    def get_n_of_vehicles(self):
        return self.n_vehicles
    
    def get_total_demand(self):
        return self.customers.DEMAND.sum() #pb.customers.DEMAND.sum()