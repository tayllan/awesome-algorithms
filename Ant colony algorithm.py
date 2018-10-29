from threading import Thread

class ant_colony:
	class ant(Thread):
		def __init__(self, init_location, possible_locations, pheromone_map, distance_callback, alpha, beta, first_pass=False):
			"""
			initialized an ant, to traverse the map
			init_location -> marks where in the map that the ant starts
			possible_locations -> a list of possible nodes the ant can go to
				when used internally, gives a list of possible locations the ant can traverse to _minus those nodes already visited_
			pheromone_map -> map of pheromone values for each traversal between each node
			distance_callback -> is a function to calculate the distance between two nodes
			alpha -> a parameter from the ACO algorithm to control the influence of the amount of pheromone when making a choice in _pick_path()
			beta -> a parameters from ACO that controls the influence of the distance to the next node in _pick_path()
			first_pass -> if this is a first pass on a map, then do some steps differently, noted in methods below
			
			route -> a list that is updated with the labels of the nodes that the ant has traversed
			pheromone_trail -> a list of pheromone amounts deposited along the ants trail, maps to each traversal in route
			distance_traveled -> total distance tranveled along the steps in route
			location -> marks where the ant currently is
			tour_complete -> flag to indicate the ant has completed its traversal
				used by get_route() and get_distance_traveled()
			"""
			Thread.__init__(self)
			
			self.init_location = init_location
			self.possible_locations = possible_locations			
			self.route = []
			self.distance_traveled = 0.0
			self.location = init_location
			self.pheromone_map = pheromone_map
			self.distance_callback = distance_callback
			self.alpha = alpha
			self.beta = beta
			self.first_pass = first_pass
			
			#append start location to route, before doing random walk
			self._update_route(init_location)
			
			self.tour_complete = False
			
		def run(self):
			"""
			until self.possible_locations is empty (the ant has visited all nodes)
				_pick_path() to find a next node to traverse to
				_traverse() to:
					_update_route() (to show latest traversal)
					_update_distance_traveled() (after traversal)
			return the ants route and its distance, for use in ant_colony:
				do pheromone updates
				check for new possible optimal solution with this ants latest tour
			"""
			while self.possible_locations:
				next = self._pick_path()
				self._traverse(self.location, next)
				
			self.tour_complete = True
		
		def _pick_path(self):
			"""
			source: https://en.wikipedia.org/wiki/Ant_colony_optimization_algorithms#Edge_selection
			implements the path selection algorithm of ACO
			calculate the attractiveness of each possible transition from the current location
			then randomly choose a next path, based on its attractiveness
			"""
			#on the first pass (no pheromones), then we can just choice() to find the next one
			if self.first_pass:
				import random
				return random.choice(self.possible_locations)
			
			attractiveness = dict()
			sum_total = 0.0
			#for each possible location, find its attractiveness (it's (pheromone amount)*1/distance [tau*eta, from the algortihm])
			#sum all attrativeness amounts for calculating probability of each route in the next step
			for possible_next_location in self.possible_locations:
				#NOTE: do all calculations as float, otherwise we get integer division at times for really hard to track down bugs
				pheromone_amount = float(self.pheromone_map[self.location][possible_next_location])
				distance = float(self.distance_callback(self.location, possible_next_location))
				
				#tau^alpha * eta^beta
				attractiveness[possible_next_location] = pow(pheromone_amount, self.alpha)*pow(1/distance, self.beta)
				sum_total += attractiveness[possible_next_location]
			
			#it is possible to have small values for pheromone amount / distance, such that with rounding errors this is equal to zero
			#rare, but handle when it happens
			if sum_total == 0.0:
				#increment all zero's, such that they are the smallest non-zero values supported by the system
				#source: http://stackoverflow.com/a/10426033/5343977
				def next_up(x):
					import math
					import struct
					# NaNs and positive infinity map to themselves.
					if math.isnan(x) or (math.isinf(x) and x > 0):
						return x

					# 0.0 and -0.0 both map to the smallest +ve float.
					if x == 0.0:
						x = 0.0

					n = struct.unpack('<q', struct.pack('<d', x))[0]
					
					if n >= 0:
						n += 1
					else:
						n -= 1
					return struct.unpack('<d', struct.pack('<q', n))[0]
					
				for key in attractiveness:
					attractiveness[key] = next_up(attractiveness[key])
				sum_total = next_up(sum_total)
			
			#cumulative probability behavior, inspired by: http://stackoverflow.com/a/3679747/5343977
			#randomly choose the next path
			import random
			toss = random.random()
					
			cummulative = 0
			for possible_next_location in attractiveness:
				weight = (attractiveness[possible_next_location] / sum_total)
				if toss <= weight + cummulative:
					return possible_next_location
				cummulative += weight
		
		def _traverse(self, start, end):
			"""
			_update_route() to show new traversal
			_update_distance_traveled() to record new distance traveled
			self.location update to new location
			called from run()
			"""
			self._update_route(end)
			self._update_distance_traveled(start, end)
			self.location = end
		
		def _update_route(self, new):
			"""
			add new node to self.route
			remove new node form self.possible_location
			called from _traverse() & __init__()
			"""
			self.route.append(new)
			self.possible_locations.remove(new)
			
		def _update_distance_traveled(self, start, end):
			"""
			use self.distance_callback to update self.distance_traveled
			"""
			self.distance_traveled += float(self.distance_callback(start, end))
	
		def get_route(self):
			if self.tour_complete:
				return self.route
			return None
			
		def get_distance_traveled(self):
			if self.tour_complete:
				return self.distance_traveled
			return None
		
	def __init__(self, nodes, distance_callback, start=None, ant_count=50, alpha=.5, beta=1.2,  pheromone_evaporation_coefficient=.40, pheromone_constant=1000.0, iterations=80):
		"""
		initializes an ant colony (houses a number of worker ants that will traverse a map to find an optimal route as per ACO [Ant Colony Optimization])
		source: https://en.wikipedia.org/wiki/Ant_colony_optimization_algorithms
		
		nodes -> is assumed to be a dict() mapping node ids to values 
			that are understandable by distance_callback
			
		distance_callback -> is assumed to take a pair of coordinates and return the distance between them
			populated into distance_matrix on each call to get_distance()
			
		start -> if set, then is assumed to be the node where all ants start their traversal
			if unset, then assumed to be the first key of nodes when sorted()
		
		distance_matrix -> holds values of distances calculated between nodes
			populated on demand by _get_distance()
		
		pheromone_map -> holds final values of pheromones
			used by ants to determine traversals
			pheromone dissipation happens to these values first, before adding pheromone values from the ants during their traversal
			(in ant_updated_pheromone_map)
			
		ant_updated_pheromone_map -> a matrix to hold the pheromone values that the ants lay down
			not used to dissipate, values from here are added to pheromone_map after dissipation step
			(reset for each traversal)
			
		alpha -> a parameter from the ACO algorithm to control the influence of the amount of pheromone when an ant makes a choice
		
		beta -> a parameters from ACO that controls the influence of the distance to the next node in ant choice making
		
		pheromone_constant -> a parameter used in depositing pheromones on the map (Q in ACO algorithm)
			used by _update_pheromone_map()
			
		pheromone_evaporation_coefficient -> a parameter used in removing pheromone values from the pheromone_map (rho in ACO algorithm)
			used by _update_pheromone_map()
		
		ants -> holds worker ants
			they traverse the map as per ACO
			notable properties:
				total distance traveled
				route
			
		first_pass -> flags a first pass for the ants, which triggers unique behavior
		
		iterations -> how many iterations to let the ants traverse the map
		
		shortest_distance -> the shortest distance seen from an ant traversal
		
		shortets_path_seen -> the shortest path seen from a traversal (shortest_distance is the distance along this path)
		"""
		#nodes
		if type(nodes) is not dict:
			raise TypeError("nodes must be dict")
		
		if len(nodes) < 1:
			raise ValueError("there must be at least one node in dict nodes")
		
		#create internal mapping and mapping for return to caller
		self.id_to_key, self.nodes = self._init_nodes(nodes)
		#create matrix to hold distance calculations between nodes
		self.distance_matrix = self._init_matrix(len(nodes))
		#create matrix for master pheromone map, that records pheromone amounts along routes
		self.pheromone_map = self._init_matrix(len(nodes))
		#create a matrix for ants to add their pheromones to, before adding those to pheromone_map during the update_pheromone_map step
		self.ant_updated_pheromone_map = self._init_matrix(len(nodes))
		
		#distance_callback
		if not callable(distance_callback):
			raise TypeError("distance_callback is not callable, should be method")
			
		self.distance_callback = distance_callback
		
		#start
		if start is None:
			self.start = 0
		else:
			self.start = None
			#init start to internal id of node id passed
			for key, value in self.id_to_key.items():
				if value == start:
					self.start = key
			
			#if we didn't find a key in the nodes passed in, then raise
			if self.start is None:
				raise KeyError("Key: " + str(start) + " not found in the nodes dict passed.")
		
		#ant_count
		if type(ant_count) is not int:
			raise TypeError("ant_count must be int")
			
		if ant_count < 1:
			raise ValueError("ant_count must be >= 1")
		
		self.ant_count = ant_count
		
		#alpha	
		if (type(alpha) is not int) and type(alpha) is not float:
			raise TypeError("alpha must be int or float")
		
		if alpha < 0:
			raise ValueError("alpha must be >= 0")
		
		self.alpha = float(alpha)
		
		#beta
		if (type(beta) is not int) and type(beta) is not float:
			raise TypeError("beta must be int or float")
			
		if beta < 1:
			raise ValueError("beta must be >= 1")
			
		self.beta = float(beta)
		
		#pheromone_evaporation_coefficient
		if (type(pheromone_evaporation_coefficient) is not int) and type(pheromone_evaporation_coefficient) is not float:
			raise TypeError("pheromone_evaporation_coefficient must be int or float")
		
		self.pheromone_evaporation_coefficient = float(pheromone_evaporation_coefficient)
		
		#pheromone_constant
		if (type(pheromone_constant) is not int) and type(pheromone_constant) is not float:
			raise TypeError("pheromone_constant must be int or float")
		
		self.pheromone_constant = float(pheromone_constant)
		
		#iterations
		if (type(iterations) is not int):
			raise TypeError("iterations must be int")
		
		if iterations < 0:
			raise ValueError("iterations must be >= 0")
			
		self.iterations = iterations
		
		#other internal variable init
		self.first_pass = True
		self.ants = self._init_ants(self.start)
		self.shortest_distance = None
		self.shortest_path_seen = None
		
	def _get_distance(self, start, end):
		"""
		uses the distance_callback to return the distance between nodes
		if a distance has not been calculated before, then it is populated in distance_matrix and returned
		if a distance has been called before, then its value is returned from distance_matrix
		"""
		if not self.distance_matrix[start][end]:
			distance = self.distance_callback(self.nodes[start], self.nodes[end])
			
			if (type(distance) is not int) and (type(distance) is not float):
				raise TypeError("distance_callback should return either int or float, saw: "+ str(type(distance)))
			
			self.distance_matrix[start][end] = float(distance)
			return distance
		return self.distance_matrix[start][end]
		
	def _init_nodes(self, nodes):
		"""
		create a mapping of internal id numbers (0 .. n) to the keys in the nodes passed 
		create a mapping of the id's to the values of nodes
		we use id_to_key to return the route in the node names the caller expects in mainloop()
		"""
		id_to_key = dict()
		id_to_values = dict()
		
		id = 0
		for key in sorted(nodes.keys()):
			id_to_key[id] = key
			id_to_values[id] = nodes[key]
			id += 1
			
		return id_to_key, id_to_values
		
	def _init_matrix(self, size, value=0.0):
		"""
		setup a matrix NxN (where n = size)
		used in both self.distance_matrix and self.pheromone_map
		as they require identical matrixes besides which value to initialize to
		"""
		ret = []
		for row in range(size):
			ret.append([float(value) for x in range(size)])
		return ret
	
	def _init_ants(self, start):
		"""
		on first pass:
			create a number of ant objects
		on subsequent passes, just call __init__ on each to reset them
		by default, all ants start at the first node, 0
		as per problem description: https://www.codeeval.com/open_challenges/90/
		"""
		#allocate new ants on the first pass
		if self.first_pass:
			return [self.ant(start, self.nodes.keys(), self.pheromone_map, self._get_distance,
				self.alpha, self.beta, first_pass=True) for x in range(self.ant_count)]
		#else, just reset them to use on another pass
		for ant in self.ants:
			ant.__init__(start, self.nodes.keys(), self.pheromone_map, self._get_distance, self.alpha, self.beta)
	
	def _update_pheromone_map(self):
		"""
		1)	Update self.pheromone_map by decaying values contained therein via the ACO algorithm
		2)	Add pheromone_values from all ants from ant_updated_pheromone_map
		called by:
			mainloop()
			(after all ants have traveresed)
		"""
		#always a square matrix
		for start in range(len(self.pheromone_map)):
			for end in range(len(self.pheromone_map)):
				#decay the pheromone value at this location
				#tau_xy <- (1-rho)*tau_xy	(ACO)
				self.pheromone_map[start][end] = (1-self.pheromone_evaporation_coefficient)*self.pheromone_map[start][end]
				
				#then add all contributions to this location for each ant that travered it
				#(ACO)
				#tau_xy <- tau_xy + delta tau_xy_k
				#	delta tau_xy_k = Q / L_k
				self.pheromone_map[start][end] += self.ant_updated_pheromone_map[start][end]
	
	def _populate_ant_updated_pheromone_map(self, ant):
		"""
		given an ant, populate ant_updated_pheromone_map with pheromone values according to ACO
		along the ant's route
		called from:
			mainloop()
			( before _update_pheromone_map() )
		"""
		route = ant.get_route()
		for i in range(len(route)-1):
			#find the pheromone over the route the ant traversed
			current_pheromone_value = float(self.ant_updated_pheromone_map[route[i]][route[i+1]])
		
			#update the pheromone along that section of the route
			#(ACO)
			#	delta tau_xy_k = Q / L_k
			new_pheromone_value = self.pheromone_constant/ant.get_distance_traveled()
			
			self.ant_updated_pheromone_map[route[i]][route[i+1]] = current_pheromone_value + new_pheromone_value
			self.ant_updated_pheromone_map[route[i+1]][route[i]] = current_pheromone_value + new_pheromone_value
		
	def mainloop(self):
		"""
		Runs the worker ants, collects their returns and updates the pheromone map with pheromone values from workers
			calls:
			_update_pheromones()
			ant.run()
		runs the simulation self.iterations times
		"""
		
		for _ in range(self.iterations):
			#start the multi-threaded ants, calls ant.run() in a new thread
			for ant in self.ants:
				ant.start()
			
			#source: http://stackoverflow.com/a/11968818/5343977
			#wait until the ants are finished, before moving on to modifying shared resources
			for ant in self.ants:
				ant.join()
			
			for ant in self.ants:	
				#update ant_updated_pheromone_map with this ant's constribution of pheromones along its route
				self._populate_ant_updated_pheromone_map(ant)
				
				#if we haven't seen any paths yet, then populate for comparisons later
				if not self.shortest_distance:
					self.shortest_distance = ant.get_distance_traveled()
				
				if not self.shortest_path_seen:
					self.shortest_path_seen = ant.get_route()
					
				#if we see a shorter path, then save for return
				if ant.get_distance_traveled() < self.shortest_distance:
					self.shortest_distance = ant.get_distance_traveled()
					self.shortest_path_seen = ant.get_route()
			
			#decay current pheromone values and add all pheromone values we saw during traversal (from ant_updated_pheromone_map)
			self._update_pheromone_map()
			
			#flag that we finished the first pass of the ants traversal
			if self.first_pass:
				self.first_pass = False
			
			#reset all ants to default for the next iteration
			self._init_ants(self.start)
			
			#reset ant_updated_pheromone_map to record pheromones for ants on next pass
			self.ant_updated_pheromone_map = self._init_matrix(len(self.nodes), value=0)
		
		#translate shortest path back into callers node id's
		ret = []
		for id in self.shortest_path_seen:
			ret.append(self.id_to_key[id])
		
		return ret
