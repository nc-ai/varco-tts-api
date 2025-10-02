import re
import logging

import os
from typing import List

import inflect
import string
import jieba
import pypinyin
from nctp.symbols import SYMBOLS, SPACE
from nctp.common import strip_diacritics
from nctp.ncg2pt.taiwanese_handler import TaiwaneseProcessor

SPECIAL_NOTES = '。？！?!.;；:,，: '

class TwnG2pHolder:
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        return obj

    def __init__(self, category, *args, **kwargs):
        self.category = self._validate_category(category)
        self._build_g2p()
        self.g2p = self._set_g2p()

    def _validate_category(self, category):
        assert category == "taiwanese", logging.info(f"This phoneme category of english is not allowed : {self.category}.")
        return category

    def _build_g2p(self):
        self.g2p_class = {
            "taiwanese": TwnProG2p()
            }

    def _set_g2p(self):
        return self.g2p_class[self.category]

    def __call__(self, text):
        return self.g2p(text)


class TwnProG2p():
    def __init__(self):
        self.symb_list = [s for s in SYMBOLS]
        self.handler = TaiwaneseProcessor()
        super().__init__()


    def __call__(self, text):
        pronounced = self.handler.text_to_sequence(text).replace("。", ".").replace("、", ",").replace("？", "?").replace("！", "!").replace("：", ",")
        return pronounced
 