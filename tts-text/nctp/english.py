import re
from unidecode import unidecode
import inflect
import string

from nctp.dictionary.eng_pid_sDict import eng_arpabet_dict, eng_ipa_dict


EN_SYMBOLS = string.ascii_lowercase + string.ascii_uppercase

EN_PHN_DICT = ["arpabet", "ipa"]
EN_PHN_SYMBOLS = list(eng_arpabet_dict.keys()) 
EN_IPA_SYMBOLS = list(eng_ipa_dict.keys()) 


def convert_to_ascii(text):
    """
    Converts to ascii, existed in keithito but deleted in carpedm20

    1) Delete non-ascii characters as emojis (비슷한 ascii character 없음)
    2) Convert non-ascii characters as the most similar ascii characters
    3) Convert chinese characters into pinyin

    Args:
        text (str): text sentence

    Returns:
        text (str): converted text sentence

    Examples:
        >>> convert_to_ascii("Welcome! 💕")
        "Welcome!"
        >>> convert_to_ascii("太美了, 是吧?")
        "Tai Mei Le, Shi Ba "
    """
    return unidecode(text)


def lowercase(text):
    """
    Convert all the upper-case characters into lower-case

    Args:
        text (str): text sentence

    Returns:
        text (str): lower-cased text sentence

    Examples:
        >>> lowercase("Please ANSWER me.")
        "please answer me."
    """
    return text.lower()


def expand_numbers(text):
    """
    Convert various types of numeric symbols into english-readable phrases
    depending on the number types

    Args:
        text (str): text sentence

    Returns:
        text (str): english-only text sentence

    Examples:
        >>> expand_numbers("$200")
        "two hundred dollars"
        >>> expand_numbers("In 1982 March 22nd")
        "In nineteen eighty two March twenty second"
        >>> expand_numbers("This year is 2021.")
        "This year is twenty twenty one."
    """
    return normalize_numbers(text)


def expand_abbreviations(text):
    """
    Describe abbreviation as a full name
    Remove `.` in initaial pattern text. ex) B.T.S -> B T S

    Args:
        text ([str]): text string with abbreviation

    Returns:
        [str]: text string with full description
    """
    for regex, replacement in _abbreviations:
        text = re.sub(regex, replacement, text)

    text = re.sub(_initials_re, _get_alphabet, text)
    return text


"""
regex argument for expand_abbreviations()
"""
_initials_re = r"\b([a-zA-Z])\.{1}(?!$)"


def _get_alphabet(m):
    return m.group(1) + " "


"""
regex argument for normalize_numbers()
"""
_inflect = inflect.engine()
_comma_number_re = re.compile(r'([0-9][0-9\,]+[0-9])')
_decimal_number_re = re.compile(r'([0-9]+\.[0-9]+)')
_pounds_re = re.compile(r'£([0-9\,]*[0-9]+)')
_dollars_re = re.compile(r'\$([0-9\.\,]*[0-9]+)')
_ordinal_re = re.compile(r'[0-9]+(st|nd|rd|th)')
_number_re = re.compile(r'[0-9]+')


def _remove_commas(m):
    """
    remove commas in input text string
    used for regex argument
    """
    return m.group(1).replace(',', '')


def _expand_decimal_point(m):
    """
    remove decimal points in input text string
    used for regex argument
    """
    return m.group(1).replace('.', ' point ')


def _expand_dollars(m):
    """
    금액에 따라서 dollar 표기법을 적어놓음
    used for regex argument
    """
    match = m.group(1)
    parts = match.split('.')
    if len(parts) > 2:
        return match + ' dollars'  # Unexpected format
    dollars = int(parts[0]) if parts[0] else 0
    cents = int(parts[1]) if len(parts) > 1 and parts[1] else 0
    if dollars and cents:
        dollar_unit = 'dollar' if dollars == 1 else 'dollars'
        cent_unit = 'cent' if cents == 1 else 'cents'
        return '%s %s, %s %s' % (dollars, dollar_unit, cents, cent_unit)
    elif dollars:
        dollar_unit = 'dollar' if dollars == 1 else 'dollars'
        return '%s %s' % (dollars, dollar_unit)
    elif cents:
        cent_unit = 'cent' if cents == 1 else 'cents'
        return '%s %s' % (cents, cent_unit)
    else:
        return 'zero dollars'


def _expand_ordinal(m):
    """
    서수를 읽을 수 있는 형태로 변환함
    used for regex argument
    """
    return _inflect.number_to_words(m.group(0))


def _expand_number(m):
    """
    연도 숫자 표기를 문법에 맞게 변환함
    used for regex argument
    """
    num = int(m.group(0))
    if num > 1000 and num < 3000:
        if num == 2000:
            return 'two thousand'
        elif num > 2000 and num < 2010:
            return 'two thousand ' + _inflect.number_to_words(num % 100)
        elif num % 100 == 0:
            return _inflect.number_to_words(num // 100) + ' hundred'
        else:
            return _inflect.number_to_words(num, andword='', zero='oh', group=2).replace(', ', ' ')
    else:
        return _inflect.number_to_words(num, andword='')


def normalize_numbers(text):
    """
    다양한 형태의 숫자 표현을 읽을 수 있는 형태로 변환함

    Args:
        text (str): input string

    Returns:
        str: 숫자들이 읽을 수 있는 형태로 풀어 쓰여진 text string
    """
    text = re.sub(_comma_number_re, _remove_commas, text)
    text = re.sub(_pounds_re, r'\1 pounds', text)
    text = re.sub(_dollars_re, _expand_dollars, text)
    text = re.sub(_decimal_number_re, _expand_decimal_point, text)
    text = re.sub(_ordinal_re, _expand_ordinal, text)
    text = re.sub(_number_re, _expand_number, text)
    return text


# List of (regular expression, replacement) pairs for abbreviations:
_abbreviations = [(re.compile('\\b%s\\.' % x[0], re.IGNORECASE), x[1]) for x in [
    ('mrs', 'misuss'),
    ('mr', 'mister'),
    ('dr', 'doctor'),
    ('st', 'saint'),
    ('co', 'company'),
    ('jr', 'junior'),
    ('maj', 'major'),
    ('gen', 'general'),
    ('drs', 'doctors'),
    ('rev', 'reverend'),
    ('lt', 'lieutenant'),
    ('hon', 'honorable'),
    ('sgt', 'sergeant'),
    ('capt', 'captain'),
    ('esq', 'esquire'),
    ('ltd', 'limited'),
    ('col', 'colonel'),
    ('ft', 'fort'),
    ('mrs', 'misess'),
    ('mr', 'mister'),
    ('dr', 'doctor'),
    ('st', 'saint'),
    ('co', 'company'),
    ('jr', 'junior'),
    ('maj', 'major'),
    ('gen', 'general'),
    ('drs', 'doctors'),
    ('rev', 'reverend'),
    ('lt', 'lieutenant'),
    ('hon', 'honorable'),
    ('sgt', 'sergeant'),
    ('capt', 'captain'),
    ('esq', 'esquire'),
    ('ltd', 'limited'),
    ('col', 'colonel'),
    ('ft', 'fort'),
    ("an\'\s", 'and '),
    ('ave', 'avenue'),
    ('bldg', 'building'),
    ('blvd', 'boulevard'),
    ('btm', 'bottom'),
    ('clb', 'club'),
    ('cnt', 'count'),
    ('co', 'company'),
    ('ct', 'court'),
    ('ext', 'extension'),
    ('fwy', 'freeway'),
    ('gen', 'general'),
    ('gen', 'general'),
    ('ms', 'miss'),
    ('msg', 'message'),
    ('mt', 'mountain'),
    ('pl', 'place'),
    ('prof', 'professor'),
    ('rd', 'road'),
    ('sq', 'square'),
    ('rly', 'really'),
    ('rev', 'reverend'),
    ('st', 'saint'),
    ('sgt', 'sergeant'),
    ('sr', 'senior'),
    ('terr', 'terrace'),
    ('txt', 'text'),
]]
