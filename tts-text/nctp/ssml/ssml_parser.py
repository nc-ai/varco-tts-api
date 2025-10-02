#########################################################
#
#                   SSML parser
#
# version 0.1 : 2024. 2. 7 - ssml config 추가
#
# 사용예
# 입력:
# "<speak><say-as interpret-as="time" format="hm">10:59</say-as> 입니다.</speak>"
#
# 출력:
# [   'speak',
#     [   'say-as',
#         ['10:59'],
#         ['Attribute : ', 'interpret-as', 'time'],
#         ['Attribute : ', 'format', 'hm']],
#     [' 입니다.'],
#     ['Attribute : ', 'xmlns:nc', 'urn:dummy']]
#
# 출력된 list는 다음과 같이 구성됩니다.
# [0]tag name (string)
# 0개 이상 원소 : tag에 의해 처리될 내용. list[string] 또는 child element list, list의 원소가 1개면 Text이고 2개 이상이면 tag element입니다
# sequence of Attributes, 리스트의 첫 원소가 "Attribute : "
#
# 각각의 attribute list는 3개의 스트링을 포함하며 다음과 같이 구성됩니다.
# [0] : "Attribute : "
# [1] : attribute name string
# [2] : value string
#
# config file 구성
# json형식이며 NC SSML의 세부명세를 결정합니다.
# '#'로 시작하는 단어는 다음과 같은 특별한 의미를 가집니다.
# #prohibited : 다음에 하위태그로 나올 수 없는 태그를 나열합니다.
# #all : 모든 태그가 하위 태그로 나올수 없는 경우에  #prohibited  안에 모든 태그를 나열하는 대신에 쓰입니다.
# ex) “#prohibited”: [“#all”]
# #essential : 리스트된 속성들중에 최소 1개는 사용이 되어야 할 경우에  쓰입니다.
# #default: 특정 태그에서 속성-값 쌍을 쓰지 않아도 default 값으로 대치합니다.
#
# value 값에 쓰일 수 있는 집합포맷은 다음과 같습니다.
# #float : 실수형 숫자
# #dur : 정수 + ms(밀리초)나 s(초) 의 형식을 의미합니다.
# #dmy : 날짜 형식 문자열
# #hmsz : 시간 형식 문자열
#
# 새로운 tag 또는 attribute-value를 추가하거나 변경하고자 할 경우 SSMLparser.py의 변경없이 config 수정으로 parser 업데이트 가능하고
# 새로운 value 집합포맷이 필요할 경우 SSMLparer.py의 SsmlParse class의  get_value_format(self, value)에 추가 구현이 필요합니다.
# 추가한 태그의 파싱 후 batchfy 처리를 위해서는 processparsed.py의 Batchfy class의 process_parsed_list() 메쏘드에 해당 태그의 코드를 추가해야합니다.
#
#########################################################

import sys
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from bs4 import BeautifulSoup
from pprint import pprint as pp
import json
import re

tag_set_default_dict = {
    "speak": {"xmlns:nc": ["urn:dummy"], "#prohibited": ["speak"]},
    "voice": {
        "name": [],
        "gender": [],
        "variant": [],
        "language": [],
        "#prohibited": ["speak", "voice"],
    },
    "break": {
        "time": ["#dur"],
        "strength": [],
        "#prohibited": ["#all"],
        "#default": {"time": "150ms"},
    },
    "say-as": {
        "interpret-as": [
            "characters",
            "digits",
            "telephone",
            "score",
            "date",
            "time",
            "number",
        ],
        "format": ["#dmy", "#hmsz", "korean", "chinese"],
        "#prohibited": ["#all"],
        "#essential": ["interpret-as"],
    },
    "sub": {"alias": [], "#prohibited": ["#all"], "#essential": ["alias"]},
    "nc:voicecontrol": {
        "speed": ["#float"],
        "energy": ["#float"],
        "pitch": ["#float"],
        "#prohibited": ["speak", "nc:postprocess", "nc:voicecontrol", "voice"],
        "#essential": ["speed", "energy", "pitch"],
    },
    "nc:texteffect": {
        "type": ["stutter", "laugh", "shout", "scream", "sigh", "filler", "cry"],
        "#prohibited": [
            "speak",
            "voice",
            "nc:voicecontrol",
            "nc:texteffect",
            "nc:postprocess",
        ],
        "#essential": ["type"],
    },
    "nc:postprocess": {
        "filter": ["band-pass", "high-pass", "low-pass"],
        "reverb": ["strong", "moderate", "weak"],
        "#prohibited": ["speak"],
        "#essential": ["filter", "reverb"],
    },
    "root": {
        "#prohibited": [
            "voice",
            "break",
            "say-as",
            "sub",
            "nc:voicecontrol",
            "nc:texteffect",
            "nc:postprocess",
        ],
        "#essential": ["speak"],
    },
}

pattern_dur = re.compile(r"\d+s|\d+ms")
pattern_sec = re.compile(r"\d+s")
pattern_float = re.compile(r"[-+]?\d*\.?\d+")
# pattern_float = re.compile(r"[-+]?\d*\.?\d+")
pattern_float = re.compile(r"\d*\.?\d+")

LANG_CODE = {
    "korean": ["KO", "ko", "kr", "KR", "korean", "Korean", "KOREAN", "한국어", "한국"],
    "english": ["EN", "en", "english", "English", "ENGLISH","영어", "미국"],
    "japanese": ["JA", "JP", "ja", "jp", "japanese", "Japanese", "JAPANESE", "일본어", "일본"],
    "taiwanese": ["TW", "tw", "taiwanese", "Taiwanese", "TAIWANESE", "대만어", "대만"]
}

# generalize language ids (added 0613)
def adjust_language_name(lang):
    flag = False
    for k, v in LANG_CODE.items():
        if lang in v:
            lang = k
            flag = True
    if flag:
        return lang
    else:
        raise ValueError("허용되지 않은 언어를 입력하였습니다.")


class SsmlParse:
    def __init__(self, doc_elem, config=None):
        """self.config를 지정한 configuration string 으로 설정. 지정하지 않으면 전역 tag_set_default_dict으로 설정.
        Args:
            config : SSML parser tag set configuration 을 위한 dictionary.
        """
        self.doc_elem = doc_elem
        self.parsed_list = []
        if config is not None:
            self.config = config
        else:
            self.config = tag_set_default_dict

    def is_elem(self):
        """
        Return
            True: minidom parser의 수행결과 tag가 파싱되었으며 SSML tag에 속함
            False: element가 아니거나 SSML tag에 속하지 않음
        """
        if self.doc_elem.nodeType == 1:
            if (
                self.doc_elem.tagName in self.config.keys()
            ):  # config dict의 keys()는 SSML tag의 집합
                return True
            else:
                return False
        else:
            return False

    def is_text(self):
        """
        Return
            True: parsed as Text
            False : other
        """
        if self.doc_elem.nodeType == 3:
            return True
        else:
            return False

    def get_value_format(self, value):
        """attribute의 value에 따라 value의 type string을 리턴

        Args:
            value (string): value string

        Returns:
            string: "#dur", "#float", "#dmy","#hmsz"
        """
        if re.match(pattern_dur, value) is not None:
            return "#dur"
        elif re.match(pattern_float, value) is not None:
            return "#float"
        elif value in [
            "dmy",
            "mdy",
            "ymd",
            "my",
            "ym",
            "md",
        ]:
            return "#dmy"
        elif value in [
            "hms",
            "hm",
            "ms",
            "hms12",
            "hm12",
            "hms24",
            "hm24",
        ]:
            return "#hmsz"
        else:
            return None

    def is_right_format(self, value, attr, elem_list):
        """value와 attribute의 호응을 검사

        Args:
            value (string): value string
            attr (string): attribute string
            elem_list (list): minidom parsed document_element

        Returns:
            _type_: _description_
        """
        value_group = self.get_value_format(value)
        if value_group in self.config[self.doc_elem.tagName][attr]:
            if value_group == "#dmy":
                if (
                    elem_list[-1][0] == "Attribute : "
                    and elem_list[-1][1] == "interpret-as"
                    and elem_list[-1][2] == "date"
                ):
                    return True
                else:
                    return False
            elif value_group == "#hmsz":
                if (
                    elem_list[-1][0] == "Attribute : "
                    and elem_list[-1][1] == "interpret-as"
                    and elem_list[-1][2] == "time"
                ):
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    def process_ssml(self, parent):
        """minidom parsed document element를 재귀적으로 분석하여 SSML문서를 파싱한다

        Args:
            parent (string): 상위 SSML tag

        Returns:
            list : parsed list
        """
        elem_list = []        
        if self.is_elem():
            if "#prohibited" in self.config[parent] and (
                self.doc_elem.tagName in self.config[parent]["#prohibited"]
                or "#all" in self.config[parent]["#prohibited"]
            ):
                raise Exception(
                    "Error : <" + self.doc_elem.tagName + "> is not allowed in this context."
                )
                return elem_list
            elem_list.extend([self.doc_elem.tagName])
            for c in self.doc_elem.childNodes:
                childObj = SsmlParse(c, self.config)
                result = childObj.process_ssml(self.doc_elem.tagName)
                if len(result):
                    self.parsed_list.append(result)

            elem_list.extend(self.parsed_list)

            EssentialAttrList = []
            if "#essential" in self.config[self.doc_elem.tagName]:
                EssentialAttrList = self.config[self.doc_elem.tagName]["#essential"]
                if self.doc_elem.attributes is None or not (
                    set(EssentialAttrList) & set(self.doc_elem.attributes._attrs.keys())
                ):
                    raise Exception(
                        "Error : There are no attributes included in the essential attribute set"
                        + "{"
                        + ",".join(EssentialAttrList)
                        + "}."
                        + " At least one of the attributes is nessary"
                    )
            if "#default" in self.config[self.doc_elem.tagName]:
                default_attr_list = self.config[self.doc_elem.tagName]["#default"].keys()
                for default_attr in default_attr_list:
                    if default_attr not in self.doc_elem.attributes._attrs.keys():
                        elem_list.append(
                            [
                                "Attribute : ",
                                default_attr,
                                self.config[self.doc_elem.tagName]["#default"][default_attr],
                            ]
                        )

            if self.doc_elem.attributes:
                for attr in self.doc_elem.attributes._attrs.keys():
                    if attr not in self.config[self.doc_elem.tagName]:
                        raise Exception(
                            "Error at the attribute name : "
                            + attr
                            + " "
                            + self.doc_elem.attributes._attrs[attr].nodeValue
                        )
                    else:
                        # if there are no specific settings configured.
                        # or the value string is in the config
                        # or if the value format string is in the config
                        if (
                            len(self.config[self.doc_elem.tagName][attr]) == 0
                            or self.doc_elem.attributes._attrs[attr].nodeValue
                            in self.config[self.doc_elem.tagName][attr]
                            or self.is_right_format(
                                self.doc_elem.attributes._attrs[attr].nodeValue, attr, elem_list
                            )
                        ):
                            # generalize language ids
                            if attr == "language":
                                self.doc_elem.attributes._attrs[attr].nodeValue = adjust_language_name(str(self.doc_elem.attributes._attrs[attr].nodeValue).strip())
                            elem_list.append(
                                [
                                    "Attribute : ",
                                    attr,
                                    self.doc_elem.attributes._attrs[attr].nodeValue,
                                ]
                            )
                        else:
                            raise Exception(
                                "Error with the value : "
                                + self.doc_elem.attributes._attrs[attr].nodeValue
                            )
        elif self.is_text():
            if len(self.doc_elem.data.strip()) != 0:
                # 개행문자만 strip
                elem_list.append(re.sub(r"[\n\r]", " ", self.doc_elem.data).strip())
        else:
            raise Exception("Error : Invalid tag name <" + self.doc_elem.tagName + ">")

        return elem_list


def process_ssml_str(ssml_str, config=None):
    """ 1. SSML document string을 입력으로 받고
        2. 입력 string을 minidom으로 파싱(parseString(str))한 결과를
        3. configuration을 참조하여
        4. SsmlParse객체를 생성하고
        5. process_ssml를 이용하여 SSML문서를 파싱한다

    Args:
        ssml_str (string): SSML 입력 string

    Returns:
        list : parsed list
    """
    parsed_list = []
    speak_attr = list(config["speak"].keys())
    if len(speak_attr) > 0 and speak_attr[0][:5] == "xmlns":
        """
            간략한 SSML문서를 위해 <speak> tag의 생략된 부분을 config를 참조하여 복원
        """
        ssml_str = ssml_str.replace(
            "<speak",
            "<speak "
            + speak_attr[0]
            + '="'
            + list(config["speak"].values())[0][0]
            + '"',
            1,
        )
    ssml_str = str(BeautifulSoup(ssml_str, "html.parser")) # bugfix: ssml 파싱 중 &, “<“, “>”, 와 같은 문자 예약어로 이스케이프 문자처리가 필요함
    smdom = parseString(ssml_str)
    doc_elem = smdom.documentElement
    if doc_elem.tagName == "speak":
        root = SsmlParse(doc_elem, config)
        parsed_list = root.process_ssml("root")
    else:
        raise Exception(
            "### SSML ERROR : This is not an SSML document.\n \
            Please use '<speak> tag'"
        )

    return parsed_list


def process_ssml_file(ssml_filename, config=None):
    """ 1. SSML document file인 ssml_filename을 입력으로 받고 
        2. 입력 string을 minidom으로 파싱(parseString(str))한 결과를
        3. configuration을 참조하여 
        4. SsmlParse객체를 생성하고
        5. process_ssml를 이용하여 SSML문서를 파싱한다

    Args:
        ssml_filename (string): SSML 입력 file name

    Returns:
        list : parsed list
    """
    parsed_list = []
    with open(ssml_filename, "r") as f:
        str = f.read()
        speak_attr = list(config["speak"].keys())
        if len(speak_attr) > 0 and speak_attr[0][:5] == "xmlns":
            str = str.replace(
                "<speak",
                "<speak "
                + speak_attr[0]
                + '="'
                + list(config["speak"].values())[0][0]
                + '"',
                1,
            )

    smdom = parseString(str)
    s = smdom.documentElement

    if s.tagName == "speak":
        root = SsmlParse(s, config)
        parsed_list = root.process_ssml("root")
    else:
        raise Exception(
            "### SSML ERROR : This is not an SSML document.\n \
            Please use '<speak> tag'"
        )

    return parsed_list


def main():
    with open("config-nc-ssml.json", "r") as test:
        data = test.read()
    ssml_config = json.loads(data)

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
            print(e.args[0])
            continue
        except Exception as e:
            print(e.args[0])
            continue
        print("\n### ", str_name[i])
        print(examples[i])
        pp(parsed_list, indent=4)

    if len(sys.argv) > 1:
        try:
            parsed_list = process_ssml_file(sys.argv[1], config=ssml_config)
            # print(parsed_list)
            print("\n\n###", sys.argv[1])
            with open(sys.argv[1], "r") as f:
                src = f.readlines()
            pp(src)
            pp(parsed_list, indent=4)
        except FileNotFoundError as e:
            print(e)
        except ExpatError as e:
            print(e.args[0])
        except Exception as e:
            print(e.args[0])


if __name__ == "__main__":
    main()