import re
import logging

from g2p_en import G2p
from gruut import sentences as g2p_ipa
from typing import Union
from copy import copy
from nctp.english import EN_PHN_DICT, EN_PHN_SYMBOLS, EN_IPA_SYMBOLS
from nctp.symbols import SYMBOLS, SPACE
from nctp.common import strip_diacritics


GRUUT_SPECIAL_CHAR = "‖"


class EnG2pHolder:
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        return obj

    def __init__(self, category, *args, **kwargs):
        self.category = self._validate_category(category)
        self._build_g2p()
        self.g2p = self._set_g2p()

    def _validate_category(self, category):
        assert category in EN_PHN_DICT, logging.info(f"This phoneme category of english is not allowed : {self.category}.")
        return category

    def _build_g2p(self):
        self.g2p_class = {
            "arpabet": EnG2p(),
            "ipa": GruutG2p()
        }

    def _set_g2p(self):
        return self.g2p_class[self.category]

    def __call__(self, text):
        return self.g2p(text)


class EnG2p(G2p):
    def __init__(self):
        self.symb_list = [s for s in SYMBOLS]
        self.puncs = "~?!,.🐢-😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉😭😢🤐🍊🍋 "
        self.symb_list = self.symb_list + list(self.puncs)
        super().__init__()
        del self.variables # NOTE: multi-processing fork 시 TypeError: cannot pickle '_io.BufferedReader' object 에러가 발생하여 np.load 객체를 제거합니다.

    def __call__(self, text):
        text, puncs = self._preprocess(text)
        pronounced = super().__call__(text)
        post_processed = self._remove_numb(pronounced)
        post_processed = self._remove_unne_space(post_processed)
        post_processed = self._postprocess(post_processed, puncs)
        self._validate(post_processed)
        return post_processed

    def _preprocess(self, text):
        i_word = 0
        # puncs = dict()
        puncs = list()
        text = list(text)
        for i, c in enumerate(text):
            if c in self.puncs:
                puncs.append(c)
                if i % 2 == 0:
                    text[i] = "!"  # !, ? 는 표식
                else:
                    text[i] = "?"
        return "".join(text), puncs
    
    def _postprocess(self, pronounced: list, puncs: dict):
        new_pron = list()
        pronounced = [p for p in pronounced if p != " "]
        for i, phn in enumerate(pronounced):
            if phn == "!" or phn == "?":
                punc = puncs.pop(0)
                new_pron.append(punc)
                continue
            new_pron.append(phn)
        return new_pron

    def _remove_numb(self, pronounced: list):
        return [re.sub('[0-9]', '', phn) for phn in pronounced]
    
    def _remove_unne_space(self, pronounced: list):
        new_pron = list()
        for i in range(len(pronounced)):
            if pronounced[i] in "~!,.🐢?-'😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉😭😢🤐":
                if pronounced[i-1] == " " and i > 1:
                    new_pron.pop(-1) # remove unnecessary space
            new_pron.append(pronounced[i])
        return new_pron
                

    def _validate(self, pronounced: list):
        """ Validate the result of g2pe
            * No number in result
            * All phoneme symbols should be in allowed phoneme symbols(see `dict_json/eng_dict.json`)

        Args:
            pronounced (list): the result of g2pe
        """
        for phn in pronounced:
            self._validate_checker(phn)

    def _validate_checker(self, phn : str):
        if not self._impurity_checker(phn):
            logging.warning("No numbers are allowed in the result of g2pe : {}".format(phn))
            raise AssertionError
        if not self._symbol_checker(phn):
            logging.warning(f"Phoneme symbol {phn} is not in EN_PHN_SYMBOLS")
            raise AssertionError

    def _symbol_checker(self, input_phn: str):
        """
            * All phoneme symbols should be in allowed phoneme symbols(see `dict_json/eng_dict.json`)

        Args:
            input (list): [description]
        """
        return True if input_phn in EN_PHN_SYMBOLS + self.symb_list else False

    def _impurity_checker(self, input_phn: str):
        """
            * No number in input phoneme.

        Args:
            input (list): [description]
        """
        p = '[0-9]'
        return True if re.search(p, input_phn) is None else False


class GruutG2p:
    def __init__(self):
        self.g2p_fn = g2p_ipa
        self.symb_list = [s for s in SYMBOLS]
        self._set_filter_special_char()

    def _filter_diac(self, phon):
        """
            diacritics 제거 : https://github.com/Kyubyong/mtp 참고
        """
        _p = re.sub("\ˌ|\ˈ", "", strip_diacritics(phon))
        return _p

    def _set_filter_special_char(self):
        raw_pattern = ''
        for idx, ww in enumerate(self.symb_list):
            if ww != SPACE:
                raw_pattern += '\\{}'.format(ww)
            if idx < len(self.symb_list) - 2:
                raw_pattern += '|'
        self.core_filter = r'({})+'.format(raw_pattern)
        # self.special_char_filter = re.compile(self.core_filter + r'\s*')
        self.special_char_filter = re.compile(self.core_filter + r'(\s|$)')

    def __call__(self, text):
        results = []
        # text 내에 존재하는 특수문자들을 filtering 해주고, 별도의 리스트에 저장
        text, special_char_list = self._filter_special_characters(text.rstrip())
        # g2p by gruut
        words_list = text.split(SPACE)
        for word in words_list:
            g2p_generator = self.g2p_fn(word, lang="en-us")
            for word in g2p_generator:
                for _w in word:
                    results.extend(list(map(lambda x: self._filter_diac(x), _w.phonemes)))
            results.append(" ")  # g2p 과정 중, word 사이에 공백이 제거되기때문에 삽입
        results.pop(-1)  # 마지막 공백 제거
        # _filter_special_characters 에서 필터링 했던 특수문자를 다시 삽입합니다.
        results = self._recover_special_characters(results, special_char_list)
        return results

    def _filter_special_characters(self, text: str) -> Union[str, list]:
        result = self.special_char_filter.finditer(text)
        special_char_list = [x.group(0) for x in result]
        # gruut g2p가 문장부호를 GRUUT_SPECIAL_CHAR 로 바꾸기 때문에, 이를 활용해 추후 문장부호를 삽입
        filtered_text = re.sub(self.core_filter, '!', text)
        return filtered_text, special_char_list

    def _recover_special_characters(self, phonemes: list, special_char_list: list):
        # phonemes 내에 존재하는 GRUUT_SPECIAL_CHAR 원래 특수문자가 있었다는 의미, 다시 원래 특수문자를 넣어줍니다.
        # print("phonemes", phonemes)
        # print("special_char_list", special_char_list)
        # print("len_special_char_list", len(special_char_list))
        for s_char in special_char_list:
            s_char_list = list(s_char.strip())
            pivot_index = phonemes.index(GRUUT_SPECIAL_CHAR)
            phonemes.pop(pivot_index)
            phonemes[pivot_index : pivot_index] = s_char_list
        return phonemes

    def _validate(self, pronounced: list):
        """ Validate the result of g2pe
            * No number in result
            * All phoneme symbols should be in allowed phoneme symbols(see `dict_json/eng_dict.json`)

        Args:
            pronounced (list): the result of g2pe
        """
        for phn in pronounced:
            self._validate_checker(phn)

    def _validate_checker(self, phn : str):
        if not self._symbol_checker(phn):
            logging.warning(f"Phoneme symbol {phn} is not in EN_IPA_SYMBOLS")
            raise AssertionError

    def _symbol_checker(self, input_phn: str):
        """
            * All phoneme symbols should be in allowed phoneme symbols(see `dict_json/eng_dict.json`)

        Args:
            input (list): [description]
        """
        return True if input_phn in EN_IPA_SYMBOLS + self.symb_list else False


if __name__ == "__main__":
    import pickle
    pickle.dump(G2p(), open("/SGV/users/mkyu/tmpd.pkl", 'wb'))