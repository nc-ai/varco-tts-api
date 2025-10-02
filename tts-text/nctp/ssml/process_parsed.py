#########################################################
#
#         Process parsed SSML with text processor
#
# version 0.1 : 2024. 3. 11 - process_say_as(), process_sub()
# version 0.2 : 2024. 4. 16 - Add Japanese support
# version 0.3 : 2024. 4. 19 - Add English support
# version 0.4 : 2024. 4. 25 - Add Chinese(Taiwanese) support
#########################################################


from xml.parsers.expat import ExpatError
from pprint import pprint as pp
import sys
import json
import re

from nctp.ssml.ssml_parser import process_ssml_str, process_ssml_file

from nctp.ssml.say_as_ko import process_sayas_ko
from nctp.ssml.say_as_en import process_sayas_en
from nctp.ssml.say_as_jp import process_sayas_jp
from nctp.ssml.say_as_zh import process_sayas_zh

emoji = {
    "stutter": ("😐", "😑"), # 말더듬
    "laugh": ("😃", "😄"), # 웃음
    "shout": ("😤", "😬"), # 기합
    "scream": ("😫", "😱"), # 비명
    "sigh": ("😔", "😞"), # 한숨
    "filler": ("😦", "😧"), # 간투어
    "cry": ("😭", "😢"), # 울음
    "말더듬": ("😐", "😑"), # 말더듬
    "웃음": ("😃", "😄"), # 웃음
    "기합": ("😤", "😬"), # 기합
    "비명": ("😫", "😱"), # 비명
    "한숨": ("😔", "😞"), # 한숨
    "간투어": ("😦", "😧"), # 간투어
    "울음": ("😭", "😢"), # 울음
    "energy": ("🍎", "🍏"),
    "pitch": ("🍊", "🍋"),
    "speed": ("🍉", "🍈"),
    "break": "🤐",
}


def process_say_as(text_n_attr, lang="korean"):
    """say-as processor

    Args:
        text_n_attr (list): parsed list
        lang (str): language name

    Returns:
        list[string] : say-as에 의해 변환된 결과 [string], string은 1개
    """
    result = []
    if lang == "korean":
        result = process_sayas_ko(text_n_attr)
    elif lang == "english":
        result = process_sayas_en(text_n_attr)
    elif lang == "japanese":
        result = process_sayas_jp(text_n_attr)
    elif lang == "taiwanese" or lang == "chinese":
        result = process_sayas_zh(text_n_attr)
    return result


def process_sub(text_n_attr):
    if text_n_attr[2][0] == "Attribute : ":
        return [text_n_attr[2][2]]


def process_break(text_n_attr):
    if text_n_attr[1][0] == "Attribute : ":
        return ["break", text_n_attr[1][2]]


class BreakEffect:
    def __init__(self, location, length):
        self.location = location
        self.length = length


class TextEffect:
    def __init__(self, type, value, start, end):
        self.type = type
        self.value = value
        self.start = start
        self.end = (
            end + 1
        )  # 서민관님의 요청에 의해 범위의 끝을 실제보다 +1, slicing 사용을 편하게 하기위함


class VoiceEffect:
    def __init__(self, type, value, start, end):
        self.type = type
        self.value = value
        self.start = start
        self.end = (
            end + 1
        )  # 서민관님의 요청에 의해 범위의 끝을 실제보다 +1, slicing 사용을 편하게 하기위함


class Voice:
    def __init__(self, type, value, start, end):
        self.type = type
        self.value = value
        self.start = start
        self.end = (
            end + 1
        )  # 서민관님의 요청에 의해 범위의 끝을 실제보다 +1, slicing 사용을 편하게 하기위함


class Batchfy:
    def __init__(self):
        self.index = 0
        self.effect_string = ""
        self.effect_queue = []

    def process_parsed_list(self, parsed_list, lang="KO"):
        """parsed list의 부분을 처리하여 변환된 list를 리턴.
            재귀호출 이전, 자식노드에 대한 순차적(for) 재귀호출, 재귀호출 이후 3부분으로 나누어 지며
            재귀호출 이전: 태그 종류에 따라 클래스 객체 생성 및 say-as, sub tag 처리
            재귀호출 : 처리할 자식 노드들에 대한 depth-first 처리
            재귀호출 이후 : self.effect_queue 와 self.effect_string에 정보 저장

        Args:
            text_n_attr (list): parsed list
            lang (str): language name

        Returns:
            list : 변환된 parsed list

        """
        start = []
        voiceEffectIdx = 0
        if parsed_list[0] == "say-as":
            return process_say_as(parsed_list, lang)
        elif parsed_list[0] == "sub":
            return process_sub(parsed_list)
        elif parsed_list[0] == "break":
            return process_break(parsed_list)
        elif parsed_list[0] == "nc:voicecontrol":
            for elem in reversed(parsed_list):
                if elem[0] == "Attribute : ":
                    start = len(self.effect_string)
                    self.effect_string += emoji[elem[1]][0]
                    self.effect_queue.append(
                        VoiceEffect(
                            elem[1],
                            elem[2],
                            start,
                            -1,
                        )
                    )
                else:
                    voiceEffectIdx = len(self.effect_queue) - 1
                    break
        elif parsed_list[0] == "nc:texteffect":
            start.append(len(self.effect_string))
            self.effect_string += emoji[parsed_list[-1][2]][0]
        elif parsed_list[0] == "voice":
            start.append(len(self.effect_string))
            voiceIdx = len(self.effect_queue)
            name = None
            lang = None
            for i in range(2, 0, -1):
                if parsed_list[-i][0] == "Attribute : ":
                    if parsed_list[-i][1] == "language":
                        lang = parsed_list[-i][2]
                    elif parsed_list[-i][1] == "name":
                        name = parsed_list[-i][2]
            self.effect_queue.append(Voice(name, lang, start[0], 0))
        for i, elem in enumerate(parsed_list[1:]):
            if len(elem) > 1:
                if elem[0] != "Attribute : ":
                    if elem[0] == "voice":
                        for attr in elem[1:]:
                            if (
                                len(attr) > 0
                                and attr[0] == "Attribute : "
                                and attr[1] == "language"
                            ):
                                lang = attr[2]
                                break

                    parsed_list[i + 1] = self.process_parsed_list(elem, lang)

                    """더이상 추가 처리가 필요없다면(len(parsed_list[i + 1]) == 1)이라면
                        effect_string에 append하여 저장
                    """
                    if len(parsed_list[i + 1]) == 1:
                        self.effect_string += parsed_list[i + 1][0]
            else:
                self.effect_string += elem[0]

        if parsed_list[0] == "break":
            self.effect_queue.append(
                BreakEffect(len(self.effect_string), parsed_list[1])
            )
            self.effect_string += emoji["break"]
        elif parsed_list[0] == "nc:texteffect":
            end = len(self.effect_string)
            self.effect_queue.append(
                TextEffect(parsed_list[-1][2], parsed_list[1], start[0], end)
            )
            self.effect_string += emoji[parsed_list[-1][2]][1]
        elif parsed_list[0] == "nc:voicecontrol":
            i = 0
            for elem in parsed_list[1:]:
                if elem[0] == "Attribute : ":
                    self.effect_queue[voiceEffectIdx + i].end = len(self.effect_string)
                    self.effect_string += emoji[elem[1]][1]
                    i -= 1
        elif parsed_list[0] == "voice":
            self.effect_queue[voiceIdx].end = len(self.effect_string)
        return parsed_list


class EmojiBatchfy:
    def __init__(self):
        self.index = 0
        self.effect_string = ""
        self.effect_queue = []
    
    def process_parsed_list(self, parsed_list, lang="korean"):
        start = []
        voiceEffectIdx = 0
        if parsed_list[0] == "say-as":
            return process_say_as(parsed_list, lang)
        elif parsed_list[0] == "sub":
            return process_sub(parsed_list)
        elif parsed_list[0] == "break":
            self.effect_queue.append(BreakEffect(len(self.effect_string), parsed_list[1][-1].replace("ms", "")))
            self.effect_string += emoji["break"]
            return process_break(parsed_list)
        elif parsed_list[0] == "nc:voicecontrol":
            for elem in reversed(parsed_list):
                if elem[0] == "Attribute : ":
                    start = len(self.effect_string)                    
                    self.effect_queue.append(
                        VoiceEffect(
                            elem[1],
                            elem[2],
                            start,
                            -1,
                        )
                    )
                    # break
                else:
                    voiceEffectIdx = len(self.effect_queue) - 1
                    break
            self.effect_string += emoji['pitch'][0]
        elif parsed_list[0] == "nc:texteffect":
            start.append(len(self.effect_string))
            self.effect_queue += emoji[parsed_list[-1][2]][0]
            self.effect_string += emoji[parsed_list[-1][2]][0]
        elif parsed_list[0] == "voice":
            start.append(len(self.effect_string))
            voiceIdx = len(self.effect_queue)
            name = None
            lang = None
            for i in range(2, 0, -1):
                if parsed_list[-i][0] == "Attribute : ":
                    if parsed_list[-i][1] == "language":
                        lang = parsed_list[-i][2]
                    elif parsed_list[-i][1] == "name":
                        name = parsed_list[-i][2]
            self.effect_queue.append(Voice(name, lang, start[0], 0))
        for i, elem in enumerate(parsed_list[1:]):
            if len(elem) > 1:
                if elem[0] != "Attribute : ":
                    if elem[0] == "voice":
                        for attr in elem[1:]:
                            if (
                                len(attr) > 0
                                and attr[0] == "Attribute : "
                                and attr[1] == "language"
                            ):
                                lang = attr[2]
                                break

                    parsed_list[i + 1] = self.process_parsed_list(elem, lang)
                    if len(parsed_list[i + 1]) == 1:
                        self.effect_string += parsed_list[i + 1][0]
            else:
                self.effect_string += elem[0]

        if parsed_list[0] == "break":
            self.effect_queue.append(BreakEffect(len(self.effect_string), parsed_list[1]))
            self.effect_string += emoji["break"]
        elif parsed_list[0] == "nc:texteffect":
            end = len(self.effect_string)
            self.effect_queue.append(
                TextEffect(parsed_list[-1][2], parsed_list[1], start[0], end)
            )
            self.effect_string += emoji[parsed_list[-1][2]][1]
        elif parsed_list[0] == "nc:voicecontrol":
            self.effect_string += emoji['pitch'][1]
            i = 0
            for elem in parsed_list[1:]:
                if elem[0] == "Attribute : ":
                    self.effect_queue[voiceEffectIdx + i].end = len(self.effect_string)                    
                    i -= 1
        elif parsed_list[0] == "voice":
            self.effect_queue[voiceIdx].end = len(self.effect_string)
        return parsed_list

def main():
    """config file 로딩"""
    with open("config-nc-ssml.json", "r") as test:
        data = test.read()
    ssml_config = json.loads(data)

    """전역변수("ex_.*")로 만들어진 예제 순차 처리
    """
    ex_pattern = re.compile(r"ex_.*")
    str_name = []
    examples = []
    for name, value in globals().items():
        if re.match(ex_pattern, name):
            for i in range(len(value)):
                str_name.append(name + "-" + str(i + 1))
                examples.append(value[i])

    for i in range(len(examples)):
        try:
            parsed_list = process_ssml_str(examples[i], config=ssml_config)
        except ExpatError as e:
            print("processparsed.py:", e.args[0])
            continue
        except Exception as e:
            print("processparsed.py:", e.args[0])
            continue
        print("\n### ", str_name[i])
        print(examples[i])
        pp(parsed_list, indent=4)
        batchList = Batchfy()
        try:
            parsed_list = batchList.process_parsed_list(parsed_list)
        except Exception as e:
            print("Exception during processing parsed_list", e.args[0])
            continue

        pp(parsed_list, indent=4)
        print(batchList.effect_string)

    """SSML 예제파일 읽어 처리
    """
    if len(sys.argv) > 1:
        try:
            parsed_list = process_ssml_file(sys.argv[1], config=ssml_config)
        except FileNotFoundError as e:
            print(e)
        except ExpatError as e:
            print(e.args[0])
        except Exception as e:
            print(e.args[0])
        # print(parsed_list)
        print("\n\n###", sys.argv[1])
        with open(sys.argv[1], "r") as f:
            src = f.readlines()
        pp(src)
        pp(parsed_list, indent=4)
        try:
            batchList = Batchfy()
            parsed_list = batchList.process_parsed_list(parsed_list)
        except Exception as e:
            print(e.args[0])
        pp(parsed_list, indent=4)
        print(batchList.effect_string)


if __name__ == "__main__":
    main()