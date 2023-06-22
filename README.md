# decentralized-traffic-bottlenecks
Enhancing Traffic Flow Efficiency through an Innovative Decentralized Traffic Control based on Traffic Bottlenecks

There are two main folders: `data` and `code`. 

Inside the `code` folder, there are four independant code parts: 

1. `net_data_builder.py` - analyze the SUMO network file and creates a network analysis json file `input_network_data.json`, that is used later to build the trees. 

2. `tripper.py` - creates the trips file: `vehicles.trips.xml` for each simulation, with vehicles origin, destination and start time.  
	   It can use a random OD or a known probabilty.  

3. `run-multi.py` - the main python projects, which uses SUMO's TraCI package to run multiple SUMO simulation according to the configuration.  
	   It uses the product of the two previous code parts.  

4. `figures_calculations.R` - uses the results of the simulations to create the figures.  
	
Inside the `data` folder, there are four experiments folders with the 20 runs of each experiment smulation per each traffic-light control method.  

There is also an excel file: `results.xlsx`, which summarize all the results together. 
