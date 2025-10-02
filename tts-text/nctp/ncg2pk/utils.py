import jamo
import re
from jamo import h2j, j2h
import os
from nctp.ncg2pk.tag_kor_dict import MECAB_TAG_DICT

JA_LIST = [chr(numb) for numb in range(0x3131, 0x314f)]
MO_LIST = [chr(numb) for numb in range(0x314f, 0x3164)]

LE_MORPHEME = ["N", "V", "M", "I", "UNKNOWN", "UNA", "NA", "UNT"] # 실질 형태소
FUNC_MORPHEME = ["J", "X", "E", "VCP", "UNKNOWN", "UNA", "NA", "UNT"] # 형식 형태소

CHO_VALID_LIST = list(set(JA_LIST) - set(['ㄳ', 'ㄵ', 'ㄶ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅄ']))
JOONG_VALID_LIST = MO_LIST
JONG_VALID_LIST = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅇ', 0]
CHIL_JONG_MAPPING_LIST = [["ㄲ", "ㅋ", "ㄳ", "ㄺ", "ㅅ", "ㅆ", "ㅈ", "ㅊ", "ㅌ", "ㅎ", "ㅍ", "ㅄ", "ㄿ", "ㄵ", "ㄶ", "ㄼ", "ㄽ", "ㄾ", "ㅀ","ㄻ"],
                        ["ㄱ", "ㄱ", "ㄱ", "ㄱ", "ㄷ", "ㄷ", "ㄷ", "ㄷ", "ㄷ", "ㄷ", "ㅂ", "ㅂ", "ㅂ", "ㄴ", "ㄴ", "ㄹ", "ㄹ", "ㄹ", "ㄹ", "ㅁ"]]


def tag_to_def(tag):
    """ return list of tags from mecab and definition of tag in korean

    Args:
        tag (str): tag from mecab

    Returns:
        tag_results (list): list of tags in english.
        def_results (str) : definition of tags in korean.
                            여러 tag가 존재하는 경우 "/"로 구분.
    """
    def _abbreviation(tags):
        tag = tags[-1]
        return tag[0]

    if '+' in tag:
        tag_results = tag.split('+')
        def_results = "/".join(MECAB_TAG_DICT[atag] for atag in tag_results)
    else:
        tag_results = [tag]
        def_results = MECAB_TAG_DICT[tag]
    tag_abbreviation = _abbreviation(tag_results)
    return tag_abbreviation, tag_results, def_results


def mapping(origin, position, new, rule_ids, verbose):
    assert position in ["cho", "joong", "jong"], "position arg should be in [cho, joong, jong] : {}".format(position)
    original_jamo = origin.jamo_dict[position]
    original_char = origin.get_char()
    origin.jamo_dict[position] = new
    new_char = origin.get_char()

    if verbose:
        print(f"by {rule_ids}: ", original_jamo, "->", new, "|", original_char, "->", new_char)


def tag_checker(tags, tag_abb, tag_conditions : list):
    results = False
    for tag_cond in tag_conditions:
        if len(tag_cond) == 1:
            results = (tag_abb == tag_cond)
        else:
            results = (tag_cond in tags)
        if results:
            break
    return results


def chj_finder(condition: list, character: str) -> int:
    """ condition 내 character 에 해당하는 index를 반환

    Args:
        condition (list): 조건
        character (str): 문자

    Returns:
        (int) : 없으면 -1, 있으면 해당 index
    """
    return condition.index(character) if character in condition else -1


def get_blank_idx(input_text):
    blank_indices = [] # in input_text
    m = re.finditer(re.compile(r"\s"), input_text)
    return [space.start() for space in m]


############## Utilities ##############
def get_rule_id2text():
    '''for verbose=True'''
    rules = open(os.path.dirname(os.path.abspath(__file__)) + '/rules.txt', 'r', encoding='utf8').read().strip().split("\n\n")
    rule_id2text = dict()
    for rule in rules:
        rule_id, texts = rule.splitlines()[0], rule.splitlines()[1:]
        rule_id2text[rule_id.strip()] = "\n".join(texts)
    return rule_id2text
