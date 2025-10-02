import logging
import re
import os
import numpy as np
import fasttext
from typing import Dict, List, Tuple, Union, Callable
import importlib.util
# from googletrans import Translator

from nctp.common import Language
from nctp.common import NormalizeStep, CleanStep
from nctp.common import symbolizer_selector
from nctp.common import parse_styles, parse_tagger
from nctp.character import Character, MLCharacter
from nctp.error import TPError
from nctp.error import TextLengthError
from nctp.symbols import S_VEF, E_VEF, S_VEF_IDX, E_VEF_IDX, CommonSymbols, SpecialSymbols
from nctp.symbols import EnglishSymbols
from nctp.symbols import EnglishPhnSymbols
from nctp.symbols import KoreanSymbols
from nctp.symbols import KoreanPhnSymbols
from nctp.symbols import JapanesePhnSymbols
from nctp.symbols import ChinesePhnSymbols
from nctp.symbols import TaiwanesePhnSymbols
import nctp.steps as steps
from nctp.korean import JAMO_TAILS

NUMBER = 1234567890
SPECIAL_NOTES = '。？！?!.;；:,，: '
ENG = [chr(i) for i in range(65, 123)]
KOR = [chr(i) for i in range(44032, 55204)]
JPN = [chr(i) for i in range(12353, 12543)]
NCTTS_TM = os.environ.get("NCTTS_TM")

class TextProcessor:
    STR2LANG: Dict[str, Language] = {
        'korean': Language.korean,
        'korean_ipa': Language.korean_ipa,
        'english': Language.english,
        'english_arpabet': Language.english_arpabet,
        'english_ipa': Language.english_ipa,
        'japanese_prosody': Language.japanese_prosody,
        'chinese': Language.chinese,
        'taiwanese': Language.taiwanese,
    }

    LANG2SYMBOL: Dict[Language, Dict[str, int]] = {
        Language.korean: {**CommonSymbols().sym2num, **SpecialSymbols().sym2num, **KoreanSymbols().sym2num},
        Language.korean_ipa: {**CommonSymbols().sym2num, **SpecialSymbols().sym2num, **KoreanPhnSymbols(category="ipa").sym2num},
        Language.english: {**CommonSymbols().sym2num, **SpecialSymbols().sym2num, **EnglishSymbols().sym2num},
        Language.english_arpabet: {**CommonSymbols().sym2num, **SpecialSymbols().sym2num, **EnglishPhnSymbols(category="arpabet").sym2num},
        Language.english_ipa: {**CommonSymbols().sym2num, **SpecialSymbols().sym2num, **EnglishPhnSymbols(category="ipa").sym2num},
        Language.japanese_prosody: {**CommonSymbols().sym2num, **SpecialSymbols().sym2num,  **JapanesePhnSymbols().sym2num},
        Language.chinese: {**CommonSymbols().sym2num, **SpecialSymbols().sym2num,  **ChinesePhnSymbols().sym2num},
        Language.taiwanese: {**CommonSymbols().sym2num, **SpecialSymbols().sym2num,  **TaiwanesePhnSymbols().sym2num}
    }

    SPACES = re.compile(r' +')

    def __init__(self,
                 language: Union[str, Language],
                 normalize_step: Union[str, List[NormalizeStep]] = None,
                 length_limit: bool = False,
                 logger: logging.Logger = None,
                 use_g2p: bool = False):
        language = TextProcessor.STR2LANG[language] if isinstance(language, str) else language
        self._language = language
        self._use_g2p = use_g2p
        self._logger = logger
        self._set_env(language, normalize_step)

        if length_limit:
            if language in [Language.english, Language.multi, Language.english_arpabet, Language.english_ipa, Language.japanese_prosody, Language.chinese, Language.taiwanese]:
                self._length_limit = 600
            elif language == Language.korean:
                self._length_limit = 200
        else:
            self._length_limit = None

    def _set_env(self, language, normalize_step):
        self._language = language
        self._nstep = steps.step_selector(language, normalize_step)
        self._symbols = {k: v for k, v in TextProcessor.LANG2SYMBOL[language].items()}
        self._val2syms = {v: k for k, v in self._symbols.items()}
        self._symbolizer = symbolizer_selector(language)
        self._g2p = self._set_g2p(language) if self._use_g2p else None
        self._log('language', self._language)
        self._log('normalize steps', self._nstep)
        self._puncs = "~!,.🐢?-'"

    def _set_g2p(self, language):
        self._dict_g2p: Dict[Language, Callable] = {
            Language.english: None,
            Language.multi: None,
        }
        if language == [Language.korean, Language.korean_ipa]:
            from nctp.ncg2pk.pronounce import nc_g2pk
            self._dict_g2p.update({
                lang: nc_g2pk for lang in [Language.korean, Language.korean_ipa]
            })
        if language in [Language.english_arpabet, Language.english_ipa]:
            from nctp.ncg2pe.pronounce import EnG2pHolder
            self._dict_g2p.update({
                Language.english_arpabet: EnG2pHolder(category="arpabet"),
                Language.english_ipa: EnG2pHolder(category="ipa")
            })
        if language in [Language.japanese_prosody]:
            from nctp.ncg2pj.pronounce import JpnG2pHolder
            self._dict_g2p.update({
                Language.japanese_prosody: JpnG2pHolder(category="prosody")
                })
        if language in [Language.chinese]:
            from nctp.ncg2pc.pronounce import ChnG2pHolder
            self._dict_g2p.update({
                Language.chinese: ChnG2pHolder(category="chinese")
                })
        if language in [Language.taiwanese]:
            from nctp.ncg2pt.pronounce import TwnG2pHolder
            self._dict_g2p.update({
                Language.taiwanese: TwnG2pHolder(category="taiwanese")
                })
        return self._dict_g2p[language]

    def validate(self, text: str) -> Union[TPError, None]:
        '''문장의 에러를 검출합니다.
        1. 길이 체크
        '''
        # check text length limit
        if self._length_limit is not None:
            if len(text) > self._length_limit:
                return TextLengthError(self._length_limit)
        return None

    def parse(self, text: str) -> Tuple[str, dict]:
        """문장 내 음성 합성 effect 명령어를 처리합니다."""
        self._log('origin text', text)
        style, parsed = parse_styles(text)
        # tags, parsed = parse_tagger(parsed)
        self._log('parsed text', parsed)
        return parsed, style

    def normalize(self, text: str) -> str:
        """문장을 정규화 합니다.
        1) 언어의 종류와 무관하게 공통적인 normalization
        2) 언어의 종류에 종속적인 normalization
        과정을 수행합니다.
        """

        # normalize by predefined normalize steps
        for step in self._nstep:
            text = step.value.normalize(text.strip())
            self._log(step.name, text)
            if text == '':
                break
        self._log('normalized text', text)
        return text

    def clean_old(self, text: str) -> str:
        """문장 내 character들의 유효성 여부에 따라 문자들을 정제합니다.
        유효하지 않은 문자는 삭제됩니다.
        """
        charlist = (MLCharacter(i, character) for i, character in enumerate(text))
        valids = (c.value if c.is_valid else ' ' for c in charlist)
        cleaned = ''.join(valids)
        cleaned = re.sub(TextProcessor.SPACES, ' ', cleaned)
        self._log('cleaned text', cleaned)
        cleaned = CleanStep.clean_residual.value.clean(cleaned.strip()) if cleaned != '' else cleaned
        return cleaned

    def clean(self, text: str) -> str:
        """문장 내 character들의 유효성 여부에 따라 문자들을 정제합니다.
        유효하지 않은 문자는 삭제됩니다.
        """
        #영어 Apostrophe 적용을 위해 ’ -> ' 치환
        text = text.replace("’", "'")
        charlist = (MLCharacter(i, character, self._language) for i, character in enumerate(text))
        valids = (c.value if c.is_valid else ' ' for c in charlist)
        cleaned = ''.join(valids)
        cleaned = re.sub(TextProcessor.SPACES, ' ', cleaned)
        self._log('cleaned text', cleaned)
        cleaned = CleanStep.clean_residual.value.clean(cleaned.strip()) if cleaned != '' else cleaned
        cleaned = cleaned.strip()
        return cleaned

    def pronounce(self, text: str) -> Union[str, List]:
        if self._g2p is not None:
            pronounced = self._g2p(text)
        else:
            pronounced = text
            logging.warning(f"Try to pronounce input string in {self._language}, but there are no g2p module for {self._language}.")
            logging.warning(f"If you want to use pronounce method for {self._language}, set `use_g2p` option as True.")
        self._log('pronunced text', pronounced)
        return pronounced

    def symbolize(self, text: Union[str, List], options: List = []) -> List[int]:
        """정규화된 문장의 끝에 eos를 추가하고, symbol화"""
        symbolized = self._symbolizer.symbolize(text, self._symbols, options)
        self._log('symbolized text', symbolized)
        return symbolized

    def input2symbol(self, text, options=[]):
        normalized = self.normalize(text)
        cleaned = self.clean(normalized)
        pronounced = self.pronounce(cleaned) if self._use_g2p else cleaned
        symbolized = self.symbolize(pronounced, options=options)
        return symbolized

    def split_punc(self, text: List, get_pure=False):
        """
            문장부호가 나타나는 그 이전 phoneme (자음+모음) 에 punctuation 정보를
            input: Text with punctuation (우와~ 너는 정말 마법을 잘 쓰는구나?)
            output:
                text : 우와 너 는 정 말 마 법 을 잘  쓰 는 구 나
                punc : 0 ~  0 0  0  0  0  0  0  0  0  0  0  ? (예시, 실제로는 phoneme 길이임)
        """
        # 아직 몇몇 종류의 TextProcssor에서는 반응하지 못합니다
        # Check Language
        assert self._language in [Language.korean, Language.japanese_prosody, Language.english_arpabet, Language.chinese, Language.taiwanese], "아직 몇몇 종류의 TextProcssor에서는 반응하지 못합니다"
        text = np.array(text)
        punc = np.zeros_like(text)
        pure_ids = []
        punc_chars = self._puncs
        key_text = [self._val2syms[k] for k in text]
        if self._language == Language.korean:
            # equal to split_text_punc (in data_utils.py)
            for idx, t in enumerate(key_text):
                if t in punc_chars:
                    if key_text[idx -1] in JAMO_TAILS:
                        # 종성 O
                        start = idx - 3
                    else:
                        # 종성 X
                        start = idx - 2
                    punc[start:idx] = self._symbols[t]
                    if not get_pure:
                        pure_ids.append(idx)
                else:
                    pure_ids.append(idx)
        elif self._language == Language.japanese_prosody:
            # VOWEL = jp_a/i/u/e/o
            for idx, t in enumerate(key_text):
                if t in punc_chars:
                    pivot = idx -  1
                    while idx > 0:
                        check = key_text[pivot].replace("jp_", "")
                        if check not in "[]aiueo":
                            break
                        else:
                            pivot -= 1
                    start = pivot
                    punc[start:idx] = self._symbols[t]
                    if not get_pure:
                        pure_ids.append(idx)
                else:
                    pure_ids.append(idx)

        elif self._language == Language.english_arpabet:
            # Punctuation Embedding as Word-level
            for idx, t in enumerate(key_text):
                if t in punc_chars:
                    pivot = idx
                    while pivot > 0:
                        if key_text[pivot] == " ":
                            break
                        else:
                            pivot -= 1
                    start = pivot + 1 if pivot > 0 else 0
                    punc[start:idx] = self._symbols[t]
                    if not get_pure:
                        pure_ids.append(idx)
                else:
                    pure_ids.append(idx)

        elif self._language == Language.chinese or self._language == Language.taiwanese:
            for idx, t in enumerate(key_text):
                if t in punc_chars:
                    pivot = idx - 1
                    flag = 0
                    while pivot > 0:
                        if "#" in key_text[pivot]:
                            if flag == 1:
                                break
                            else:
                                flag += 1
                                pivot -= 1
                        else:
                            pivot -= 1
                    flag = 0
                    start = pivot + 1 if pivot > 0 else 0
                    punc[start:idx] = self._symbols[t]
                    if not get_pure:
                        pure_ids.append(idx)
                else:
                    pure_ids.append(idx)
        else:
            raise Exception("지원하지 않는 언어에 대해 문장부호를 나누려고 하였습니다.")

        return text[pure_ids], punc[pure_ids], pure_ids

    def split_tone(self, text, punc=None, tag=None, get_pure=False):
        if not (self._language == Language.chinese or self._language == Language.taiwanese):
            return text, np.zeros_like(text), punc, tag, []

        text = np.array(text)
        tone = np.zeros_like(text)
        pure_ids = []
        tone_chars = {"_1": 1, "_2":2, "_3":3, "_4":4, "_5":5, "_6": 6}
        key_text = [self._val2syms[k] for k in text]

        for idx, t in enumerate(key_text):
            if t in tone_chars:
                # 중국어는 항상 자음 + 모음 입니다.
                start = idx - 2
                tone[start:idx] = tone_chars[t]
                if not get_pure:
                    pure_ids.append(idx)
            else:
                pure_ids.append(idx)


        return text[pure_ids], tone[pure_ids], punc[pure_ids] if punc is not None else punc, tag[pure_ids] if tag is not None else tag, pure_ids

    def split_style_tag(self, text, punc=None, tone=None, get_pure=True):
        ss = SpecialSymbols()
        text = np.array(text)
        tag = np.zeros_like(text)
        pure_ids = []
        tag_chars = ss._symbols
        key_text = [self._val2syms[k] for k in text]
        for idx, t in enumerate(key_text):
            if t in ss._ends:
                pivot = idx
                while pivot > 0:
                    if key_text[pivot] in ss._starts and (ss._ends[t] == ss._starts[ss.e2s[t]]):
                        break
                    else:
                        pivot -= 1
                start = pivot if pivot > 0 else 0
                tag[start:idx] = ss._ends[t]
                if not get_pure:
                    pure_ids.append(idx)
            elif t in ss._starts:
                if not get_pure:
                    pure_ids.append(idx)
                else: continue
            else:
                pure_ids.append(idx)

        return text[pure_ids], tag[pure_ids], punc[pure_ids] if punc is not None else punc, tone[pure_ids] if tone is not None else tone, pure_ids

    def _log(self, step: str, target):
        if self._logger is None:
            return
        logging.info('{:20} : {}'.format(step, target))

class MultiTextProcessor(object):
    """
    NOTE: CREATE BY MKYU (24.02.27)
        각 TextProcessor 간의 빈공간이 없도록 하기 위한 Multi-TextProcessor
        입력된 text-processor를 토대로 offset을 조정함
    """
    def __init__(self, processors: Dict):
        self.processors = processors
        self.len_default_syms = len({**CommonSymbols().sym2num}) + len({**SpecialSymbols().sym2num})
        self.default_offset = self.len_default_syms
        self.total_offset = 0
        self.lang_codes = {
            "ko": "korean",
            "en": "english",
            "ja": "japanese",
            "zh": "chinese",
            "tw": "taiwanese",
        }
        self.symbols = dict()
        self._adjust_offset()

    def _adjust_offset(self):
        self.total_offset = 0
        self._initialize_symbols()
        for lang, proc in sorted(self.processors.items()):
            curr_offset = self.total_offset
            for k, v in proc._symbols.items():
                if v >= self.default_offset:
                    proc._symbols[k] += curr_offset
            self.total_offset += len(list(proc._symbols)) - self.len_default_syms
            proc._val2syms = {v:k for k, v in proc._symbols.items()}
            self.symbols.update(proc._val2syms)
        if "english" in self.processors.keys() and "taiwanese" in self.processors.keys():
            self.processors["taiwanese"]._symbols.update(self.processors["english"]._symbols)
            self.processors["taiwanese"]._val2syms.update(self.processors["english"]._val2syms)

    def _initialize_symbols(self):
        for lang, proc in sorted(self.processors.items()):
            proc._symbols = {k: v for k, v in TextProcessor.LANG2SYMBOL[proc._language].items()}
            # print("initialized", proc._symbols)

    def _find_activated_language(self):
        return [processor._language for processor in self.processors.values()]

    def _show_sym2nums(self):
        for lang, proc in sorted(self.processors.items()):
            print(proc._symbols)

    def input2symbol(self, text, options=[], translator=None, language=None, code_switching=False, debug_mode=False):
        # translator 가 init에 있으면 NCTTS가 RuntimeError를 뱉음
        assert translator is not None or language is not None
        debug_log={}
        if translator is not None and language is None:
            detected_lang = translator.predict(text, k=1)[0][0][-2:]
            if (detected_lang == "zh" and "taiwanese" in self.processors) or language == "tw": # 중국어랑 대만어를 같이 학습하게 되면 어떻게 처리하지?
                detected_lang = "tw"
            detected_lang = self.lang_codes[detected_lang]
        elif translator is None and language is not None:
            detected_lang = language
        if code_switching:
            all_symbols = []
            sub_words, sub_langs = self.make_words(text, detected_lang)
            for idx in range(len(sub_words)):
                symbols = self.processors[sub_langs[idx]].input2symbol(sub_words[idx], options)
                # remove unnecessary period+EOS
                if symbols[-2:] == [7, 1] and idx != len(sub_words) - 1:
                    symbols = symbols[:-2]
                if (symbols[-1] == 1) and idx != len(sub_words) - 1:
                    symbols = symbols[:-1]
                all_symbols.extend(symbols)
            return all_symbols
        elif language=="taiwanese":
            normalized = self.processors[detected_lang].normalize(text)
            debug_log["tw_normalized"]=normalized        
            cleaned = self.processors[detected_lang].clean(normalized)
            debug_log["tw_clean"]=cleaned
            sub_words, sub_langs = self.make_words(cleaned, detected_lang)
            if "english" in sub_langs: # 영어 포함된 대만어
                all_symbols = []
                sym2num = {v: k for k, v in self.symbols.items()}
                for idx in range(len(sub_words)):
                    pronounced = self.processors[sub_langs[idx]].pronounce(sub_words[idx]) if self.processors[detected_lang]._use_g2p else cleaned
                    symbols= self.processors[sub_langs[idx]].symbolize(pronounced, options=options)
                    if symbols[-2:] == [7, 1] and idx != len(sub_words) - 1:
                        symbols = symbols[:-2]
                    if (symbols[-1] == 1) and idx != len(sub_words) - 1:
                        symbols = symbols[:-1]
                    all_symbols.extend(symbols)
                if debug_mode: print("\n".join([f"{k}: {v}" for k, v in debug_log.items()]))
                return all_symbols
            else:
                pronounced = self.processors[detected_lang].pronounce(cleaned) if self.processors[detected_lang]._use_g2p else cleaned
                symbolized = self.processors[detected_lang].symbolize(pronounced, options=options)
                if debug_mode: print("\n".join([f"{k}: {v}" for k, v in debug_log.items()]))
                return symbolized
        else:
            try:
                symbols = self.processors[detected_lang].input2symbol(text, options)
            except Exception as e:
                print(e)
                symbols = False
            return symbols

    def make_words(self, text, lang):
        """
            NOTE: CREATED BY seungje (24.02.16)
            NOTE: 현재 4개국어(한,중,영,일) 만 가능합니다.
        """
        sub_words = []
        sub_langs = []
        tmp = ''
        cur = None
        for c in text:
            if c in ENG:
                t_l = 'english'
            elif c in KOR:
                t_l = 'korean'
            elif c in JPN:
                t_l = 'japanese'
            elif c in SPECIAL_NOTES:
                t_l = cur
            else:
                t_l = lang
            if t_l == cur:
                tmp = tmp + c
            else:
                if cur == None:
                    cur = t_l
                    tmp = c
                elif cur == t_l:
                    tmp = tmp + c
                else:
                    sub_words.append(tmp)
                    sub_langs.append(cur)
                    tmp = c
                    cur = t_l
        sub_words.append(tmp)
        sub_langs.append(cur)
        return sub_words, sub_langs

def get_language_detector(light=True):
    if light:
        ext = "ftz"
    else:
        ext = "bin"
    # package_path = "/".join(importlib.util.find_spec("nctp").origin.split("/")[:-2] + [f"lid.176.{ext}"])
    package_path = f"{NCTTS_TM}/language_detector/lid.176.{ext}"


    model = fasttext.load_model(package_path)
    return model

if __name__ == '__main__':
    import jamo
    processor = {
            'korean': TextProcessor(
                language=Language.korean,
                normalize_step="default"),
            'english': TextProcessor(
                language="english_arpabet", normalize_step="default", use_g2p=True),
            # 'english': TextProcessor(
            #     language=Language.english, normalize_step="default"),
            'japanese': TextProcessor('japanese_prosody', "default", use_g2p=True),
            'taiwanese': TextProcessor("taiwanese", "baker", use_g2p=True)
        }
    m_proc = MultiTextProcessor(processor)
    m_proc._show_sym2nums()
    # x = "너 제법 쓸모있구나? [g]하하하하![/g] [s]나, 나, 나랑[/s] 같이 일해볼 생각, 정말 없어?"
    # x = "右蛮#1舞#1袅袅#3，左琼#2歌#1昔昔#4。"
    # # x = "Like~ an unquenchable flame... it fights fiercely and survives until the end."
    # translator = get_language_detector()
    # model = fasttext.load_model("/SGV/users/mkyu/share/lid.176.bin")
    # out1 = model.predict("背包太重的話，就去倉庫那吧。", k=1)[0][0][-2:]
    # out2 = translator.predict("背包太重的話，就去倉庫那吧。", k=1)[0][0][-2:]

    ## Test
    x = "随后#1上场的#1林超攀#2出现#1重大#1失误#4.|sui2 hou4 shang4 chang3 de5 lin2 chao1 pan1 chu2 xian4 zhong4 da4 shi1 wu4"
    norm_x = m_proc.processors["taiwanese"].normalize(x)
    print(norm_x)
    print(m_proc.processors['taiwanese'].symbolize(norm_x))

    import json
    from tqdm import tqdm
    align1 = json.load(open("/SGV/NC-TTS/ttsdb/NC_Taiwan/NctFemale001/v0/alignment.json", 'r', encoding='utf-8')).values()
    align2 = json.load(open("/SGV/NC-TTS/ttsdb/NC_Taiwan/NctFemale002/v0/alignment.json", 'r', encoding='utf-8')).values()
    aligns = list(align1) + list(align2)

    new_pinyin = []
    for line in aligns:
        try:
            norm_x = m_proc.processors["taiwanese"].normalize(line)
            # x = m_proc.processors["taiwanese"].symbolize(norm_x)
        except:
            pass
    # norm_x = m_proc.processors['chinese'].normalize(x)
    # print("???", norm_x)
    # norm_x = m_proc.processors['chinese'].pronounce(norm_x)
    # print("o o", norm_x)
    raise
    print(translator.predict(re.sub(r"#[0-9]", "", x)))

    x = m_proc.processors['chinese'].input2symbol(x)


    x, punc = m_proc.processors['chinese'].split_punc(x, get_pure=True)
    print("split_punc", x, punc)
    x, tone, punc, tag = m_proc.processors['chinese'].split_tone(x, punc=punc, get_pure=True)
    print("split_tone", x, tone, punc)
    x, tag, punc, tone = m_proc.processors['chinese'].split_style_tag(x, punc=punc, tone=tone, get_pure=True)
    print("split tag", x, tone, punc, tag)
    # print(m_proc._find_activated_language())
    # m_proc._adjust_offset()
    # m_proc._show_sym2nums()

    # x = m_proc.processors['japanese'].normalize("みんなお疲れ様でした。 帰りましょう、 私たちの要塞に！")
    # print("jp normalized", x)
    # x = m_proc.processors['japanese'].clean(x)
    # print("jp cleaned", x)
    # x = m_proc.processors['japanese'].pronounce(x)
    # print(x)

    # # print(m_proc.processors["english"].pronounce("Hello? This is president! Thank you!"))

    # # print(m_proc.processors['korean'].split_punc(m_proc.processors['korean'].symbolize(jamo.h2j("우와~ 너는 정말 삼겹살, 소고기, 양고기 모두 좋아하는 돼지구나!")), get_pure=True))
    # print(m_proc.processors['japanese'].split_punc(m_proc.processors['japanese'].symbolize(x), get_pure=True))
    # print(m_proc.processors['english'].split_punc(m_proc.processors["english"].symbolize(m_proc.processors["english"].pronounce("Hello? This is president! Thank you!")), get_pure=True))

    # x = m_proc.processors["chinese"].normalize("武术都是时代的精粹")
    # print("normalize", x)
    # x = m_proc.processors["chinese"].clean(x)
    # print("clean", x)
    # x = m_proc.processors["chinese"].pronounce(x)
    # print("g2p", x)
    # x = m_proc.processors["chinese"].symbolize(x)
    # print("syms", x)
    # x, punc = m_proc.processors['chinese'].split_punc(x, get_pure=True)
    # print("split_punc", x, punc)
    # x, tone, punc, tag = m_proc.processors['chinese'].split_tone(x, punc=punc, get_pure=True)
    # print("split_tone", x, tone, punc)
    # x, tone, punc, tag = m_proc.processors['chinese'].split_style_tag(x, punc=punc, tone=tone, get_pure=True)
    # print("split tag", x, tone, punc, tag)
    # print(len(x), len(punc), len(tone))

    # sample = 'このとき, My name is 김택진 from 엔씨소프트. 잘 부탁드립니다.'
    # sample = "오늘 조셉스테이크에 가서 맛있는 스테이크를 먹었습니다~"
    # sample = "すでに邦訳のある 黒い時計の旅 などに先駆けて、氏の手法が最初に開花した作品だという."
    # # sample = "Hello? This is president! ..Thank you!"
    # print(m_proc.processors["english"].pronounce(sample))
    # from googletrans import Translator
    # translator = Translator()
    # sample_out = m_proc.input2symbol(sample, [], translator=translator, code_switching=True)
    # print(sample_out)

    # out = m_proc.input2symbol("그... 있잖아 피터, 너와 모험하며 생각해 봤는데 어른이 된다는 건 최고의 모험일지도 몰라.", translator=translator)
    # out, punc = m_proc.processors['korean'].split_punc(out, get_pure=True)
    # print(out, punc)
    # import pickle
    # from nctp.ncg2pe.pronounce import EnG2pHolder
    # pickle.dump(EnG2pHolder(category="arpabet"), open("/SGV/users/mkyu/tmp.pkl", 'wb'))

    """processes = ['patterns', 'number', 'etc_dictionary', 'eng_dictionary', 'english', 'character',
                 'pronunciation', 'period']
    sample_korean_text = '0:9;(0.7)감자골a     감asdf자 감자ㅋㅋㅋㅋ.'
    sample_korean_text2 = '구름 위를 날아가는 ~#~!@#$@^#$%&^&(%^)ㅣㅏㅁㄴ;어ㅜㅍㅋㅌ'
    sample_korean_texts = [sample_korean_text, sample_korean_text2]

    def test_dump(processor: TextProcessor, text: str):
        parsed, _ = processor.parse(text)
        normalized = processor.normalize(parsed)
        cleaned = processor.clean(normalized)
        symbolized = processor.symbolize(cleaned)
        print(text)
        print(json.dumps(parsed, indent=4, ensure_ascii=False))
        print(json.dumps(normalized, indent=4, ensure_ascii=False))
        print(json.dumps(cleaned, indent=4, ensure_ascii=False))
        print(json.dumps(symbolized, ensure_ascii=False))

    ktp = TextProcessor(Language.korean)
    etp = TextProcessor(Language.english)
    test_dump(ktp, sample_korean_text)
    test_dump(ktp, sample_korean_text2)
    # test_dump(etp, sample_english_text)

    # Example: process text
    def input2text(processor: TextProcessor, text: str) -> str:
        parsed, _ = processor.parse(text)
        normalized = processor.normalize(parsed)
        return processor.clean(normalized)

    # Example: extract character list from text
    def input2chlist(processor: TextProcessor, text: str) -> Tuple[List[Character], List[Character]]:
        before = [Character(i, character) for i, character in enumerate(text)]
        parsed, _ = processor.parse(text)
        normalized = processor.normalize(parsed)
        after = [Character(i, character) for i, character in enumerate(normalized)]
        return before, after

    # Example: convert input text to symbols
    def input2symbol(processor: TextProcessor, text: str) -> List[int]:
        parsed, _ = processor.parse(text)
        normalized = processor.normalize(parsed)
        cleaned = processor.clean(normalized)
        return processor.symbolize(cleaned)

    # Example: process text
    print(sample_korean_text)
    print(input2text(ktp, sample_korean_text))

    # Example: extract character list from text
    before, after = input2chlist(ktp, sample_korean_text)
    print(before)
    print(after)

    # Example: convert input text to symbols
    print(input2symbol(ktp, sample_korean_text))

    # Example: convert input text to symbols with custom pattern for dealing with repititive special characters.
    def input2symbol_custompattern(processor: TextProcessor, text: str) -> List[int]:
        parsed, _ = processor.parse(text)
        normalized = processor.normalize(parsed)
        cleaned = processor.clean(normalized, )
        return processor.symbolize(cleaned)
    """
