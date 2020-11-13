import pandas as pd 
import numpy as np

class Customer:
    def __init__(self, id, x, y, demand, ready_time, due_date, service_time):
        self.id = int(id)
        self.x = x
        self.y = y
        self.demand = demand
        self.ready_time = ready_time
        self.due_date = due_date
        self.service_time = service_time
        
    @staticmethod    
    def from_series(values):
        return Customer(  values["customer"], values["X"], values["Y"], values["DEMAND"],
                        values["READY TIME"], values["DUE DATE"], values["SERVICE TIME"]  )
    @staticmethod
    def from_id(id, pb):
        cs = pb.customers.iloc[id]
        return Customer(  cs["customer"], cs["X"], cs["Y"], cs["DEMAND"], cs["READY TIME"],
                    cs["DUE DATE"], cs["SERVICE TIME"]  )
    
    def __eq__(self, other):
        if self.id == other.id:
            return True
        return False
    
    def __repr__(self):
        return str(self.id)
    
    def __str__(self):
        return str(self.id)
    
    def get_demand(self):
        return self.demand