import re
import logging
import jamo

import unicodedata
from enum import Enum
from typing import Callable
from typing import Dict
from typing import Union
from typing import List

import nctp.korean as knorm
import nctp.english as enorm
import nctp.chinese as cnorm
import nctp.taiwanese as tnorm
import nctp.japanese as jnorm
from nctp.symbols import CommonSymbols, ERR_SYMBOL, SpecialSymbols

TAG_DICT = {'@p': 'player', '@t': 'team', '@f': 'break', '@i': 'interjection', '@in': 'sigh'}

WHITESPACE_PATTERN = [
    [r'\xa0{1,}', ' '], [r'\s{1,}', ' '], [r'\!{4,}', '!'], [r'\?{4,}', '?'],
    [r'\.{4,}', '...'], [r'\,{2,}', ','], [r'\'{2,}', '\''], [r'\〜{1,}', '~'], [r'\~{3,}', '~~']
]
# WHITESPACE_PATTERN_SERVICE = [
#     # 느낌표를 제외한 문장부호는 하나만 작성하는 편이 성능 우수함.
#     # 물음표는 2개 이상 사용 시 열화 등의 이슈

#     [r'(\xa0|\s|\_){1,}', r' '],
#     [r'\.{2,}(\!|\?)', r'...\1'], [r'(\?\!){1,}', '?!'], [r'(\!\?){1,}', '!?'],
#     [r'\,{2,}', ','], [r'\'{2,}', '\''],
#     # [r'\~+\?+', r'~?'], [r'\~+\!+', r'~!'],
#     [r'\〜{1,}', '~'], [r'\~{2,}', '~'],
#     [r'\;{1,}', '...'], [r'\.{2,}', '...'], [r'\!{3,}', '!!'], [r'\?{3,}', '??']
# ]

TAG_SPLIT_PATTERN = re.compile(r"\[(\w)\]([^[\[\/?\]]+)\[(\/)(\w)\]")

TAG_PATTERN = re.compile(r"\[(\/?)(\w)\]")

brackets_wtext = re.compile(r"\([^)]+\)")
brackets = re.compile(r"[\(\)]+")

quotation = re.compile(r"[「」\"\'\“\”]+")

CONTMARKS_WHITE_LIST = [
    # r'\.\.\.\?',  # ...? model capacity issue
    # r'\.\.\.!',   # ...!
    # r'\.\.\.',    # ...
    r'\~\.',      # ~.
    r'\?\!',      # ?!
    # r'\!\?',      # !? model capacity issue
    r'\!\!',      # !!
    # r'\?\?',      # ?? model capacity issue
    r'\~\?',      # ~?
    r'\~\!',      # ~!
    r'\.\'',      # .'
    r'\!', r'\?', r'\~', r'\.', r'\_', r'\'', r'\,', r'\-'
]


def service_pattern_generator(white_list):
    tails = '['
    for key in CommonSymbols().sym2num.keys():
        if key == ' ':
            continue
        tails += '\\' + key
    tails += ']*'

    heads = '|'.join(white_list)
    heads = r'({})'.format(heads)
    pattern = [heads + tails, r'\1']
    return pattern


WHITESPACE_PATTERN_SERVICE = [
                   [r'\〜{1,}', '~'], [r'\~{2,}', '~'],
                   [r'(\S)[\_\終\'\,\-\.\始\!]+(\?){1,}', r'\1\2'], # model capapcity issue
                   [r'(\S[^(\_\終\~\!\'\,\-\.\?\始)])[\.]+(\!)', r'\1\2'],
                   [r'\;{1,}', '.'], [r'\.{2,}', '.'],
                   [r'\,{2,}', ','], [r'\'{2,}', '\''],
                   service_pattern_generator(CONTMARKS_WHITE_LIST),
                   [r'(\xa0|\s|\_){1,}', r' ']
]
# model capacity issue
# [r'\;{1,}', '...'], [r'\.{2,}', '...'],
# [r'(\S[^(\_\終\~\!\'\,\-\.\?\始)])\.(\!|\?)', r'\1\2'], # model capacity issue : origin => (\!|\?)


def parse_styles(text):
    '''
    Parse styles

    Args:
        text (str): text for parsing

    Returns:
        style_dict (dict): dictionary of style
        text (str): remained text excluding style rule

    Examples:
        >>> parse_styles('<-style:5&reverb:0->안녕하세요')
        ({'style':5, 'reverb':0}, '안녕하세요')
        >>> parse_styles('<-reverb:0.1-> 입닥쳐 말포이')
        ({'reverb':0.1}, ' 입닥쳐 말포이')
        >>> parse_styles('  <-reverb:0-> 입닥쳐 말포이')
        ({'reverb':0}, ' 입닥쳐 말포이')
        >>> parse_styles('위즐리! <-reverb:0-> 입닥쳐 말포이')
        ({'reverb':0}, '위즐리! <-reverb:0-> 입닥쳐 말포이')
    '''
    pattern = r'^\<\-(\w+\:(\d+([.,]\d*)?|[.,]\d+)([eE][-+]?\d+)?\&?)+\-\>'
    style_dict = {'style': 0, 'reverb': 0., 'duration': 0., 'speed': 1., 'pitch': 1., 'energy': 1.}
    result = re.search(pattern, text.strip())
    if result is not None:
        styles = result.group()[2:-2].split('&')
        for style in styles:
            key, value = style.split(':')
            if key == 'style':
                style_dict[key] = int(value)
            elif key == 'reverb':
                style_dict[key] = float(value)
            elif key == 'duration':  # TODO: it will be deprecated
                style_dict[key] = float(value)
            elif key == 'speed':
                style_dict[key] = float(value)
            elif key == 'pitch':
                style_dict[key] = float(value)
            elif key == 'energy':
                style_dict[key] = float(value)
        text = result.string[result.span()[-1]:]  # separate remained text

    # pattern = re.compile(r'\@[가-힣]{1,2}[\.|\!]+|[가-힣]+\@i{1}n{1}|[가-힣]+\@[ptfi]')

    # def at_style(founded):
    #     at_index = founded.group().index('@')
    #     if at_index == 0:
    #         text = founded.group()[1:]
    #         style_dict['at_style'].append((text, 'interjection'))
    #     else:
    #         key = founded.group()[at_index:]
    #         if key in TAG_DICT.keys():
    #             text = founded.group()[:at_index]
    #             style_dict['at_style'].append((text, TAG_DICT[key]))
    #     return text

    # text = re.sub(pattern, lambda x: at_style(x), text)

    return style_dict, text

def handle_for_correct_puncs(input: str):
    # PUNCS_AFTER_SPACE = r"([🐢~。、？！.;；:,，:?!])(?=[^😧😑😄😞😱😬🙉🍋🤐😢🐢~。、？！.;；:,，:?! ])(?!$)"
    PUNCS_AFTER_SPACE = r"([🐢~。、？！.;；:,，:?!])(?!(\d\.\d))(?!(\d))(?=[^😧😑😄😞😱😬🙉🍋🤐😢🐢~。、？！.;；:,，:?!\s])(?!$)" # 숫자 소수점 제외
    MORE_SPACES = r"\s{2,}"
    result = re.sub(PUNCS_AFTER_SPACE, r'\1 ', input)
    result = re.sub(MORE_SPACES, " ", result).strip()
    result = re.sub(r'\s*🤐\s*', '🤐', result) # break 심볼 양 옆에 SPACE 토큰 있는지 탐색
    result = re.sub(r'\s*🍋', '🍋', result) # voice control end 앞에 공백이 있으면 제거
    result = re.sub(rf'🍋(?!\s|$)', '🍋 ', result) # voice control end 뒤에 공백이 없거나 끝이 아니면 추가
    return result

def parse_tagger(input: str) -> Union[str, List]:
    # NOTE: UPDATED BY MKYU (24.02.19)
    """
        input: tagging 이 표기된 문장 ex) [g]음...[/g] [s]아, 아,[/s] 그게, [g]그...[/g] 안녕하세요?"
        tag는 중괄호 안에 알파벳 n개로 구성
        output:
            - pure_text(str): tag가 제거된 문장
            - pure_tag(list): tag를 지니는 리스트
            - input(str): not processed text
    """
    text_list = list(input)
    res = TAG_SPLIT_PATTERN.finditer(input)
    tag_list = [0] * len(input)

    for x in res:
        start, end = x.start(), x.end()
        tag_list[start:end] = [x.group(1)] * (end - start)
        text_list[start: start + len(x.group(1)) + 2] = ["_"] * ((start + len(x.group(1)) + 2) - start)
        text_list[end - len(x.group(1)) - 3: end] = ["_"] * ((end + len(x.group(1)) + 3) - end)

    if "_" in text_list:
        pure_text = []
        pure_tag = []
        for idx in range(len(text_list)):
            if text_list[idx] != "_":
                pure_text.append(text_list[idx])
                pure_tag.append(tag_list[idx])
        pure_text = ''.join(pure_text)
    else:
        pure_text, pure_tag = input, tag_list
    return pure_tag, pure_text, input

def parse_style_tag_indi(input: str):
    # NOTE: CREATED BY MKYU (24.02.19)
    """
        input: tagging 이 표기된 문장 ex) [g]음...[/g] [s]아, 아,[/s] 그게, [g]그...[/g] 안녕하세요?"
        outout:
            태그가 심볼로 바뀐 문장 ex) 😦음...😧 😐아, 아,😑 그게, 😦그...😧 안녕하세요?
    """
    ssym = SpecialSymbols()
    res = TAG_PATTERN.finditer(input)
    for r in res:
        input = input.replace(r.group(0), ssym.tag2sym.get(r.group(0),r.group(0)), 1) #스타일 태그에 해당 되지 않는 태그는 그대로 반환 되도록 수정 - 25/03/25 dongjoo195
    return input

def parse_style_tag2ssml(input: str):
    # 입력받은 문장에서 style tag를 ssml로 파싱합니다(보여주기용임, 폐기예정)
    """
        input: tagging 이 표기된 문장 ex) [g]음...[/g] [s]아, 아,[/s] 그게, [g]그...[/g] 안녕하세요?"
        outout:
            태그가 심볼로 바뀐 문장 ex) 😦음...😧 😐아, 아,😑 그게, 😦그...😧 안녕하세요?

    """
    ssym = SpecialSymbols()
    res = TAG_PATTERN.finditer(input)
    
    nv_type = {
        "g": "간투어",
        "s": "말더듬",
        "l": "웃음",
        "c": "비명",
        "h": "기합",
        "i": "한숨",
        "r": "울음"
    }

    for r in res:
        t = r.group(0)[1]
        if t == "/":
            replace = '</nc:texteffect>'
        else:
            replace = f'<nc:texteffect type="{nv_type[t]}">'  
        input = input.replace(r.group(0), replace, 1)
    return input

def remove_bracket(input: str):
    # NOTE: CREATED BY MKYU (24.02.20)
    """
        input: 괄호 여닫음이 있는 문장 (주로 병음표기를 위해 사용됩니다) ex) 저는 제임스(James)와 콜린(Colin) 요원을 가족으로 생각하고 ((있습니다.
        output: 괄호 여닫음이 없는 문장 ex) 저는 제임스와 콜린 요원을 가족으로 생각하고 있습니다.
    """
    fixed_code = input.replace("（", "(").replace("）", ")").replace("[", "").replace("]", "")

    bracket_wtext_removed = re.sub(brackets_wtext, "", fixed_code)
    bracket_removed = re.sub(brackets, "", bracket_wtext_removed)
    output = bracket_removed.replace("  ", " ")
    return output

def remove_quotation(input: str):
    # NOTE: CREATE BY MKYU (24.02.20)
    """
        input: 인용표시가 있는 문장 
        output: 인용표시를 제거한 문장
    """
    return re.sub(quotation, "", input)

def convert_enumeration(input: str):
    # NOTE: CREATE BY MKYU (24.02.20)
    """
        input: 중국어, 일본어에서 사용하는 가운데 점을 사용한 열거형 문장 ex) 네가 장을 봐야할 것은 토마토・바나나・감자・치즈・소고기 란다.
        output: 가운데 점을 반점 (", ") 으로 치환함. (반점+SPACE)
    """
    return input.replace("・", ", ")

def strip_diacritics(input: str):
    return ''.join(char for char in unicodedata.normalize('NFD', input) if unicodedata.category(char) != 'Mn')

def convert_ellipsis(text: str) -> str:
    # 몇몇 텍스트 편집기에서 ...을 압축하여 표현하는 것 같다.
    text = re.sub("…", "🐢", text)
    text = re.sub(r"\.\.\.+", "🐢", text)
    text = re.sub(r"\.\.", ".", text)
    return text

def collapse_linebreak(text: str) -> str:
    '''여러 라인의 문장이 들어올 경우 linebreak들을 없애 한 라인으로 collapse.

    Args:
        text (str): 입력 문장

    Returns:
        text (str): 중복 문장 부호 제거 처리 된 결과
    '''
    if text.count('\n') == 0:
        return text

    lines = (line.strip() for line in text.splitlines())
    lines = (knorm.join_period(line) for line in lines if line != '')
    return ' '.join(lines)


def collapse_specialchars(text, custom_pattern=None):
    """ 입력 문장 내 중복 공백 혹은 중복 문장 부호 제거
        | 문장 부호 | 중복 개수(N개 이상) | 처리 |
        | (space)  | 1 | 하나로 통합 |
        | ! | 4 | 하나로 통합 |
        | ? | 4 | 하나로 통합 |
        | . | 4 | 말줄임표(마침표 세개)로 변환
        | , | 1 | 하나로 통합 |
        | ' | 2 | 하나로 통합 |
        | ∼ | 1 | ~로 변환 및 통합 |
        | ~ | 3 | 두개로 변환 |

    Args:
        text (str): 입력 문장

    Returns:
        text (str): 중복 문장 부호 제거 처리 된 결과
    """
    # text = re.sub(r'\xa0', ' ', text)
    # _whitespace_re = re.compile(r'\s+')
    # text = re.sub(_whitespace_re, ' ', text)
    if custom_pattern is not None:
        pattern_dict = custom_pattern
    else:
        pattern_dict = WHITESPACE_PATTERN
    for p in pattern_dict:
        text = re.sub(re.compile(p[0]), p[1], text)
    return text


def remove_parentheses(text):
    text, _ = _remove_parentheses(text)
    return text


def _remove_parentheses(text, start=False):
    """괄호 내 단어 삭제

    Args:
        text (str): 입력 문장
        start (bool, optional): [description]. Defaults to False.

    Returns:
        processed_text (str) : 괄호가 제거된 문장, 재귀 호출 후 최종 결과는 괄호와 괄호 내 문자가 제거된 문장.
        i (int) : pivot 포지션
    """
    ret = []
    i = 0
    while i < len(text):
        if text[i] == "(":
            _ret, _i = _remove_parentheses(text[i + 1:], True)
            if _ret == "":
                ret.append(_ret)
                i = i + _i + 1
            else:
                ret.append(text[i])
                ret.append(_ret)
                i = i + _i + 1
        elif text[i] == ")" and start is True:
            return "", i + 1
        else:
            ret.append(text[i])
            i = i + 1
    processed_text = "".join(ret)
    return processed_text, i


# if __name__ == '__main__':
#     print(sym2num)

def log_csv(texts, name, stepbystep=False):
    with open("./logs/{}.csv".format(name), "a", encoding="UTF-8") as f:
        for text in texts:
            if stepbystep:
                f.write('{:40}'.format(text[0]) + ': ' + text[1] + '\n')
            else:
                f.write(text + '\n')
        f.write('\n')


def limit_txtlen(text, limit):
    try:
        if len(text) > limit:
            logging.debug("The length of input text exceed limitation. Length : {}".format(len(text)))
            return text[:limit]
        else:
            return text
    except Exception as err:
        logging.debug(err, exc_info=True)
        return logging.debug("Fail during cheking the length of input text.")


# TODO: Code-Switching


class Language(Enum):
    korean = 'korean'
    korean_ipa = 'korean_ipa'
    english = 'english'
    multi = 'multi'
    english_arpabet = 'english_arpabet'
    english_ipa = 'english_ipa'
    japanese_prosody = 'japanese_prosody'
    chinese = 'chinese'
    taiwanese = 'taiwanese'

    def __str__(self):
        return self.value


class Normalizer:
    def __init__(self, normalize: Callable, *args):
        self._normalize = normalize
        self._args = args

    def normalize(self, target: str) -> str:
        return self._normalize(target, *self._args)


class NormalizeStep(Enum):
    # Common normalize steps
    collapse_linebreak = Normalizer(collapse_linebreak)
    remove_parentheses = Normalizer(remove_parentheses)
    collapse_special_characters = Normalizer(collapse_specialchars)
    collapse_special_characters_service = Normalizer(collapse_specialchars, WHITESPACE_PATTERN_SERVICE)
    handle_style_tag = Normalizer(parse_style_tag_indi)
    convert_ellipsis = Normalizer(convert_ellipsis)
    handle_puncs_spaces = Normalizer(handle_for_correct_puncs)

    # Korean normalize steps
    drop_incompletes = Normalizer(knorm.drop_incompletes)
    patterns = Normalizer(knorm.normalize_patterns)
    number = Normalizer(knorm.normalize_number)
    etc_dictionary = Normalizer(knorm.normalize_with_dictionary, 'etc', 'key_only')
    universe_dictionary = Normalizer(knorm.normalize_with_dictionary, 'universe', 'chunks_upper')
    eng_dictionary = Normalizer(knorm.normalize_with_dictionary, 'english', 'chunks_upper')
    english = Normalizer(knorm.normalize_english)
    character = Normalizer(knorm.normalize_character)
    pronunciation = Normalizer(knorm.normalize_pronunciation)
    period = Normalizer(knorm.join_period)

    # English normalize steps
    to_ascii = Normalizer(enorm.convert_to_ascii)
    lowercase = Normalizer(enorm.lowercase)
    expand_numbers = Normalizer(enorm.expand_numbers)
    expand_abbreviations = Normalizer(enorm.expand_abbreviations)

    # Chinese step
    chn_normalize = Normalizer(cnorm.chn_normalize)
    remove_prosody = Normalizer(cnorm.remove_prosody)
    chn_prosody = Normalizer(cnorm.prosody_predict)
    chn_baker = Normalizer(cnorm.handle_baker_like)

    remove_quotation = Normalizer(remove_quotation)
    convert_enumeration = Normalizer(convert_enumeration)
    remove_bracket = Normalizer(remove_bracket)

    # Taiwanese step
    twn_normalize = Normalizer(tnorm.twn_normalize)
    twn_normalize_new = Normalizer(tnorm.twn_normalize_new)
    twn_prosody = Normalizer(tnorm.prosody_predict)
    twn_baker = Normalizer(tnorm.handle_baker_like)

    # Japanese Normalize
    jpn_num_normalize = Normalizer(jnorm.convert_number_to_hiragana_in_text)



class Cleaner:
    def __init__(self, clean: Callable, *args):
        self._clean = clean
        self._args = args

    def clean(self, target: str) -> str:
        return self._clean(target, *self._args)


class CleanStep(Enum):
    clean_residual = Cleaner(knorm.remove_residual)


def key_checker(options: Dict, target_key: str, default):
    return True if target_key in options else default


def check_then_symbolize(text: str, symbols: Dict, err_symbol=ERR_SYMBOL):
    return [symbols[s] if key_checker(symbols, s, False) else err_symbol for s in text]


def korean_symbolize(text, kor_symbols: Dict, options: Dict):
    """정규화된 문장의 끝에 eos를 추가하고, symbol화"""
    _del_ng = key_checker(options, 'del_ng', False)
    _head = key_checker(options, 'head', False)
    _tail = key_checker(options, 'tail', False)
    text = jamo.h2j(text)

    comsym = CommonSymbols()
    symbolized = check_then_symbolize(text, kor_symbols)

    if _head:
        symbolized = [kor_symbols[comsym.bos], kor_symbols[comsym.space]] + symbolized
    if _del_ng:
        symbolized = list(filter(lambda x: x != kor_symbols[chr(0x110b)], symbolized))
    if _tail:
        symbolized = symbolized + [kor_symbols[comsym.space]]
    # default step
    symbolized = symbolized + [kor_symbols[comsym.eos]]

    return symbolized


def korean_phn_symbolize(text, kor_symbols: Dict, options: Dict):
    """정규화된 문장의 끝에 eos를 추가하고, symbol화"""
    _del_ng = key_checker(options, 'del_ng', False)
    _head = key_checker(options, 'head', False)
    _tail = key_checker(options, 'tail', False)
    text = jamo.h2j(text)
    if _del_ng:
        text = list(filter(lambda x: x != chr(0x110b), text))
    text = [knorm.KR_IPA_MAP[s]["ipa"] if s in knorm.KR_IPA_MAP else s for s in text]

    comsym = CommonSymbols()
    symbolized = check_then_symbolize(text, kor_symbols)
    # symbolized = [kor_symbols[s] for s in text if s in kor_symbols]
    if _head:
        symbolized = [kor_symbols[comsym.bos], kor_symbols[comsym.space]] + symbolized
    # if _del_ng:
    #     symbolized = list(filter(lambda x: x != 311, symbolized))
    if _tail:
        symbolized = symbolized + [kor_symbols[comsym.space]]
    # default step
    symbolized = symbolized + [kor_symbols[comsym.eos]]

    return symbolized


def eng_symbolize(text: Union[str, List], eng_symbols: Dict, options: Dict):
    """정규화된 문장의 끝에 eos를 추가하고, symbol화"""
    _head = key_checker(options, 'head', False)
    _tail = key_checker(options, 'tail', False)

    comsym = CommonSymbols()
    symbolized = check_then_symbolize(text, eng_symbols)
    if _head:
        symbolized = [eng_symbols[comsym.bos], eng_symbols[comsym.space]] + symbolized
    if _tail:
        symbolized = symbolized + [eng_symbols[comsym.space]]
    # default step
    symbolized = symbolized + [eng_symbols[comsym.eos]]

    return symbolized

def jpn_symbolize(text: Union[str, List], jpn_symbols: Dict, options: Dict):
    """정규화된 문장의 끝에 eos를 추가하고, symbol화"""
    _head = key_checker(options, 'head', False)
    _tail = key_checker(options, 'tail', False)
    # print(jpn_symbols)
    comsym = CommonSymbols()
    symbolized = check_then_symbolize(text, jpn_symbols)
    if -1 in symbolized:
        print(text)
    if _head:
        symbolized = [jpn_symbols[comsym.bos], jpn_symbols[comsym.space]] + symbolized
    if _tail:
        symbolized = symbolized + [jpn_symbols[comsym.space]]
    # default step
    symbolized = symbolized + [jpn_symbols[comsym.eos]]

    return symbolized

def chn_symbolize(text: Union[str, List], chn_symbols: Dict, options: Dict):
    """정규화된 문장의 끝에 eos를 추가하고, symbol화"""
    _head = key_checker(options, 'head', False)
    _tail = key_checker(options, 'tail', False)

    comsym = CommonSymbols()
    if type(text) == str:
        text = text.split(" ")
    # new_text = list()
    # for sym in text:
    #     if "#" in sym and "_" in sym:
    #         new_text.extend([sym[:-1], " "])
    #     else:
    #         new_text.append(sym)
    # text = new_text

    symbolized = check_then_symbolize(text, chn_symbols)
    if _head:
        symbolized = [chn_symbols[comsym.bos], chn_symbols[comsym.space]] + symbolized
    if _tail:
        symbolized = symbolized + [chn_symbols[comsym.space]]
    # default step
    symbolized = symbolized + [chn_symbols[comsym.eos]]

    return symbolized

def multi_symbolize(text: Union[str, List], multilang_symbols: Dict, options: Dict):
    """
        한국어 symbolize 과정을 따름
    """
    return korean_symbolize(text, multilang_symbols, options)



class Symbolizer:
    def __init__(self, symbolize: Callable, *args):
        self._symbolize = symbolize
        self._args = args

    def _validate(self, symbolized: List) -> bool:
        err_flag = True if ERR_SYMBOL in symbolized else False
        if err_flag:
            logging.warning("Error in results of symbolize, please check KeyError in symbolize function.")
            print(symbolized)
        return symbolized

    def symbolize(self, target, symbols: List, options: List = []) -> List:
        return self._validate(self._symbolize(target, symbols, options))


class GetSymbolizer:
    def __init__(self):
        self._symbol_step_dict = {
            Language.korean : Symbolizer(korean_symbolize),
            Language.korean_ipa : Symbolizer(korean_phn_symbolize),
            Language.english : Symbolizer(eng_symbolize),
            Language.multi : Symbolizer(multi_symbolize),
            Language.english_arpabet : Symbolizer(eng_symbolize),
            Language.english_ipa : Symbolizer(eng_symbolize),
            Language.japanese_prosody : Symbolizer(jpn_symbolize),
            Language.chinese : Symbolizer(chn_symbolize),
            Language.taiwanese: Symbolizer(chn_symbolize)
        }

    def __call__(self, lang: Language):
        return self._symbol_step_dict[lang]


def symbolizer_selector(lang: Language):
    __SymbStep = GetSymbolizer()
    return __SymbStep(lang)


if __name__ == "__main__":
    # print(convert_ellipsis("안녕........ 하세요?"))
    from bs4 import BeautifulSoup
    import textwrap
    x = parse_style_tag2ssml("<speak>[g]음...[/g] [s]아, 아,[/s] 그게, [g]그...[/g] 안녕하세요?</speak>")
    x = BeautifulSoup(x, 'xml')
    x = x.prettify()
    print(x)
    print(parse_style_tag_indi("오늘 배울 내용은 수학 익힘책 백사십육쪽이에요~"))
    print(remove_bracket("李舜臣（イ・スンシン）その知らせを聞いた人々は皆、李舜臣（イ・スンシン）を気を毒に思((った。."))
    print(remove_quotation("彼女の代表作「オルランド」は、ジェンダーと性の問題を歴史的・社会的脈絡で考察する。"))
    print(convert_enumeration("彼女の代表作「オルランド」は、ジェンダーと性の問題を歴史的・社会的脈絡で考察する。"))
    print(handle_for_correct_puncs("그게말이야,너,정말  이상해!"))