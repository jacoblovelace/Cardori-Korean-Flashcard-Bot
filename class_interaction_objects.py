import datetime

class SearchObject:
    
    def __init__(self, id, korean_word, korean_dfn, trans_word, trans_dfn):
        self.id = id
        self.korean_word = korean_word
        self.korean_dfn = korean_dfn
        self.trans_word = trans_word
        self.trans_dfn = trans_dfn
        
    def to_dict(self):
        return vars(self)
    
    
class FlashcardObject:
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
            "last_reviewed": None,
            "interval": self.INITIAL_INTERVAL.total_seconds() // 60,
            "times_studied": 0,
            "learning_phase": True
        }
        
    @classmethod
    def from_dict(cls, flashcard_dict):
        return cls(
            flashcard_dict['id'],
            flashcard_dict['front']['word'],
            flashcard_dict['front']['dfn'],
            flashcard_dict['back']['word'],
            flashcard_dict['back']['dfn'],
            flashcard_dict.get('spaced_repetition', {})
        )
        
    def to_dict(self):
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
    
    def flip(self):
        temp = self.front
        self.front = self.back
        self.back = temp  
        
    def calculate_factor(self, rating):
        flashcard_phase = "Learning" if self.spaced_repetition["learning_phase"] else "Review"
        
        if rating.emoji == '🟥':
            return self.FACTORS["Poor"][flashcard_phase]
        elif rating.emoji == '🟩':
            return self.FACTORS["Good"][flashcard_phase]
        else:
            return self.FACTORS["Okay"][flashcard_phase]
    
    def update_interval(self, factor):
        new_interval = self.spaced_repetition['interval'] * factor
        self.spaced_repetition['interval'] = min(new_interval, int(self.MAX_INTERVAL.total_seconds() / 60))
        self.spaced_repetition['interval'] = max(new_interval, int(self.MIN_INTERVAL.total_seconds() / 60))
    
    def update_learning_phase(self):
        learning_threshold_minutes = int(self.LEARNING_THRESHOLD.total_seconds() / 60)
        self.spaced_repetition["learning_phase"] = self.spaced_repetition['interval'] < learning_threshold_minutes
       
    def process_rating(self, rating):
        factor = self.calculate_factor(rating)
        self.update_interval(factor)
        self.update_learning_phase()
        self.spaced_repetition['last_reviewed'] = datetime.datetime.now().isoformat()
        self.spaced_repetition['times_studied'] += 1
    
