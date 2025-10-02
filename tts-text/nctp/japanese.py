
from nctp.dictionary.jpn_pid_sDict import jpn_prosody_dict

JPN_SYMBOLS = list(jpn_prosody_dict.keys())


import kanjize
import re

def convert_number_to_hiragana_in_text(text):
    def replace_number_with_kanji(match):
        num_str = match.group(0)
        if '.' in num_str:
            int_part, frac_part = num_str.split(".")
            kanji = kanjize.number2kanji(int(int_part)) + "点" + "".join(kanjize.number2kanji(int(d)) for d in frac_part)
        else:
            kanji = kanjize.number2kanji(int(num_str))
        return kanji

    # \d+(?:\.\d+)? → 소수를 포함한 숫자 전체를 잡기
    converted_text = re.sub(r'\d+(?:\.\d+)?', replace_number_with_kanji, text)
    return converted_text
