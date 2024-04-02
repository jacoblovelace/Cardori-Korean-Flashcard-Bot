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
    
    def __init__(self, id, korean_word, korean_dfn, trans_word, trans_dfn):
        self.id = id
        self.front = {
            "word": korean_word,
            "dfn": korean_dfn
        }
        self.back = {
            "word": trans_word,
            "dfn": trans_dfn
        }
        
    def to_dict(self):
        return vars(self)
    
    def flip(self):
        temp = self.front
        self.front = self.back
        self.back = temp
