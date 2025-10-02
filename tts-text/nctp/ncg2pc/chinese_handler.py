# -*- coding: utf-8 -*-
# Copyright 2020 TensorFlowTTS Team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Perform preprocessing and raw feature extraction for Baker dataset."""

import os
import re
from typing import Dict, List, Union, Tuple, Any

import librosa
import numpy as np
import soundfile as sf
from dataclasses import dataclass, field
from pypinyin import Style
from pypinyin.contrib.neutral_tone import NeutralToneWith5Mixin
from pypinyin.converter import DefaultConverter
from pypinyin.core import Pinyin
# p = Pinyin()

_pad = ["pad"]
_eos = ["eos"]
_pause = ["sil", "#0", "#1", "#2", "#3"]

_initials = [
    "^",
    "b",
    "c",
    "ch",
    "d",
    "f",
    "g",
    "h",
    "j",
    "k",
    "l",
    "m",
    "n",
    "p",
    "q",
    "r",
    "s",
    "sh",
    "t",
    "x",
    "z",
    "zh",
]

_tones = ["1", "2", "3", "4", "5"]

_finals = [
    "a",
    "ai",
    "an",
    "ang",
    "ao",
    "e",
    "ei",
    "en",
    "eng",
    "er",
    "i",
    "ia",
    "ian",
    "iang",
    "iao",
    "ie",
    "ii",
    "iii",
    "in",
    "ing",
    "iong",
    "iou",
    "o",
    "ong",
    "ou",
    "u",
    "ua",
    "uai",
    "uan",
    "uang",
    "uei",
    "uen",
    "ueng",
    "uo",
    "v",
    "van",
    "ve",
    "vn",
]

PINYIN_DICT = {
    "a": ("^", "a"),
    "ai": ("^", "ai"),
    "an": ("^", "an"),
    "ang": ("^", "ang"),
    "ao": ("^", "ao"),
    "ba": ("b", "a"),
    "bai": ("b", "ai"),
    "ban": ("b", "an"),
    "bang": ("b", "ang"),
    "bao": ("b", "ao"),
    "be": ("b", "e"),
    "bei": ("b", "ei"),
    "ben": ("b", "en"),
    "beng": ("b", "eng"),
    "bi": ("b", "i"),
    "bian": ("b", "ian"),
    "biao": ("b", "iao"),
    "bie": ("b", "ie"),
    "bin": ("b", "in"),
    "bing": ("b", "ing"),
    "bo": ("b", "o"),
    "bu": ("b", "u"),
    "ca": ("c", "a"),
    "cai": ("c", "ai"),
    "can": ("c", "an"),
    "cang": ("c", "ang"),
    "cao": ("c", "ao"),
    "ce": ("c", "e"),
    "cen": ("c", "en"),
    "ceng": ("c", "eng"),
    "cha": ("ch", "a"),
    "chai": ("ch", "ai"),
    "chan": ("ch", "an"),
    "chang": ("ch", "ang"),
    "chao": ("ch", "ao"),
    "che": ("ch", "e"),
    "chen": ("ch", "en"),
    "cheng": ("ch", "eng"),
    "chi": ("ch", "iii"),
    "chong": ("ch", "ong"),
    "chou": ("ch", "ou"),
    "chu": ("ch", "u"),
    "chua": ("ch", "ua"),
    "chuai": ("ch", "uai"),
    "chuan": ("ch", "uan"),
    "chuang": ("ch", "uang"),
    "chui": ("ch", "uei"),
    "chun": ("ch", "uen"),
    "chuo": ("ch", "uo"),
    "ci": ("c", "ii"),
    "cong": ("c", "ong"),
    "cou": ("c", "ou"),
    "cu": ("c", "u"),
    "cuan": ("c", "uan"),
    "cui": ("c", "uei"),
    "cun": ("c", "uen"),
    "cuo": ("c", "uo"),
    "da": ("d", "a"),
    "dai": ("d", "ai"),
    "dan": ("d", "an"),
    "dang": ("d", "ang"),
    "dao": ("d", "ao"),
    "de": ("d", "e"),
    "dei": ("d", "ei"),
    "den": ("d", "en"),
    "deng": ("d", "eng"),
    "di": ("d", "i"),
    "dia": ("d", "ia"),
    "dian": ("d", "ian"),
    "diao": ("d", "iao"),
    "die": ("d", "ie"),
    "ding": ("d", "ing"),
    "diu": ("d", "iou"),
    "dong": ("d", "ong"),
    "dou": ("d", "ou"),
    "du": ("d", "u"),
    "duan": ("d", "uan"),
    "dui": ("d", "uei"),
    "dun": ("d", "uen"),
    "duo": ("d", "uo"),
    "e": ("^", "e"),
    "ei": ("^", "ei"),
    "en": ("^", "en"),
    "ng": ("^", "en"),
    "eng": ("^", "eng"),
    "er": ("^", "er"),
    "fa": ("f", "a"),
    "fan": ("f", "an"),
    "fang": ("f", "ang"),
    "fei": ("f", "ei"),
    "fen": ("f", "en"),
    "feng": ("f", "eng"),
    "fo": ("f", "o"),
    "fou": ("f", "ou"),
    "fu": ("f", "u"),
    "ga": ("g", "a"),
    "gai": ("g", "ai"),
    "gan": ("g", "an"),
    "gang": ("g", "ang"),
    "gao": ("g", "ao"),
    "ge": ("g", "e"),
    "gei": ("g", "ei"),
    "gen": ("g", "en"),
    "geng": ("g", "eng"),
    "gong": ("g", "ong"),
    "gou": ("g", "ou"),
    "gu": ("g", "u"),
    "gua": ("g", "ua"),
    "guai": ("g", "uai"),
    "guan": ("g", "uan"),
    "guang": ("g", "uang"),
    "gui": ("g", "uei"),
    "gun": ("g", "uen"),
    "guo": ("g", "uo"),
    "ha": ("h", "a"),
    "hai": ("h", "ai"),
    "han": ("h", "an"),
    "hang": ("h", "ang"),
    "hao": ("h", "ao"),
    "he": ("h", "e"),
    "hei": ("h", "ei"),
    "hen": ("h", "en"),
    "heng": ("h", "eng"),
    "hong": ("h", "ong"),
    "hou": ("h", "ou"),
    "hu": ("h", "u"),
    "hua": ("h", "ua"),
    "huai": ("h", "uai"),
    "huan": ("h", "uan"),
    "huang": ("h", "uang"),
    "hui": ("h", "uei"),
    "hun": ("h", "uen"),
    "huo": ("h", "uo"),
    "ji": ("j", "i"),
    "jia": ("j", "ia"),
    "jian": ("j", "ian"),
    "jiang": ("j", "iang"),
    "jiao": ("j", "iao"),
    "jie": ("j", "ie"),
    "jin": ("j", "in"),
    "jing": ("j", "ing"),
    "jiong": ("j", "iong"),
    "jiu": ("j", "iou"),
    "ju": ("j", "v"),
    "juan": ("j", "van"),
    "jue": ("j", "ve"),
    "jun": ("j", "vn"),
    "ka": ("k", "a"),
    "kai": ("k", "ai"),
    "kan": ("k", "an"),
    "kang": ("k", "ang"),
    "kao": ("k", "ao"),
    "ke": ("k", "e"),
    "kei": ("k", "ei"),
    "ken": ("k", "en"),
    "keng": ("k", "eng"),
    "kong": ("k", "ong"),
    "kou": ("k", "ou"),
    "ku": ("k", "u"),
    "kua": ("k", "ua"),
    "kuai": ("k", "uai"),
    "kuan": ("k", "uan"),
    "kuang": ("k", "uang"),
    "kui": ("k", "uei"),
    "kun": ("k", "uen"),
    "kuo": ("k", "uo"),
    "la": ("l", "a"),
    "lai": ("l", "ai"),
    "lan": ("l", "an"),
    "lang": ("l", "ang"),
    "lao": ("l", "ao"),
    "le": ("l", "e"),
    "lei": ("l", "ei"),
    "leng": ("l", "eng"),
    "li": ("l", "i"),
    "lia": ("l", "ia"),
    "lian": ("l", "ian"),
    "liang": ("l", "iang"),
    "liao": ("l", "iao"),
    "lie": ("l", "ie"),
    "lin": ("l", "in"),
    "ling": ("l", "ing"),
    "liu": ("l", "iou"),
    "lo": ("l", "o"),
    "long": ("l", "ong"),
    "lou": ("l", "ou"),
    "lu": ("l", "u"),
    "lv": ("l", "v"),
    "luan": ("l", "uan"),
    "lve": ("l", "ve"),
    "lue": ("l", "ve"),
    "lun": ("l", "uen"),
    "luo": ("l", "uo"),
    "ma": ("m", "a"),
    "mai": ("m", "ai"),
    "man": ("m", "an"),
    "mang": ("m", "ang"),
    "mao": ("m", "ao"),
    "me": ("m", "e"),
    "mei": ("m", "ei"),
    "men": ("m", "en"),
    "meng": ("m", "eng"),
    "mi": ("m", "i"),
    "mian": ("m", "ian"),
    "miao": ("m", "iao"),
    "mie": ("m", "ie"),
    "min": ("m", "in"),
    "ming": ("m", "ing"),
    "miu": ("m", "iou"),
    "mo": ("m", "o"),
    "mou": ("m", "ou"),
    "mu": ("m", "u"),
    "n": ("^", "en"), # edit by mkyu
    "na": ("n", "a"),
    "nai": ("n", "ai"),
    "nan": ("n", "an"),
    "nang": ("n", "ang"),
    "nao": ("n", "ao"),
    "ne": ("n", "e"),
    "nei": ("n", "ei"),
    "nen": ("n", "en"),
    "neng": ("n", "eng"),
    "ni": ("n", "i"),
    "nia": ("n", "ia"),
    "nian": ("n", "ian"),
    "niang": ("n", "iang"),
    "niao": ("n", "iao"),
    "nie": ("n", "ie"),
    "nin": ("n", "in"),
    "ning": ("n", "ing"),
    "niu": ("n", "iou"),
    "nong": ("n", "ong"),
    "nou": ("n", "ou"),
    "nu": ("n", "u"),
    "nv": ("n", "v"),
    "nuan": ("n", "uan"),
    "nve": ("n", "ve"),
    "nue": ("n", "ve"),
    "nuo": ("n", "uo"),
    "o": ("^", "o"),
    "ou": ("^", "ou"),
    "pa": ("p", "a"),
    "pai": ("p", "ai"),
    "pan": ("p", "an"),
    "pang": ("p", "ang"),
    "pao": ("p", "ao"),
    "pe": ("p", "e"),
    "pei": ("p", "ei"),
    "pen": ("p", "en"),
    "peng": ("p", "eng"),
    "pi": ("p", "i"),
    "pian": ("p", "ian"),
    "piao": ("p", "iao"),
    "pie": ("p", "ie"),
    "pin": ("p", "in"),
    "ping": ("p", "ing"),
    "po": ("p", "o"),
    "pou": ("p", "ou"),
    "pu": ("p", "u"),
    "qi": ("q", "i"),
    "qia": ("q", "ia"),
    "qian": ("q", "ian"),
    "qiang": ("q", "iang"),
    "qiao": ("q", "iao"),
    "qie": ("q", "ie"),
    "qin": ("q", "in"),
    "qing": ("q", "ing"),
    "qiong": ("q", "iong"),
    "qiu": ("q", "iou"),
    "qu": ("q", "v"),
    "quan": ("q", "van"),
    "que": ("q", "ve"),
    "qun": ("q", "vn"),
    "ran": ("r", "an"),
    "rang": ("r", "ang"),
    "rao": ("r", "ao"),
    "re": ("r", "e"),
    "ren": ("r", "en"),
    "reng": ("r", "eng"),
    "ri": ("r", "iii"),
    "rong": ("r", "ong"),
    "rou": ("r", "ou"),
    "ru": ("r", "u"),
    "rua": ("r", "ua"),
    "ruan": ("r", "uan"),
    "rui": ("r", "uei"),
    "run": ("r", "uen"),
    "ruo": ("r", "uo"),
    "sa": ("s", "a"),
    "sai": ("s", "ai"),
    "san": ("s", "an"),
    "sang": ("s", "ang"),
    "sao": ("s", "ao"),
    "se": ("s", "e"),
    "sen": ("s", "en"),
    "seng": ("s", "eng"),
    "sha": ("sh", "a"),
    "shai": ("sh", "ai"),
    "shan": ("sh", "an"),
    "shang": ("sh", "ang"),
    "shao": ("sh", "ao"),
    "she": ("sh", "e"),
    "shei": ("sh", "ei"),
    "shen": ("sh", "en"),
    "sheng": ("sh", "eng"),
    "shi": ("sh", "iii"),
    "shou": ("sh", "ou"),
    "shu": ("sh", "u"),
    "shua": ("sh", "ua"),
    "shuai": ("sh", "uai"),
    "shuan": ("sh", "uan"),
    "shuang": ("sh", "uang"),
    "shui": ("sh", "uei"),
    "shun": ("sh", "uen"),
    "shuo": ("sh", "uo"),
    "si": ("s", "ii"),
    "song": ("s", "ong"),
    "sou": ("s", "ou"),
    "su": ("s", "u"),
    "suan": ("s", "uan"),
    "sui": ("s", "uei"),
    "sun": ("s", "uen"),
    "suo": ("s", "uo"),
    "ta": ("t", "a"),
    "tai": ("t", "ai"),
    "tan": ("t", "an"),
    "tang": ("t", "ang"),
    "tao": ("t", "ao"),
    "te": ("t", "e"),
    "tei": ("t", "ei"),
    "teng": ("t", "eng"),
    "ti": ("t", "i"),
    "tian": ("t", "ian"),
    "tiao": ("t", "iao"),
    "tie": ("t", "ie"),
    "ting": ("t", "ing"),
    "tong": ("t", "ong"),
    "tou": ("t", "ou"),
    "tu": ("t", "u"),
    "tuan": ("t", "uan"),
    "tui": ("t", "uei"),
    "tun": ("t", "uen"),
    "tuo": ("t", "uo"),
    "wa": ("^", "ua"),
    "wai": ("^", "uai"),
    "wan": ("^", "uan"),
    "wang": ("^", "uang"),
    "wei": ("^", "uei"),
    "wen": ("^", "uen"),
    "weng": ("^", "ueng"),
    "wo": ("^", "uo"),
    "wu": ("^", "u"),
    "xi": ("x", "i"),
    "xia": ("x", "ia"),
    "xian": ("x", "ian"),
    "xiang": ("x", "iang"),
    "xiao": ("x", "iao"),
    "xie": ("x", "ie"),
    "xin": ("x", "in"),
    "xing": ("x", "ing"),
    "xiong": ("x", "iong"),
    "xiu": ("x", "iou"),
    "xu": ("x", "v"),
    "xuan": ("x", "van"),
    "xue": ("x", "ve"),
    "xun": ("x", "vn"),
    "ya": ("^", "ia"),
    "yan": ("^", "ian"),
    "yang": ("^", "iang"),
    "yao": ("^", "iao"),
    "ye": ("^", "ie"),
    "yi": ("^", "i"),
    "yin": ("^", "in"),
    "ying": ("^", "ing"),
    "yo": ("^", "iou"),
    "yong": ("^", "iong"),
    "you": ("^", "iou"),
    "yu": ("^", "v"),
    "yuan": ("^", "van"),
    "yue": ("^", "ve"),
    "yun": ("^", "vn"),
    "za": ("z", "a"),
    "zai": ("z", "ai"),
    "zan": ("z", "an"),
    "zang": ("z", "ang"),
    "zao": ("z", "ao"),
    "ze": ("z", "e"),
    "zei": ("z", "ei"),
    "zen": ("z", "en"),
    "zeng": ("z", "eng"),
    "zha": ("zh", "a"),
    "zhai": ("zh", "ai"),
    "zhan": ("zh", "an"),
    "zhang": ("zh", "ang"),
    "zhao": ("zh", "ao"),
    "zhe": ("zh", "e"),
    "zhei": ("zh", "ei"),
    "zhen": ("zh", "en"),
    "zheng": ("zh", "eng"),
    "zhi": ("zh", "iii"),
    "zhong": ("zh", "ong"),
    "zhou": ("zh", "ou"),
    "zhu": ("zh", "u"),
    "zhua": ("zh", "ua"),
    "zhuai": ("zh", "uai"),
    "zhuan": ("zh", "uan"),
    "zhuang": ("zh", "uang"),
    "zhui": ("zh", "uei"),
    "zhun": ("zh", "uen"),
    "zhuo": ("zh", "uo"),
    "zi": ("z", "ii"),
    "zong": ("z", "ong"),
    "zou": ("z", "ou"),
    "zu": ("z", "u"),
    "zuan": ("z", "uan"),
    "zui": ("z", "uei"),
    "zun": ("z", "uen"),
    "zuo": ("z", "uo"),
}


zh_pattern = re.compile("[\u4e00-\u9fa5]")


def is_zh(word):
    global zh_pattern
    match = zh_pattern.search(word)
    return match is not None

def fix_prosodic_label(text):
    return re.sub(r"#[0-9]", "", text)


class MyConverter(NeutralToneWith5Mixin, DefaultConverter):
    pass


class ChineseProcessor():
    pinyin_dict= PINYIN_DICT
    def __init__(self,):
        self.pinyin_parser = None # self.get_pinyin_parser()

    @classmethod
    def get_phoneme_from_char_and_pinyin(self, chn_char, pinyin):
        # we do not need #4, use sil to replace it
        tmp = chn_char
        chn_char = chn_char.replace("#4", "")
        char_len = len(chn_char)
        i, j = 0, 0
        # result = ["sil"]
        result = []
        
        while i < char_len:
            cur_char = chn_char[i]
            if is_zh(cur_char):
                # print(i, j, chn_char[i], pinyin[j])
                if pinyin[j] == "_":
                    i += 1
                    j += 1
                    continue

                # 성우가 그냥 얼화로 읽은 경우
                if pinyin[j][:-1] not in self.pinyin_dict and chn_char[min(i + 1, len(chn_char)-1)] != "儿" and pinyin[j][-2] == "r":
                    # print("그냥 얼화로 읽었슈", pinyin[j][:-1], pinyin[j], chn_char[i], chn_char, j)
                    tone = pinyin[j][-1]
                    a = pinyin[j][:-2]
                    a1, a2 = self.pinyin_dict[a]
                    result += [a1, a2, "_"+tone, "^", "er", "_5"]
                    if i + 2 < char_len and chn_char[i + 2] != "#":
                        result.append("#0")

                    i += 1
                    j += 1
                    continue
                # 그냥 틀린경우
                elif pinyin[j][:-1] not in self.pinyin_dict and chn_char[min(i + 1, len(chn_char)-1)] != "儿" and pinyin[j][-2] != "r":
                    print("나 틀렸슈", pinyin[j][:-1], pinyin[j], chn_char[i], chn_char, j)
                    break
                
                if pinyin[j][:-1] not in self.pinyin_dict:
                    # print(pinyin[j][:-1], pinyin[j], chn_char[i], chn_char, j)
                    # 儿화 코딩
                    assert chn_char[i + 1] == "儿", "얼화 규칙"
                    assert pinyin[j][-2] == "r", "얼화 규칙"
                    tone = pinyin[j][-1]
                    a = pinyin[j][:-2]
                    a1, a2 = self.pinyin_dict[a]
                    result += [a1, a2, "_"+tone, "^", "er", "_5"]
                    if i + 2 < char_len and chn_char[i + 2] != "#":
                        result.append("#0")

                    i += 2
                    j += 2
                else:
                    tone = pinyin[j][-1]
                    a = pinyin[j][:-1]
                    a1, a2 = self.pinyin_dict[a]
                    result += [a1, a2, "_"+tone]

                    if i + 1 < char_len and chn_char[i + 1] != "#":
                        result.append("#0")

                    i += 1
                    j += 1
            elif cur_char == "#":
                # result.append(chn_char[i : i + 2] + "" if int(chn_char[i+1]) == 0 else chn_char[i : i + 2] + "_")
                result.append(chn_char[i : i + 2])
                i += 2
            else:
                result.append(chn_char[i])
                i += 1
        try:
            if result[-1] == "#0":
                result = result[:-1]
        except:
            # print(tmp)
            pass
        if result[-1] not in "！!。.？?😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉😭😢🐢":
            result.append("。")
        assert j == len(pinyin), f"{j}, {len(pinyin)}"
        return result

    def get_one_sample(self, item):
        text, wav_file, utt_id, speaker_name = item

        # normalize audio signal to be [-1, 1], soundfile already norm.
        audio, rate = sf.read(wav_file)
        audio = audio.astype(np.float32)
        if rate != self.target_rate:
            assert rate > self.target_rate
            audio = librosa.resample(audio, rate, self.target_rate)

        # convert text to ids
        try:
            text_ids = np.asarray(self.text_to_sequence(text), np.int32)
        except Exception as e:
            print(e, utt_id, text)
            return None

        # return None
        sample = {
            "raw_text": text,
            "text_ids": text_ids,
            "audio": audio,
            "utt_id": str(int(utt_id)),
            "speaker_name": speaker_name,
            "rate": self.target_rate,
        }

        return sample

    def get_pinyin_parser(self):
        my_pinyin = Pinyin(MyConverter())
        pinyin = my_pinyin.pinyin
        return pinyin
        # return Pinyin()

    def text_to_sequence(self, text):
        text = text.replace(" ", "") # remove unnecessary space
        if self.pinyin_parser is None:
            self.pinyin_parser = self.get_pinyin_parser()
        pinyin = self.pinyin_parser(text, style=Style.TONE3, errors="ignore")
        # TODO: 얼화 규칙 적용
        """
            # MKYU(2024. 04. 03)
            얼(儿)화 규칙
            1. er 단독으로 나온 경우: er+성조 (eg. er4, er2)
            2. 모음 -a, -e, -o, -u 뒤에 나온 경우: +r    (eg. hua1 er2 --> huar1)
            3. -i, -ü, -in, -ün 뒤에 나온 경우: +er     (eg. bi2 er2 --> bier2 / xin4 er2 --> xier4)
            4. -ai, -ui, -ei, -en, -un 뒤에 나온 경우: i/n를 빼서 r만 추가     (eg. dai4 er2 --> dair4 / dan1 er2 --> dar1)
            5. zi, ci, si, zhi, chi, shi 뒤에 나온 경우: i를 빼서 +er    (eg. zi3 er --> zer3)
            6. -ng 뒤에 나온 경우: ng를 빼서 +r    (eg. bang1 er --> bar3)
            7. 다른 자음 뒤에 나온 경우: +r *원래 끝음 발음 생략 (eg. wan2 er2 --> wanr2)
        """
        # 2nd & 3rd rule
        # if a2 in ["a", "e", "o", "u", "v", "ie", "ue", "ve", "i", "ii", "iii",]:
        #     pass # nothing to do
        # # 4th rule
        # if a2 in ["air", "eir", "uair", "ueir", "uir"]:
        #     results += [a1, a2.replace("i", ""), "_"+tone, "^", "er", "_5"]
        # elif a2 in ["enr", "anr", "ianr", "uanr", "uenr", "vanr", "vnr"]:
        #     results += [a1, a2.replace("n", ""), "_"+tone, "^", "er", "_5"]
        # # 5th rule
        # elif a1 in ["z", "c", "s", "zh", "ch", "sh"] and a2 in ["ir", "iir", "iiir"]:
        #     results += [a1, "er", "_"+tone]
        # # 6th rule
        # elif 
        new_pinyin = []
        for x in pinyin:
            x = "".join(x)
            if "#" not in x:
                new_pinyin.append(x)
        phonemes = self.get_phoneme_from_char_and_pinyin(text, new_pinyin)
        text = " ".join(phonemes)
        return text
    
if __name__ == "__main__":
    import jieba
    from nctp.text_processor import TextProcessor
    from nctp.common import Language
    from nctp.common import NormalizeStep
    import os
    os.environ["NCTTS_TM"] = "/SGV/users/mkyu/proj/NCTTSs/NCTTS-bitbang/tts-engine/nctts.tm/"
    
    import os
    os.environ["NCTTS_TM"] = "/SGV/users/mkyu/proj/NCTTSs/NCTTS-bitbang/tts-engine/nctts.tm/"
    tp = ChineseProcessor()
    text = "你#1可以#1先#1出门#3,我不#1知道#1穿#1什么#1出去#4.|ni3 ke6 yi3 xian1 cu1 men2 wo3 bu4 zao1 _ cuan1 sen3 me5 cu1 qu4"
    text = "我#1现在#1还在#1高铁上呢#3,也不#1知道#1啥时候到#3,你#1不用#1接我啦#4.|wo3 xian4 zai4 hai2 zai4 gao1 tie3 shang4 ne5 ye3 bu4 zhao4 _ sha2 shi2 hou5 dao4 ni3 bu2 yong4 jie1 wo3 la5"
    han, phn = text.split("|")
    print(han)
    print(phn)
    print(tp.get_phoneme_from_char_and_pinyin(han, phn.split(" ")))
    pinyin = ChineseProcessor.get_pinyin_parser()
    text = "ABC要一杯朗姆酒嗎？"
    print(pinyin(text, style=Style.TONE3, errors="ignore"))
    # print(tp.normalize("上述#1这些#1地块#2折合#1楼面价#2几乎#1均已达到#2五万元#1每平#1方米?"))
    # print(tp.pronounce(tp.normalize("上述#1这些#1地块#2折合#1楼面价#2几乎#1均已达到#2五万元#1每平#1方米?")))
    # print(tp.pronounce("上述#1这些#1地块#2折合#1楼面价#2几乎#1均已达到#2五万元#1每平#1方米#4"))
    # print((tp.pronounce(tp.normalize("[g]对[/g]瓦尔库斯保持警惕吗？呃，我知道你的背景不清楚。"))))
    # symb, tone = tp.symbolize(tp.text_to_sequence("妈妈#2当时#1表示#3，儿子#2开心得#1像#1花儿一样#4。", inference=True))
    # print(symb, tone)
    # print(list(jieba.cut("妈妈当时表示，儿子开心得像花儿一样。")))