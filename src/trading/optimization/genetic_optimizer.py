import numpy as np
import pandas as pd
import logging
import random
from typing import Dict, List, Tuple, Any, Callable, Optional, Union
import time
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from deap import base, creator, tools, algorithms
    DEAP_AVAILABLE = True
except ImportError:
    logger.warning("DEAP library not available. Genetic optimization will use simple implementation.")
    DEAP_AVAILABLE = False

class GeneticOptimizer:
    """
    Genetic algorithm based optimizer for trading strategy parameters.
    Uses DEAP library if available, otherwise falls back to simpler implementation.
    """
    
    def __init__(self, 
                population_size: int = 50, 
                generations: int = 100,
                parameter_ranges: Dict[str, Tuple] = None,
                fitness_function: Callable = None,
                crossover_probability: float = 0.7,
                mutation_probability: float = 0.2,
                tournament_size: int = 3):
        """
        Initialize the genetic optimizer.
        
        Args:
            population_size: Size of population in each generation
            generations: Number of generations to evolve
            parameter_ranges: Dictionary of parameter names and (min, max) tuples
            fitness_function: Function that evaluates parameters and returns fitness
            crossover_probability: Probability of crossover
            mutation_probability: Probability of mutation
            tournament_size: Tournament selection size
        """
        self.population_size = population_size
        self.generations = generations
        self.crossover_probability = crossover_probability
        self.mutation_probability = mutation_probability
        self.tournament_size = tournament_size
        self.fitness_function = fitness_function
        self.parameter_ranges = parameter_ranges or {
            'rsi_period': (9, 25),
            'macd_fast': (8, 20),
            'macd_slow': (20, 40),
            'ema_short': (5, 20),
            'ema_long': (20, 100),
            'sl_atr': (0.5, 3.0),
            'tp_ratio': (1.0, 4.0)
        }
        
        # Set up the genetic algorithm framework
        if DEAP_AVAILABLE:
            self._setup_deap()
        else:
            logger.info("Using simple genetic algorithm implementation")
            
        # Store results
        self.best_individual = None
        self.best_fitness = -float('inf')
        self.history = []
        
    def _setup_deap(self):
        """Set up DEAP genetic algorithm framework"""
        # Create fitness class that we want to maximize
        if not hasattr(creator, 'FitnessMax'):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
            
        # Create individual class
        if not hasattr(creator, 'Individual'):
            creator.create("Individual", list, fitness=creator.FitnessMax)
        
        # Set up toolbox
        self.toolbox = base.Toolbox()
        
        # Register parameter generators
        for name, (min_val, max_val) in self.parameter_ranges.items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                self.toolbox.register(name, random.randint, min_val, max_val)
            else:
                # For float parameters
                self.toolbox.register(name, random.uniform, min_val, max_val)
        
        # Register individual and population creation
        attrs = tuple(self.parameter_ranges.keys())
        self.toolbox.register("individual", self._create_individual, creator.Individual, attrs)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Register genetic operators
        self.toolbox.register("evaluate", self._evaluate_individual)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self._mutate_individual)
        self.toolbox.register("select", tools.selTournament, tournsize=self.tournament_size)
    
    def _create_individual(self, ind_class, attributes):
        """Create an individual with specified attributes"""
        ind = ind_class()
        for attr in attributes:
            gene = getattr(self.toolbox, attr)()
            ind.append(gene)
        return ind
    
    def _mutate_individual(self, individual):
        """Mutate an individual by randomly changing genes"""
        for i, (name, (min_val, max_val)) in enumerate(self.parameter_ranges.items()):
            # 20% chance to mutate each gene
            if random.random() < 0.2:
                if isinstance(min_val, int) and isinstance(max_val, int):
                    individual[i] = random.randint(min_val, max_val)
                else:
                    individual[i] = random.uniform(min_val, max_val)
        return individual,
    
    def _evaluate_individual(self, individual):
        """Convert individual to parameters dict and evaluate fitness"""
        if not self.fitness_function:
            raise ValueError("No fitness function provided")
            
        # Convert individual to parameters dict
        params = {}
        for i, name in enumerate(self.parameter_ranges.keys()):
            params[name] = individual[i]
            
        # Call fitness function
        try:
            fitness = self.fitness_function(params)
            return (fitness,)
        except Exception as e:
            logger.error(f"Error evaluating individual: {e}")
            return (-float('inf'),)
    
    def _simple_genetic_algorithm(self):
        """Simple genetic algorithm implementation without DEAP"""
        # Initialize population
        population = []
        for _ in range(self.population_size):
            individual = []
            for name, (min_val, max_val) in self.parameter_ranges.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    individual.append(random.randint(min_val, max_val))
                else:
                    individual.append(random.uniform(min_val, max_val))
            population.append(individual)
            
        # Evolve for specified generations
        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                params = {name: individual[i] for i, name in enumerate(self.parameter_ranges.keys())}
                try:
                    fitness = self.fitness_function(params)
                    fitness_scores.append(fitness)
                except Exception as e:
                    logger.error(f"Error evaluating individual: {e}")
                    fitness_scores.append(-float('inf'))
            
            # Find best individual
            best_idx = np.argmax(fitness_scores)
            best_individual = population[best_idx]
            best_fitness = fitness_scores[best_idx]
            
            # Store best of this generation
            self.history.append({
                'generation': generation,
                'best_fitness': best_fitness,
                'best_params': {name: best_individual[i] for i, name in enumerate(self.parameter_ranges.keys())}
            })
            
            # Update overall best
            if best_fitness > self.best_fitness:
                self.best_fitness = best_fitness
                self.best_individual = best_individual.copy()
                
            # Status update
            if generation % 10 == 0:
                logger.info(f"Generation {generation}: Best fitness = {best_fitness:.4f}")
            
            # Create new population
            new_population = []
            
            # Elitism - keep best individual
            new_population.append(best_individual)
            
            # Create rest of population through selection, crossover, mutation
            while len(new_population) < self.population_size:
                # Tournament selection
                parent1_idx = self._tournament_selection(fitness_scores)
                parent2_idx = self._tournament_selection(fitness_scores)
                
                parent1 = population[parent1_idx].copy()
                parent2 = population[parent2_idx].copy()
                
                # Crossover
                if random.random() < self.crossover_probability:
                    child1, child2 = self._simple_crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2
                    
                # Mutation
                if random.random() < self.mutation_probability:
                    self._simple_mutation(child1)
                    
                if random.random() < self.mutation_probability:
                    self._simple_mutation(child2)
                    
                # Add to new population
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            # Replace old population
            population = new_population
            
        # Return best individual found
        return self.best_individual, self.best_fitness
    
    def _tournament_selection(self, fitness_scores, tournament_size=None):
        """Tournament selection of individuals"""
        tournament_size = tournament_size or self.tournament_size
        tournament = random.sample(range(len(fitness_scores)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament]
        return tournament[np.argmax(tournament_fitness)]
    
    def _simple_crossover(self, parent1, parent2):
        """Simple two-point crossover"""
        size = len(parent1)
        point1 = random.randint(0, size - 1)
        point2 = random.randint(point1, size - 1)
        
        child1 = parent1[:point1] + parent2[point1:point2] + parent1[point2:]
        child2 = parent2[:point1] + parent1[point1:point2] + parent2[point2:]
        
        return child1, child2
    
    def _simple_mutation(self, individual):
        """Simple mutation - randomly change genes"""
        for i, (name, (min_val, max_val)) in enumerate(self.parameter_ranges.items()):
            # 20% chance to mutate each gene
            if random.random() < 0.2:
                if isinstance(min_val, int) and isinstance(max_val, int):
                    individual[i] = random.randint(min_val, max_val)
                else:
                    individual[i] = random.uniform(min_val, max_val)
        return individual
    
    def optimize(self) -> Dict[str, Any]:
        """
        Run genetic algorithm optimization.
        
        Returns:
            Dictionary with best parameters and optimization stats
        """
        start_time = time.time()
        
        if not self.fitness_function:
            raise ValueError("No fitness function provided")
        
        if DEAP_AVAILABLE:
            # Run optimization using DEAP
            logger.info("Starting genetic optimization with DEAP")
            
            # Create population
            population = self.toolbox.population(n=self.population_size)
            
            # Track statistics
            stats = tools.Statistics(lambda ind: ind.fitness.values[0])
            stats.register("avg", np.mean)
            stats.register("min", np.min)
            stats.register("max", np.max)
            stats.register("std", np.std)
            
            # Run evolution
            population, logbook = algorithms.eaSimple(
                population, 
                self.toolbox, 
                cxpb=self.crossover_probability, 
                mutpb=self.mutation_probability, 
                ngen=self.generations,
                stats=stats,
                verbose=True
            )
            
            # Get best individual
            best_ind = tools.selBest(population, 1)[0]
            self.best_individual = best_ind
            self.best_fitness = best_ind.fitness.values[0]
            
            # Store optimization history
            for gen, record in enumerate(logbook):
                self.history.append({
                    'generation': gen,
                    'best_fitness': record['max'],
                    'avg_fitness': record['avg'],
                    'std_fitness': record['std']
                })
                
        else:
            # Run simple genetic algorithm implementation
            logger.info("Starting simple genetic optimization")
            self._simple_genetic_algorithm()
        
        # Convert best individual to parameters
        best_params = {}
        for i, name in enumerate(self.parameter_ranges.keys()):
            best_params[name] = self.best_individual[i]
            
            # Round integer parameters
            if isinstance(self.parameter_ranges[name][0], int):
                best_params[name] = int(round(best_params[name]))
        
        # Calculate optimization stats
        elapsed_time = time.time() - start_time
        
        result = {
            'best_params': best_params,
            'best_fitness': self.best_fitness,
            'elapsed_time': elapsed_time,
            'generations': self.generations,
            'population_size': self.population_size,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Genetic optimization completed in {elapsed_time:.2f} seconds")
        logger.info(f"Best fitness: {self.best_fitness:.4f}")
        logger.info(f"Best parameters: {best_params}")
        
        return result
    
    def set_fitness_function(self, fitness_function: Callable):
        """Set the fitness function for evaluation"""
        self.fitness_function = fitness_function
        if DEAP_AVAILABLE:
            self.toolbox.register("evaluate", self._evaluate_individual)
            
    def set_parameter_ranges(self, parameter_ranges: Dict[str, Tuple]):
        """
        Set parameter ranges for optimization.
        
        Args:
            parameter_ranges: Dictionary of parameter names and (min, max) tuples
        """
        self.parameter_ranges = parameter_ranges
        if DEAP_AVAILABLE:
            self._setup_deap()  # Re-setup with new parameter ranges 