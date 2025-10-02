import re
from typing import Dict, Pattern

from . import eng_kor_sDict as edict
from . import kor_sDict as kdict
from . import universe_sDict as udict

PAT_BASIC = r'''
    {}              # just body
'''

PAT_CHUNK = r'''
    (?<!            # open negative lookbehind assertion
        [A-Za-z]    # one alphabet should precede the body
    )               # close negative lookbehind assertion
    (?:             # open non-capturing group
        {}          # pattern to be matched
    )               # close non-capturing group
    (?!             # open negative lookahead assertion
        [A-Za-z]    # one alphabet should follow the body
    )               # close negative lookahead assertion
'''


class Precompiler:
    '''
    DictManager handles and pre-compile dictionaries for substitution usage.
    '''

    __SINGLETON_MANAGER: 'Precompiler' = None

    def __init__(self):
        self.dicts: Dict[str, Dict[str, str]] = {
            'etc': kdict.etc_dict,
            'english': edict.eng_dict,
            'universe': udict.universe_dict,
            'pronounce_g2p': kdict.pronounce_dict_g2p,
            'pronounce_norm_pron': kdict.pronounce_dict_norm_pron,
            'unit': kdict.unit_to_kor1
        }

        self.dicts_escaped: Dict[str, Dict[str, str]] = {
            lang: {
                re.escape(key): value for key, value in dic.items()
            } for lang, dic in self.dicts.items()
        }

        self.regex_patterns: Dict[str, Dict[bool, Dict[str, Pattern]]] = {
            lang: {
                False: {
                    'basic': re.compile(PAT_BASIC.format('|'.join(dic.keys())), re.VERBOSE),
                    'chunk': re.compile(PAT_CHUNK.format('|'.join(dic.keys())), re.VERBOSE),
                },
                True: {
                    'basic': re.compile(PAT_BASIC.format('|'.join(dic.keys())), re.VERBOSE | re.IGNORECASE),
                    'chunk': re.compile(PAT_CHUNK.format('|'.join(dic.keys())), re.VERBOSE | re.IGNORECASE),
                },
            } for lang, dic in self.dicts_escaped.items()
        }

    def dic(self, lang: str, escaped: bool = False) -> Dict[str, str]:
        dicts = self.dicts if not escaped else self.dicts_escaped
        assert lang in dicts, "Dictionary for '{}' does not exists.".format(lang)
        return dicts[lang]

    def pattern(self, lang: str, type: str, ignorecase: bool = False) -> Pattern:
        assert lang in self.regex_patterns, "Pattern for '{}' does not exists.".format(lang)

        patterns = self.regex_patterns[lang][ignorecase]
        assert type in patterns, "'{}' type pattern does not exists.".format(type)

        return patterns[type]

    @classmethod
    def get(cls):
        if cls.__SINGLETON_MANAGER is None:
            cls.__SINGLETON_MANAGER = Precompiler()
        return cls.__SINGLETON_MANAGER


def get_dict(lang: str, escaped: bool = False) -> Dict[str, str]:
    '''
    Find and return preprocessed dictionary. Raise AssertionError when given
    `lang` does not exists.

    `lang`: 'etc', 'english', 'universe', 'pronounce', 'unit'
    '''
    manager = Precompiler.get()
    return manager.dic(lang, escaped)


def get_regex_pattern(lang: str, type: str, ignorecase: bool = False) -> Pattern:
    '''
    Find and return precompiled regex pattern from dictionary keys. Raise
    AssertionError when given `lang` or `type` does not exists.

    `lang`: 'etc', 'english', 'universe', 'pronounce', 'unit'
    `type`: 'basic', 'chunk'
    '''
    manager = Precompiler.get()
    return manager.pattern(lang, type, ignorecase)
