import jamo
import string
import logging
import re

from nctp.symbols import E_VEF, S_VEF, BREAK, CommonSymbols
from nctp.symbols import EnglishSymbols
from nctp.symbols import KoreanSymbols
from nctp.symbols import JapanesePhnSymbols
from nctp.symbols import SpecialSymbols
from nctp.symbols import ChinesePhnSymbols


EASIA_PUNCS = "。、？！"
# JP/CN puncs: 
KR_SYMBOLS = r'[\uAC00-\uD7AF가-힣]'
EN_SYMBOLS = r'[a-zA-Z]'
JP_SYMBOLS = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]' # 일본어 + 중국어
CN_SYMBOLS = r'[\u4E00-\u9FFF_#]'
SSML_SYMBOLS = S_VEF + E_VEF + BREAK

class Character:
    ALLOWED_SYMBOLS = CommonSymbols().symbols + EnglishSymbols().symbols + string.digits + SpecialSymbols().symbols + EASIA_PUNCS + SSML_SYMBOLS

    def __init__(self, position, value, language=None):
        # symbols which will be eliminated by normalize
        self.position = position
        self.value = value
        self.is_valid = self._validate()
        self.language = language

    def get_character(self):
        return {'position': self.position, 'value': self.value, 'is_valid': self.is_valid}

    def _validate(self):
        if self.value in Character.ALLOWED_SYMBOLS or jamo.is_hangul_char(self.value):
            is_valid = True
        else:
            is_valid = False
        return is_valid

    def __str__(self):
        ret_str = 'position: <{}>, value: <{}>, is_valid: <{}>'.format(self.position, self.value, self.is_valid)
        return ret_str

    def __repr__(self):
        return str(self)

class MLCharacter(Character):
    # ALLOWED_SYMBOLS = list(CommonSymbols().symbols) + list(EnglishSymbols().symbols)

    def __init__(self, position, value, language):
        # symbols which will be eliminated by normalize
        self.position = position
        self.value = value
        self.language = language
        self.is_valid = self._validate()

    def get_character(self):
        return {'position': self.position, 'value': self.value, 'is_valid': self.is_valid}

    def _validate(self):
        if "korean" in str(self.language):
            if self.value in MLCharacter.ALLOWED_SYMBOLS or re.search(KR_SYMBOLS, self.value):
                is_valid = True
            else:
                is_valid = False
        elif "japanese" in str(self.language):
            if self.value in MLCharacter.ALLOWED_SYMBOLS or re.search(JP_SYMBOLS, self.value):
                is_valid = True
            else:
                is_valid = False
        elif "english" in str(self.language):
            if self.value in MLCharacter.ALLOWED_SYMBOLS or re.search(EN_SYMBOLS, self.value):
                is_valid = True
            else:
                is_valid = False
        elif "chinese" in str(self.language):
            if self.value in MLCharacter.ALLOWED_SYMBOLS or re.search(CN_SYMBOLS, self.value):
                is_valid = True
            else:
                is_valid = False
        elif "taiwanese" in str(self.language):
            if self.value in MLCharacter.ALLOWED_SYMBOLS or re.search(CN_SYMBOLS, self.value):
                is_valid = True
            else:
                is_valid = False
        return is_valid

    def __str__(self):
        ret_str = 'position: <{}>, value: <{}>, is_valid: <{}>'.format(self.position, self.value, self.is_valid)
        return ret_str

    def __repr__(self):
        return str(self)