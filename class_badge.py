class Badge:
    def __init__(self, name, description, metric, threshold):
        self.name = name 
        self.description = description  
        self.metric = metric 
        self.threshold = threshold 
        self.completed = False 

    def complete(self):
        self.completed = True

    def check_completion(self, user_progress):
        """
        Method to check if the badge has been completed based on user progress data.
        """
        
        # check if the user progress metric meets or exceeds the threshold value
        return user_progress.get(self.metric, 0) >= self.threshold