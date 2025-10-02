import re
import logging

from packaging.version import parse as V
from typing import Iterable, List, Optional, Union

import inflect
import string
from typing import Union
from copy import copy
# from nctp.japanese import JPN_SYMBOLS
# from nctp.symbols import SYMBOLS, SPACE
# from nctp.common import strip_diacritics
import pyopenjtalk
import pykakasi
import difflib


SPECIAL_NOTES = '。、？！.;；:,，:?!~-😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉😭😢🤐🐢🍊🍋 '
SPECIAL_NOTES_PATTERN = r"[。、？！.;：；:,，:?!~\-😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉😭😢🤐🐢🍊🍋 ]"

x2_consonant = {"sh": "S", "ry": "R", "ts": "T", "ny": "W", "gy": "G", "ky": "K", "ch": "C", "hy": "H", "mu": "M", "by":"B", "py": "P", "dy":"D", "ty":"Q", "cl": "X"}
x2_consonant_rev = {v:k for k, v in x2_consonant.items()}


alp = r"[a-zA-Z]+"

def print_diff(text1, text2):
    # difflib에서 제공하는 비교 객체 생성
    text1 = text1.lower()
    text2 = text2.lower()
    d = difflib.Differ()
    diff = list(d.compare(text1, text2))

    # # 틀린 부분 상세하게 출력
    print(f"Text1: {''.join(text1)}")
    print(f"Text2: {''.join(text2)}")
    print(diff)
    # # 틀린 부분 상세 출력

    new_line = ""
    for i, line in enumerate(diff):
        prefix = line[0]
        content = line[2:]
        # if content == "_": continue
        if prefix == '-':
            print(f"Text2 ({i}): {''.join(content)}")
            if re.match(alp, content):
                continue
            elif content == "_":
                continue
            else:
                new_line += "_"+content+"_"
        elif prefix == '+':
            print(f"Text2 ({i}): {''.join(content)}")
            if content == " ": continue

            new_line += content
        else:
            new_line += content
    return new_line

def print_diff2(text1, text2):
    # 두 텍스트를 difflib.SequenceMatcher를 사용하여 비교
    org_text1 = text1
    org_text2 = text2
    text1 = text1.lower()
    text2 = text2.lower()
    sequence_matcher = difflib.SequenceMatcher(None, text1, text2)
    opcodes = sequence_matcher.get_opcodes()
    
    # 두 텍스트의 길이를 같게 만들기 위한 새로운 리스트 생성
    aligned_text1 = []
    aligned_text2 = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'replace':
            for k in range(max(i2 - i1, j2 - j1)):
                if i1 + k < i2:
                    aligned_text1.append(org_text1[i1 + k])
                    # aligned_text1.append("_")
                else:
                    aligned_text1.append('_')
                if j1 + k < j2:
                    aligned_text2.append(org_text2[j1 + k])
                    # aligned_text2.append("_")
                else:
                    aligned_text2.append('_')
        elif tag == 'equal':
            aligned_text1.extend(org_text1[i1:i2])
            aligned_text2.extend(org_text2[j1:j2])
        elif tag == 'delete':
            aligned_text1.extend(org_text1[i1:i2])
            aligned_text2.extend(['_'] * (i2 - i1))
        elif tag == 'insert':
            aligned_text1.extend(['_'] * (j2 - j1))
            aligned_text2.extend(org_text2[j1:j2])
    
    # 남은 부분 추가
    aligned_text1 = ''.join(aligned_text1)
    aligned_text2 = ''.join(aligned_text2)

    # 두 텍스트의 길이를 같게 맞춤
    max_len = max(len(aligned_text1), len(aligned_text2))
    aligned_text1 = aligned_text1.ljust(max_len, '_')
    aligned_text2 = aligned_text2.ljust(max_len, '_')
    
    return aligned_text1, aligned_text2

def _extract_fullcontext_label(text):

    if V(pyopenjtalk.__version__) >= V("0.3.0"):
        return pyopenjtalk.make_label(pyopenjtalk.run_frontend(text))
    else:
        return pyopenjtalk.run_frontend(text)[1]

def _numeric_feature_by_regex(regex, s):
    match = re.search(regex, s)
    if match is None:
        return -50
    return int(match.group(1))

def pyopenjtalk_g2p_prosody(text: str, drop_unvoiced_vowels: bool = True) -> List[str]:
    """Extract phoneme + prosoody symbol sequence from input full-context labels.

    The algorithm is based on `Prosodic features control by symbols as input of
    sequence-to-sequence acoustic modeling for neural TTS`_ with some r9y9's tweaks.

    Args:
        text (str): Input text.
        drop_unvoiced_vowels (bool): whether to drop unvoiced vowels.

    Returns:
        List[str]: List of phoneme + prosody symbols.

    Examples:
        >>> from espnet2.text.phoneme_tokenizer import pyopenjtalk_g2p_prosody
        >>> pyopenjtalk_g2p_prosody("こんにちは。")
        ['^', 'k', 'o', '[', 'N', 'n', 'i', 'ch', 'i', 'w', 'a', '$']

    .. _`Prosodic features control by symbols as input of sequence-to-sequence acoustic
        modeling for neural TTS`: https://doi.org/10.1587/transinf.2020EDP7104

    """
    def fix_longer_sym(text):
        # 장음 앞에 빈칸이 오는 경우를 제거
        return re.sub(r" +ー", "ー", text)
    text = text.replace('、 ', '、').replace('。 ', '。').replace(' ', '、')
    text = fix_longer_sym(text)
    kks = pykakasi.kakasi()
    puncs = [x for x in text if x in SPECIAL_NOTES]
    text = re.sub(SPECIAL_NOTES_PATTERN, " ", text)
    ss = kks.convert(text)
    y = "".join(x['hepburn'].lower() if x['orig'] not in SPECIAL_NOTES else x['orig'] for x in ss).replace("'", "")
    for k, v in x2_consonant.items():
        y = y.replace(k, v)
    y = "_".join([sym if sym != " " else puncs.pop(0) for sym in y ])
    labels = _extract_fullcontext_label(text)
    # puncs = re.findall(r"[。、？！.;：；:,，:?!~\-😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉🐢🍊🍋 ']", text)

    N = len(labels)
    phones = []
    tmp_phones = []
    for n in range(N):
        lab_curr = labels[n]
        # current phoneme
        p3 = re.search(r"\-(.*?)\+", lab_curr).group(1)
        if p3 in x2_consonant:
            p3 = x2_consonant[p3]
        # deal unvoiced vowels as normal vowels
        if drop_unvoiced_vowels and p3 in "AEIOU":
            p3 = p3.lower()
        # deal with sil at the beginning and the end of text
        if p3 == "sil":
            continue
        elif p3 == "pau":
            tmp_phones.append(" ")
            continue
        else:
            phones.append(p3)
            tmp_phones.append(p3)

        # accent type and position info (forward or backward)
        a1 = _numeric_feature_by_regex(r"/A:([0-9\-]+)\+", lab_curr)
        a2 = _numeric_feature_by_regex(r"\+(\d+)\+", lab_curr)
        a3 = _numeric_feature_by_regex(r"\+(\d+)/", lab_curr)

        # number of mora in accent phrase
        f1 = _numeric_feature_by_regex(r"/F:(\d+)_", lab_curr)

        a2_next = _numeric_feature_by_regex(r"\+(\d+)\+", labels[n + 1])
        # accent phrase border
        if a3 == 1 and a2_next == 1 and p3 in "aeiouAEIOUNcl":
            phones.append("#")
        # pitch falling
        elif a1 == 0 and a2_next == a2 + 1 and a2 != f1:
            phones.append("]")
        # pitch rising
        elif a2 == 1 and a2_next == 2:
            phones.append("[")
        
    tmp_phones = "_".join(tmp_phones)
    if y[0] == "🍊"  and y[-1] == "🍋":
        tmp_phones = "🍊_" + tmp_phones + "_🍋"
    a, b = print_diff2(y, tmp_phones)

    a = list(a)
    b = list(b)

    for i, (_,_) in enumerate(zip(a,b)):
        if a[i] in SPECIAL_NOTES:
            if re.match(r"[a-zA-Z]", b[i] ) is not None:
                b[i] = f"_{a[i]}_{b[i]}"
            else:
                b[i] = a[i]
    b = "".join(b).replace("。", ".").replace("，", ",").replace("、", ",").replace("？", "?").replace("！", "!").replace("：", ",")
    prosodic = "_".join(phones)

    a, b = print_diff2(prosodic, b)

    a = list(a.replace("_", ""))
    b = list(b.replace("_", ""))
    # a가 풀 음소를 갖고 있기 때문에 같은 인덱스에 a[i]가 b[i]에 없는 경우 삽입할 것.
    new_sequence = list()
    
    i = 0
    j = 0
    burden = 0

    while True:
        # 두 문자열 정렬하여 prosodic label (#[]) 삽입
        cur_a = a[i]
        cur_b = b[j]

        if cur_a == cur_b:
            i += 1
            j += 1
            new_sequence.append(cur_a)
        if cur_a in "#[]":
            new_sequence.append(cur_a)
            i += 1
        if cur_b in SPECIAL_NOTES:
            new_sequence.append(cur_b)
            j += 1
        if i >= len(a):
            new_sequence.extend(b[j:])
            break
        elif j >= len(b):
            new_sequence.extend(a[i:])
            break 
        burden += 1
        if burden > 2000:
            # 정렬에 실패한 경우 (보통 알파벳 시퀀스가 불일치 하는 경우임)
            # 이 경우 pyopenjtalk 결과를 리턴함
            if y[0] == "🍊"  and y[-1] == "🍋":
                out = ["🍊"] + phones + ["🍋"]
            else:
                out = phones
            return out

    # 쉼표가 앞뒤로 딱 붙은 경우(알파벳 + 쉼표 + 알파벳),
    # 매끄러운 발음을 위해 공백 추가(알파벳 + 쉼표 + 공백 + 알파벳)
    text = ''.join(new_sequence).replace(',,', ',')
    text = re.sub(r'🐢+', '~', text) # ...이 거북이 심볼로 바뀌는데, 좀 더 잘 먹도록 ~로 바꿔줌
    new_sequence = list(re.sub(
        r'(?<=[a-zA-Z\~])([,.])(?=[a-zA-Z])',
        lambda m: m.group(1) + ' ', text # , 또는 . 인 경우 뒤에 공백 붙이기
    ))

    return new_sequence


class JpnG2pHolder:
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        return obj

    def __init__(self, category, *args, **kwargs):
        self.category = self._validate_category(category)
        self._build_g2p()
        self.g2p = self._set_g2p()

    def _validate_category(self, category):
        assert category == "prosody", logging.info(f"This phoneme category of english is not allowed : {self.category}.")
        return category

    def _build_g2p(self):
        self.g2p_class = {
            "prosody": JpnProG2p()
            }

    def _set_g2p(self):
        return self.g2p_class[self.category]

    def __call__(self, text):
        return self.g2p(text)


class JpnProG2p():
    def __init__(self):
        # self.symb_list = [s for s in SYMBOLS]
        super().__init__()

    def __call__(self, text):
        pronounced = pyopenjtalk_g2p_prosody(text)  # dummy for first punc
        for i in range(len(pronounced)):
            if pronounced[i] not in SPECIAL_NOTES and pronounced[i] != " ":
                if pronounced[i] in x2_consonant_rev:
                    pronounced[i] = x2_consonant_rev[pronounced[i]]
                pronounced[i] = 'jp_' + pronounced[i]
        pronounced = [sym for sym in pronounced if sym != ""]        
        return pronounced
    

if __name__ == "__main__":
    # from nctp.common import remove_bracket
    # from nctp.text_processor import TextProcessor
    # from nctp.common import Language
    # from nctp.common import NormalizeStep
    # import pykakasi
    # from nctp.japanese import convert_number_to_hiragana_in_text
    import kanjize
    import re

    def convert_number_to_hiragana_in_text(text):
        # 정규 표현식을 사용하여 문장에서 숫자 부분을 추출
        def replace_number_with_hiragana(match):
            number = int(match.group(0))
            kanji_str = kanjize.number2kanji(number)
            # hiragana_str = kanjize.kanji2hiragana(kanji_str)
            # return hiragana_str
            return kanji_str
        
        # 모든 숫자 부분을 변환
        converted_text = re.sub(r'\d+', replace_number_with_hiragana, text)
        return converted_text

    # tp = TextProcessor('japanese_prosody', "default", use_g2p=True)
    g2p = JpnProG2p()
    # # print(tp._symbols)
    # # print(g2p(remove_bracket("その知らせを聞いた人々は皆、李舜臣（イ・スンシン）を気を毒に思った。")))
    kks = pykakasi.kakasi()
    # result = kks.convert("これらの多くは1950年代にディズニー, スタジオの主要ライバルであったUPAの設立に参加した。")
    # print(result)
    # # print(g2p(remove_bracket("その知らせを聞いた人？々は皆、李舜臣（イ・スンシン）、を気を毒に！思った。")))
    # print(tp.symbolize(g2p(remove_bracket("逓伝哨には、乗馬伝令による逓騎哨、自転車による逓自転車哨などの種類がある."))))
    # print(g2p("君がいなければまた金床の前に 立つことは無かっただろう！ 任せてくれ、 ベストを尽くそう！"))
    # text = "かすかに聞こえてくる~1931年版の讃美歌~が? 次第に大きくなっていく."
    # text = "ルールーコウという名は,中国にはない."
    # # norm_text = convert_number_to_hiragana_in_text(text)
    # # # norm_text = tp.normalize("同じ料理じゃないですよ。 うちの料理の方が美味しいです！")
    # # # norm_text = tp.normalize(text)
    # # norm_text = tp.clean(norm_text)
    # print(norm_text)
    # pron_text = tp.pronounce(norm_text)
    # sym = tp.symbolize(pron_text)
    # print(sym)
    # sym = tp.input2symbol(text)
    # print(norm_text)
    
    # text = " "
    print(g2p("ルールーコウという名は,中国にはない."))
    

    # print(kks.convert(text))
    # print(tp.input2symbol(text))
    # x = "".join(x['hepburn'] for x in kks.convert("秋葉原には,電気屋がたくさんあります. "))
    # print(x)
    # print(g2p(" 君は誰ですか?"))
    # print(pyopenjtalk.g2p(" 君は誰ですか？"))
    # print(g2p("君は誰ですか?"))
    # # print(g2p("".join(item['hira'] for item in result)))
    # for f in pyopenjtalk.run_frontend("あ、逓伝哨には、乗馬伝令による逓騎哨、自転車による逓自転車哨などの種類がある."):
    # import pykakasi
    # kks = pykakasi.kakasi()
    # x = ""
    # for f in pyopenjtalk.run_frontend("何の人形が出てくるか、わかりません! それでも買いますか？"):
    #     x += " "+kks.convert(f['pron'])[0]['hepburn'] 
    #     # print(f)
    #     print(f['string'], f['pron'], kks.convert(f['pron'])[0]['hepburn'])
    # print(x)
    # y = ""
    # for r in pyopenjtalk.g2p("!!何君は誰ですか？").split(" "):
    #     y += r if r != "pau" else ""
    # print(y)
    # print(pyopenjtalk.run_frontend("逓伝哨には、乗馬伝令による逓騎哨、自転車による逓自転車哨などの種類がある."))