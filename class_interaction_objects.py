"""
This module defines two classes: `SearchObject` and `FlashcardObject`.

Classes:
    SearchObject: Represents an object used to store a single dictionary search result.
    FlashcardObject: Represents a flashcard object used for spaced repetition learning.

SearchObject Methods:
    __init__: Initializes a SearchObject instance.
    to_dict: Converts a SearchObject instance to a dictionary.

FlashcardObject Methods:
    __init__: Initializes a FlashcardObject instance.
    from_dict: Constructs a FlashcardObject instance from a dictionary.
    to_dict: Converts a FlashcardObject instance to a dictionary.
    invert: Swaps the information on front and back of the flashcard.
    calculate_factor: Calculates the factor based on user rating for the spaced repetition algorithm.
    update_interval: Updates the interval for spaced repetition learning.
    update_learning_phase: Updates the learning phase based on the interval.
    process_rating: Processes the user rating for the flashcard.
"""

import datetime

class SearchObject:
    """
    Represents the resulting data from a dictionary search.
    """
    
    def __init__(self, id, korean_word, korean_dfn, trans_word, trans_dfn):
        """
        Initializes a SearchObject instance with the provided data.

        :param id: The unique identifier of the search object.
        :param korean_word: The Korean word associated with the search object.
        :param korean_dfn: The definition or description of the Korean word.
        :param trans_word: The translated word corresponding to the Korean word.
        :param trans_dfn: The definition or description of the translated word.
        """
        
        self.id = id
        self.korean_word = korean_word
        self.korean_dfn = korean_dfn
        self.trans_word = trans_word
        self.trans_dfn = trans_dfn
        
    def to_dict(self):
        """
        Converts the SearchObject instance to a dictionary.

        :return: A dictionary representation of the SearchObject instance.
        """
        
        return vars(self)
    
    
class FlashcardObject:
    """
    Represents a flashcard object with spaced repetition data.

    Attributes:
        LEARNING_THRESHOLD (datetime.timedelta): The threshold for considering a flashcard in the learning phase.
        MIN_INTERVAL (datetime.timedelta): The minimum interval between reviews.
        MAX_INTERVAL (datetime.timedelta): The maximum interval between reviews.
        INITIAL_INTERVAL (datetime.timedelta): The initial interval for a flashcard.
        FACTORS (dict): Dictionary containing factors for different rating levels.
            Keys: Rating levels ('Good', 'Okay', 'Poor')
            Values: Dictionaries containing factors for learning and review phases.
                Keys: Phases ('Learning', 'Review')
                Values: Factors for learning and review phases.
        
    Methods:
        __init__: Initializes a FlashcardObject instance.
        from_dict: Creates a FlashcardObject instance from a dictionary.
        to_dict: Converts the FlashcardObject instance to a dictionary.
        invert: Inverts the front and back sides of the flashcard.
        calculate_factor: Calculates the factor based on the user's rating.
        update_interval: Updates the review interval based on the calculated factor.
        update_learning_phase: Updates the learning phase based on the interval.
        process_rating: Processes the user's rating and updates spaced repetition data.
    """
    
    LEARNING_THRESHOLD = datetime.timedelta(minutes=60)
    MIN_INTERVAL = datetime.timedelta(minutes=10)
    MAX_INTERVAL = datetime.timedelta(days=30)
    INITIAL_INTERVAL = datetime.timedelta(minutes=10)
    
    FACTORS = {
        "Good": {"Learning": 3, "Review": 3.5},
        "Okay": {"Learning": 1, "Review": 1},
        "Poor": {"Learning": 0.5, "Review": 0.75}
    }
    
    def __init__(self, id, korean_word, korean_dfn, trans_word, trans_dfn, spaced_repetition=None):
        """
        Initializes a FlashcardObject instance.

        :param id: The unique identifier of the flashcard.
        :param korean_word: The Korean word on the front side of the flashcard.
        :param korean_dfn: The definition or description of the Korean word.
        :param trans_word: The translated word on the back side of the flashcard.
        :param trans_dfn: The definition or description of the translated word.
        :param spaced_repetition: Optional. Dictionary containing spaced repetition data.
        """
        
        self.id = id
        self.front = {
            "word": korean_word,
            "dfn": korean_dfn
        }
        self.back = {
            "word": trans_word,
            "dfn": trans_dfn
        }
        self.spaced_repetition = spaced_repetition or {
            "to_review": False,
            "last_reviewed": None,
            "last_reminded": None,
            "interval": self.INITIAL_INTERVAL.total_seconds() // 60,
            "learning_phase": True,
            "times_studied": 0
        }
        
    @classmethod
    def from_dict(cls, flashcard_dict):
        """
        Creates a FlashcardObject instance from a dictionary.

        :param flashcard_dict: Dictionary containing flashcard data.
        :return: FlashcardObject instance.
        """
        
        return cls(
            flashcard_dict['id'],
            flashcard_dict['front']['word'],
            flashcard_dict['front']['dfn'],
            flashcard_dict['back']['word'],
            flashcard_dict['back']['dfn'],
            flashcard_dict.get('spaced_repetition', {})
        )
        
    def to_dict(self):
        """
        Converts the FlashcardObject instance to a dictionary.

        :return: Dictionary representation of the FlashcardObject instance.
        """
        
        # Create a copy of the spaced_repetition dictionary
        spaced_repetition_copy = self.spaced_repetition.copy()

        # Convert last_reviewed datetime to string format
        if (spaced_repetition_copy["last_reviewed"] is not None) and (not isinstance(spaced_repetition_copy["last_reviewed"], str)):
            spaced_repetition_copy["last_reviewed"] = spaced_repetition_copy["last_reviewed"].isoformat()
            
        spaced_repetition_copy["interval"] = int(spaced_repetition_copy["interval"])

        # Return the dictionary representation of the FlashcardObject
        return {
            "id": self.id,
            "front": self.front,
            "back": self.back,
            "spaced_repetition": spaced_repetition_copy
        }
    
    def invert(self):
        """
        Inverts the front and back sides of the flashcard.
        """
        
        temp = self.front
        self.front = self.back
        self.back = temp  
        
    def calculate_points(self, rating):
        """
        Calculates the points earned based on the user's rating.

        :param rating: User's rating.
        :return: Points earned from rating.
        """
        
        rating_to_points = {
            '🟩': 3,
            '🟨': 1,
            '🟥': 0
        }
        
        return rating_to_points[rating.emoji]
        
    def calculate_factor(self, rating):
        """
        Calculates the factor based on the user's rating.

        :param rating: User's rating.
        :return: Factor for spaced repetition.
        """
        flashcard_phase = "Learning" if self.spaced_repetition["learning_phase"] else "Review"
        
        rating_to_factor = {
            '🟩': self.FACTORS["Good"][flashcard_phase],
            '🟨': self.FACTORS["Okay"][flashcard_phase],
            '🟥': self.FACTORS["Poor"][flashcard_phase]
        }
        
        return rating_to_factor[rating.emoji]
        
    
    def update_interval(self, factor):
        """
        Updates the interval based on the factor.

        :param factor: The interval factor.
        """
        
        new_interval = int(self.spaced_repetition['interval']) * factor
        self.spaced_repetition['interval'] = min(new_interval, int(self.MAX_INTERVAL.total_seconds() / 60))
        self.spaced_repetition['interval'] = max(new_interval, int(self.MIN_INTERVAL.total_seconds() / 60))
    
    def update_learning_phase(self):
        """
        Updates the learning phase based on the interval threshold.

        """
        
        learning_threshold_minutes = int(self.LEARNING_THRESHOLD.total_seconds() / 60)
        self.spaced_repetition["learning_phase"] = self.spaced_repetition['interval'] < learning_threshold_minutes
       
    def process_rating(self, rating):
        """
        Processes the rating given to the flashcard.

        :param rating: The rating given to the flashcard.
        """
        
        factor = self.calculate_factor(rating)
        self.update_interval(factor)
        self.update_learning_phase()
        self.spaced_repetition['to_review'] = False
        self.spaced_repetition['last_reviewed'] = datetime.datetime.now().isoformat()
        self.spaced_repetition['times_studied'] += 1
        
        points_earned = self.calculate_points(rating)
        
        return points_earned
    
