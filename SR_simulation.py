import random
import datetime

class FlashcardSimulation:
    LEARNING_THRESHOLD = datetime.timedelta(minutes=60)
    MIN_INTERVAL = datetime.timedelta(minutes=10)
    MAX_INTERVAL = datetime.timedelta(days=7)

    FACTORS = {
        "Good": {"Learning": 3, "Review": 3.5},
        "Okay": {"Learning": 1, "Review": 1},
        "Poor": {"Learning": 0.5, "Review": 0.75}
    }

    def __init__(self):
        self.current_phase = "Learning"
        self.interval = datetime.timedelta(minutes=30)

    def simulate(self, iterations):
        results = []

        for i in range(iterations):
            
            # Choose a random rating
            rating = random.choice(["Good", "Okay", "Poor"])
            
            # Calculate the factor based on the current phase and rating
            factor = self.FACTORS[rating][self.current_phase]
            
            # Append the results to the list
            results.append({
                "Iteration": i + 1,
                "Rating": rating,
                "Phase": self.current_phase,
                "Factor": factor,
                "Interval (minutes)": self.interval.total_seconds() / 60,
                "Interval (hours)": self.interval.total_seconds() / 3600,
                "Interval (days)": self.interval.total_seconds() / (3600 * 24),
                
            })

            # Update the interval based on the factor
            self.interval *= factor
            self.interval = min(self.interval, self.MAX_INTERVAL)
            self.interval = max(self.interval, self.MIN_INTERVAL)

            # Determine the next phase based on the interval
            if self.interval >= self.LEARNING_THRESHOLD:
                self.current_phase = "Review"
            else:
                self.current_phase = "Learning"

        return results

# Instantiate the simulation
simulation = FlashcardSimulation()

# Run the simulation for 10 iterations
results = simulation.simulate(10)

# Print the results
for result in results:
    print(result)
