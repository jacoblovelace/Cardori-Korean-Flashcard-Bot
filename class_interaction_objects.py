class SearchObject:
    
    def __init__(self, id, korean_word, korean_dfn, trans_word, trans_dfn) -> None:
        self.id = id
        self.korean_word = korean_word
        self.korean_dfn = korean_dfn
        self.trans_word = trans_word
        self.trans_dfn = trans_dfn
        
    def to_dict(self):
        return vars(self)
    
    
class FlashcardObject:
    
    def __init__(self, id, korean_word, korean_dfn, trans_word, trans_dfn) -> None:
        self.id = id
        self.korean_word = korean_word
        self.korean_dfn = korean_dfn
        self.trans_word = trans_word
        self.trans_dfn = trans_dfn
        
    def to_dict(self):
        return vars(self)
