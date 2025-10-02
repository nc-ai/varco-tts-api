from nctp.korean import KR_SYMBOLS
from nctp.korean import KR_IPA_SYMBOLS
from nctp.english import EN_SYMBOLS
from nctp.english import EN_PHN_SYMBOLS
from nctp.english import EN_IPA_SYMBOLS
from nctp.japanese import JPN_SYMBOLS
from nctp.chinese import CHI_SYMBOLS
from nctp.taiwanese import TWN_SYMBOLS

import logging
import jamo
from typing import Union, List, Dict

PAD = '_'
BOS = '🔊'
EOS = '🚩'
PUNC = '.,\'?!-~🐢'  # parsing에서 쓰이는 문자 : '<', '-', '&', ':', '>', '@'
SPACE = ' '
SYMBOLS = PAD + BOS + EOS + PUNC + SPACE
S_GTO = '😦'
E_GTO = '😧'
S_STU = '😐'
E_STU = '😑'
S_LAH = '😃'
E_LAH = '😄'
S_SIH = '😔'
E_SIH = '😞'
S_SCR = '😫'
E_SCR = '😱'
S_HAA = '😤'
E_HAA = '😬'
S_CRY = '😭'
E_CRY = '😢'
S_VEF = '🍊'
E_VEF = '🍋'
BREAK = '🤐'
S_VEF_IDX = -2
E_VEF_IDX = -3
BREAK_IDX = -4
# 😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉🐢


ERR_SYMBOL = -1
GRUUT_SPECIAL_CHAR = "‖"


class BaseSymbols(object):
    def __init__(self):
        self._symbols = None
        self._offset = None

    @property
    def symbols(self):
        return self._symbols

    @property
    def sym2num(self):
        sym2num = {}
        for i, s in enumerate(self._symbols):
            sym2num[s] = self._offset + i
        return sym2num

    @property
    def num2sym(self):
        num2sym = {}
        for i, s in enumerate(self._symbols):
            num2sym[self._offset + i] = s
        return num2sym


class KoreanSymbols(BaseSymbols):
    def __init__(self):
        self._symbols = KR_SYMBOLS
        self._offset = len(CommonSymbols().sym2num.keys()) + len(SpecialSymbols().sym2num.keys())


class KoreanPhnSymbols(BaseSymbols):
    def __init__(self, category="ipa"):
        self.category = category
        self._symbols, self._offset = self._set_category()

    def _set_category(self):
        if self.category == "ipa":
            symbols = KR_IPA_SYMBOLS
            offset = len(CommonSymbols().sym2num.keys()) + len(SpecialSymbols().sym2num.keys())
        else:
            logging.info(f"This phoneme category of english is not allowed : {self.category}.")
            assert NotImplementedError
        return symbols, offset


class EnglishSymbols(BaseSymbols):
    def __init__(self):
        self._symbols = EN_SYMBOLS
        self._offset = len(CommonSymbols().sym2num.keys()) + len(SpecialSymbols().sym2num.keys())


class EnglishPhnSymbols(BaseSymbols):
    def __init__(self, category="arpabet"):
        self.category = category
        self._symbols, self._offset = self._set_category()

    def _set_category(self):
        if self.category == "arpabet":
            symbols = self._valid_checker(EN_PHN_SYMBOLS)
            offset = len(CommonSymbols().sym2num.keys()) + len(SpecialSymbols().sym2num.keys())
        elif self.category == "ipa":
            symbols = EN_IPA_SYMBOLS
            offset = len(CommonSymbols().sym2num.keys()) + len(SpecialSymbols().sym2num.keys())
        else:
            logging.info(f"This phoneme category of english is not allowed : {self.category}.")
            assert NotImplementedError
        return symbols, offset

    def _valid_checker(self, ephn_symbols):
        s_ephn = sorted(ephn_symbols)
        if ephn_symbols != s_ephn:
            logging.error("The order of ENG Phn in json file and the alphabetical order are different.")
        return s_ephn


class JapanesePhnSymbols(BaseSymbols):
    def __init__(self):
        self._symbols = JPN_SYMBOLS
        self._offset = len(CommonSymbols().sym2num.keys()) + len(SpecialSymbols().sym2num.keys())

    def _valid_checker(self, jphn_symbols):
        s_jphn = sorted(jphn_symbols)
        if jphn_symbols != s_jphn:
            logging.error("The order of JPN Phn in json file and the alphabetical order are different.")
        return s_jphn


class ChinesePhnSymbols(BaseSymbols):
    def __init__(self):
        self._symbols = CHI_SYMBOLS
        self._offset = len(CommonSymbols().sym2num.keys()) + len(SpecialSymbols().sym2num.keys())

    def _valid_checker(self, cphn_symbols):
        s_cphn = sorted(cphn_symbols)
        if cphn_symbols != s_cphn:
            logging.error("The order of CHI Phn in json file and the alphabetical order are different.")
        return s_cphn
    

class TaiwanesePhnSymbols(BaseSymbols):
    def __init__(self):
        self._symbols = TWN_SYMBOLS
        self._offset = len(CommonSymbols().sym2num.keys()) + len(SpecialSymbols().sym2num.keys())

    def _valid_checker(self, tphn_symbols):
        s_tphn = sorted(tphn_symbols)
        if tphn_symbols != s_tphn:
            logging.error("The order of CHI Phn in json file and the alphabetical order are different.")
        return s_tphn


class CommonSymbols(BaseSymbols):
    # NOTE: UPDATED BY MKYU (24.02.19)
    """ 언어와 무관하게 공통적으로 사용되는 symbol들을 지니는 class
        PAD = '_' : 0
        BOS = '始' : 11
        EOS = '終' : 1
        PUNC = '.' : 7
               '…' : 8
               ',' : 5
               '?' : 9
               '!' : 3
               '~' : 2
               "'": 4
               "-": 6
        SPACE = ' ' : 80
    """
    def __init__(self):
        self.eos = EOS
        self.bos = BOS
        self.space = SPACE
        self._symbols = SYMBOLS

    @property
    def sym2num(self):
        return {**{PAD: 0, EOS: 1}, **{'~': 2, '!': 3, '\'': 4, ',': 5, '-': 6, '.': 7, '🐢': 8, '?': 9},
                **{SPACE: 10}, **{BOS: 11}} # @@@ : Embedding size 문제 때문에 기존 81에서 78로 변경.

    @property
    def num2sym(self):
        sym2num = self.sym2num
        return {num: sym for sym, num in sym2num.items()}
    
class SpecialSymbols(BaseSymbols):
    # NOTE: CRATED BY MKYU (24.02.19)
    # WARNING: Python Scripts are must written by "UTF-8" because of Special Symbols
    """
        Handling Speicial Style Tagging
        g: 간투어 GTO
        s: 말더듬이 STU
        l: 웃음 LAH
        i: 한숨 SIH
        c: 비명 SCR
        h: 기합 HAA
        r: 울음 CRY
        /*: close tag
    """
    def __init__(self):
        self._sym2num = {S_GTO: 12, E_GTO: 13, S_STU: 14, E_STU: 15, S_LAH: 16, E_LAH: 17, 
            S_SIH: 18, E_SIH: 19, S_SCR: 20, E_SCR: 21, S_HAA: 22, E_HAA: 23, 
            S_CRY: 24, E_CRY: 25, }
        self._num2sym = {k: v for k, v in self._sym2num.items()}
        self._symbols = "".join(list({**self._sym2num}.keys()))
        self._tag2sym = {
            "[g]": S_GTO, "[/g]": E_GTO, "[s]": S_STU, "[/s]": E_STU, "[l]": S_LAH, "[/l]": E_LAH, 
            "[i]": S_SIH, "[/i]": E_SIH, "[c]": S_SCR, "[/c]": E_SCR, "[h]": S_HAA, "[/h]": E_HAA, 
            "[r]": S_CRY, "[/r]": E_CRY,
        }
        
        self._starts = {
            '😦': 1,
            '😐': 2,
            '😃': 3,
            '😔': 4,
            '😫': 5,
            '😤': 6,
            '😭': 7,
            '🍊': 8,
        }
        self._ends = {
            '😧': 1,
            '😑': 2,
            '😄': 3,
            '😞': 4,
            '😱': 5,
            '😬': 6,
            '😢': 7,
            '🍋': 8,
        }
        self.s2e = {
            '😦': '😧',
            '😐': '😑',
            '😃': '😄',
            '😔': '😞',
            '😫': '😱',
            '😤': '😬',
            '😭': '😢',
            '🍊': '🍋',
        }
        self.e2s = {
            v: k for k, v in self.s2e.items()
        }
    
    @property
    def symbols(self):
        return self._symbols

    @property
    def sym2num(self):
        return self._sym2num

    @property
    def num2sym(self):
        return self._num2sym

    @property
    def tag2sym(self):
        return self._tag2sym

if __name__ == '__main__':
    print(CommonSymbols().symbols)
    print(KoreanSymbols().sym2num)
    print(EnglishSymbols().sym2num)
    print(EnglishPhnSymbols().sym2num)
    print(JapanesePhnSymbols().sym2num)
    print(ChinesePhnSymbols().sym2num)
    print(CommonSymbols().sym2num)
