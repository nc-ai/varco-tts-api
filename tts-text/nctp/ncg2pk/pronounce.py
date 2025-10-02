import logging
import re

from abc import *
# from mecab import MeCab
import MeCab
from jamo import h2j
from nctp.symbols import CommonSymbols, SPACE
from nctp.ncg2pk.utils import CHO_VALID_LIST, JOONG_VALID_LIST, JONG_VALID_LIST, CHIL_JONG_MAPPING_LIST, get_blank_idx, mapping
from nctp.ncg2pk.holder_class import *
from nctp.ncg2pk.rule_manager import RuleManager
from nctp.korean import normalize_with_dictionary
import nctp.ncg2pk.rule_book as rule_book

# MECAB = MeCab()
MECAB = MeCab.Tagger ('-d /usr/local/lib/mecab/dic/mecab-ko-dic')


RM = RuleManager()


def _rule_applyer(sent_chain, special_indices, verbose):
    jamo_indices = list(set(range(len(sent_chain))) - set(special_indices)) # index of JamoHolder only in sent_chain
    # processing for eos(end of strings among characters)
    if len(jamo_indices):
        sent_chain[jamo_indices[-1]].eos = True
    RM.apply(sent_chain, jamo_indices, verbose)


def _get_tokens(input_text):
    """ tokenize inpute text based on MeCab(Official Python Warpper)

    Args:
        input_text (str): [description]

    Returns:
        tokens [list]: (토큰, 태그) input_text의 형태소 분석결과
    """
    MECAB.parse(input_text)
    m = MECAB.parseToNode(input_text)
    tokens = []
    while m:
        tokens.append((m.surface, m.feature.split(',')[0]))
        m = m.next
    return tokens[1:-1] # 처음과 끝 BOS/EOS


def _process_tokens(tokens, blank_indices):
    sent_chain = []
    special_indices = [] # in sent_chain
    idx = 0

    for chars, tag in tokens:
        chars = chars.strip(' ')
        # 특수기호(숫자, 문장부호 등)인 경우
        if (chars in CommonSymbols().sym2num.keys()) or \
                tag.startswith("S") or len(h2j(chars)) < 2:
            sent_chain, special_indices = _specialholder_process(chars, tag, idx, sent_chain, special_indices)
            _find_before_endpoint(idx, sent_chain)
            idx += len(chars)
        # 문자인 경우
        elif idx not in blank_indices:
            sent_chain = _jamoholder_process(chars, tag, sent_chain)
            idx += len(chars)
        # 공백 앞 문자 정보 처리
        _find_before_space(idx, blank_indices, sent_chain)
        # 공백인 경우
        if idx in blank_indices:
            sent_chain, special_indices = _specialholder_process(" ", "UNKNOWN", idx, sent_chain, special_indices)
            idx += 1
    return sent_chain, special_indices


def _find_before_space(idx, blank_indices, sent_chain):
    """ 공백 앞 가장 가까운 JamoHolder 객체의 before_space 필드를 True로 지정 

    Args:
        idx (int): 현재 sent_chain 길이
        blank_indices (list): 공백 index 
        sent_chain (list): Holder class의 객체 list
    """
    if idx in blank_indices:
        for i in range(idx)[::-1]:
            if isinstance(sent_chain[i], JamoHolder):
                sent_chain[i].before_space = True
                break


def _find_before_endpoint(idx, sent_chain):
    """  

    Args:
        idx (int): 현재 sent_chain 길이
        blank_indices (list): 공백 index 
        sent_chain (list): Holder class의 객체 list
    """
    endpoint_punc = CommonSymbols().sym2num.keys() - [CommonSymbols().eos, CommonSymbols().bos, CommonSymbols().space]
    if sent_chain[idx].get_char() in endpoint_punc:
        for i in range(idx)[::-1]:
            if isinstance(sent_chain[i], JamoHolder):
                sent_chain[i].end = True
                break


def _specialholder_process(chars, tag, idx, sent_chain, special_indices):
    for i, char in enumerate(chars):
        holder = SpecialHolder(char, tag)
        sent_chain.append(holder)
        special_indices.append(idx + i)
    return sent_chain, special_indices


def _jamoholder_process(chars, tag, sent_chain):
    for i, char in enumerate(chars):
        holder = JamoHolder(char, tag)
        sent_chain.append(holder)
    return sent_chain


def _valid_checker(holder: JamoHolder or SpecialHolder):
    """ JamoHolder 내의 초성, 중성, 종성이 허용되는 character만으로 구성되어있는지를 확인.
        g2p 변환 후에 수행되어야 합니다.

        초성 허용 문자 : CHO_VALID_LIST
        중성 허용 문자 : JOONG_VALID_LIST
        종성 허용 문자 : JONG_VALID_LIST

    Args:
        holder (JamoHolder or SpecialHolder):

    """
    if not (holder.jamo_dict["cho"] in CHO_VALID_LIST):
        logging.warning("{} not in valid CHO_VALID_LIST characters".format(holder.jamo_dict["cho"]))
        raise AssertionError
    if not (holder.jamo_dict["joong"] in JOONG_VALID_LIST):
        logging.warning("{} not in valid JOONG_VALID_LIST characters".format(holder.jamo_dict["joong"]))
        raise AssertionError
    if not (holder.jamo_dict["jong"] in JONG_VALID_LIST):
        logging.warning("{} not in valid JONG_VALID_LIST characters".format(holder.jamo_dict["jong"]))
        raise AssertionError


def _validate(sent_chain: list, verbose):
    """ g2p 변환 결과가 올바르게 수행되었는지를 체크합니다.
        변환이 올바르게 되었다면 에러 없이 수행됩니다.

    Args:
        sent_chain (list): Holder 클래스들을 갖고있는 리스트
    """
    for holder in sent_chain:
        if isinstance(holder, JamoHolder):
            _valid_checker(holder)


def _get_sent_from_chars(chain):
    """CharHolder들로부터 문자(str)를 얻어 이를 하나로 합친 string을 출력

    Args:
        chain (list): JamoHolder, SpecialHolder 들을 담고있는 list

    Returns:
        [str]: [description]
    """
    res_str = ''
    for holder in chain:
        res_str += holder.get_char()

    return res_str


def nc_g2pk(input_text : str, verbose=False):
    """ g2p 함수 for korean.

    Args:
        input_text (str): 입력 문자열(초중종 갖춰진 한글 글자의 sequence)
        verbose (bool, optional): 자세한 변환과정 출력여부. Defaults to False.

    Returns:
        res_text (str) : g2p가 반영된 출력 문자열
    """
    # STEP 1 : 딕셔너리 적용
    input_text = normalize_with_dictionary(input_text, 'pronounce_g2p', "chunks")

    # STEP 2 : 공백(space) 인덱스
    blank_indices = get_blank_idx(input_text)
    # STEP 3 : 형태소분석 by Mecab
    # tokens = MECAB.pos(input_text) # python-mecab-ko
    tokens = _get_tokens(input_text)

    if verbose:
        print("input text : ", input_text)
        print(tokens)

    # STEP 4 : JamoHolder/SpecialHolder chian 생성
    sent_chain, special_indices = _process_tokens(tokens, blank_indices)
    # STEP 5 : 발음규칙 적용
    # 클래스기반 발음규칙 적용
    _rule_applyer(sent_chain, special_indices, verbose)

    # STEP 6 : 검증과정 적용
    _validate(sent_chain, verbose)  # verbose for 'validate_jongseong'

    # STEP 7 : 결과로부터 text 반환
    res_text = _get_sent_from_chars(sent_chain)
    res_text = ''.join(res_text).strip()
    return res_text


if __name__ == "__main__":
    input_text = "닭가슴살을 알지도 모른다"
    res_text = nc_g2pk(input_text, verbose=True)
    print("g2p result : ", res_text)
