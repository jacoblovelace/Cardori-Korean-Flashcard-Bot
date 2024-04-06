import json

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
    
def load_badges_from_json(json_file):
    """
    Load badge data from a JSON file and convert it into a list of Badge objects.
    
    :param json_file (File): JSON file containing data about badges. 
    :return: List of Badge instances.
    """
    with open(json_file, 'r') as file:
        badge_data = json.load(file)
    
    badges = []
    for category, category_badges in badge_data.items():
        for badge_info in category_badges:
            badge = Badge(
                name=badge_info['name'],
                description=badge_info['description'],
                metric=category,
                threshold=badge_info['threshold']
            )
            badges.append(badge)
    
    return badges