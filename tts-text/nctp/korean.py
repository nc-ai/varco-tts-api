# version 1.1 : version 1 written in Google Style

from typing import Match
import jamo
import re

from nctp.dictionary.kor_sDict import kor_ipa_dict
from nctp.dictionary.precompile import get_dict, get_regex_pattern
from nctp.dictionary.kor_sDict import \
    num_to_kor, big_dec, num_to_kor_native, unit_to_kor1, \
    eng_cons_to_jamo_batchim, eng_cons_to_jamo, eng_longv_to_jamo, \
    eng_vowel_to_jamo, alpha_to_han, jaeum_to_han

JAMO_LEADS = "".join([chr(_) for _ in range(0x1100, 0x1113)])
JAMO_VOWELS = "".join([chr(_) for _ in range(0x1161, 0x1176)])
JAMO_TAILS = "".join([chr(_) for _ in range(0x11A8, 0x11C3)])

JAMO = JAMO_LEADS + JAMO_VOWELS + JAMO_TAILS

KR_SYMBOLS = JAMO


def get_ipa_symbols(kor_ipa_dict):
    symbol_list = []
    for phn_info in kor_ipa_dict.values():
        ipa = phn_info["ipa"]
        if ipa not in symbol_list:
            symbol_list.append(ipa)
    return symbol_list


KR_IPA_SYMBOLS = get_ipa_symbols(kor_ipa_dict)
KR_IPA_MAP = kor_ipa_dict


def join_period(text):
    '''
    check if there is a puncuation mark at the end of the sentence.
    if not, add period.

    Args:
        text (str): text sentence

    Returns:
        perioded text (str): text sentence with period

    Examples:
        >>> join_period("Hello, world")
        "Hello, world."
        >>> join_period("Hello, world?.")
        "Hello, world?."
        >>> join_period("Hello, world..")
        "Hello, world.."
    '''
    # 중국/일본의 문장부호 대응 (UPDATED 24.02.21)
    # #4는 중국어 EOS
    # 추가된 이모지들은 styletag end symbol 임. (문장 끝에 이것들이 오는 경우 맨 뒤에 .이 한번 더 붙기 때문)
    punctuation = ('!', '?', '.', '~', '？','！','。', "#4", "🍊", "🍋", '😧', '😑', '😄', '😞', '😱', '😬', '🙉')
    if not text.endswith(punctuation):
        _perioded_text = text + '.'
    else:
        _perioded_text = text
    return _perioded_text


def remove_residual(text):
    """ 문장부호 앞 공백을 제거하기 위한 step
        문장의 마지막에 위치하는 문장부호에도 적용하기 위해서,
        입력 텍스트 마지막에 임시로 `臨`를 추가하여 처리 후 제거
        clean step 중 하나

    Args:
        text ([type]): 입력 텍스트
    Returns:
        [type]: [description]
    """
    punctuation = ('!', '?', '.', '~', ',', '-', '\'')
    special_punc = '|'.join(re.escape(a_punc) for a_punc in punctuation)
    # special_punc = [f'\{a_punc}' for a_punc in punctuation]
    residual_extract_pattern = re.compile(r'\s+([{}]+)([^\S]|[臨])'.format(special_punc))

    threshold = 10
    for stopper in range(threshold):
        text_r = re.sub(residual_extract_pattern, lambda x : x.group(1) + x.group(2), text + '臨')
        text_r = text_r[:-1] if text_r.endswith('臨') else text_r
        # 처리 결과가 처리 이전과 동일할 때까지 수행
        if text_r == text:
            break
        else:
            text = text_r
    return text

def remove_residual_2(text):
    """ 문장부호 앞 공백을 제거하기 위한 step
        문장의 마지막에 위치하는 문장부호에도 적용하기 위해서,
        입력 텍스트 마지막에 임시로 `🗑`를 추가하여 처리 후 제거
        clean step 중 하나

    Args:
        text ([type]): 입력 텍스트
    Returns:
        [type]: [description]
    """
    punctuation = ('!', '?', '.', '~', ',', '-', '\'', '。', '、', '？', '！')
    special_punc = '|'.join(re.escape(a_punc) for a_punc in punctuation)
    # special_punc = [f'\{a_punc}' for a_punc in punctuation]
    residual_extract_pattern = re.compile(r'\s+([{}]+)([^\S]|[🗑])'.format(special_punc))

    threshold = 10
    for stopper in range(threshold):
        text_r = re.sub(residual_extract_pattern, lambda x : x.group(1) + x.group(2), text + '🗑')
        text_r = text_r[:-1] if text_r.endswith('🗑') else text_r
        # 처리 결과가 처리 이전과 동일할 때까지 수행
        if text_r == text:
            break
        else:
            text = text_r
    return text


def normalize_pronunciation(text):
    '''
    합성했을 때 발음이 어색한 부분들을 적절히 전처리한다. (즉, model specific하므로 데이터 증가로 발음이 괜찮아질 경우 함수를 삭제하며, 반대로 필요시 추가한다.)

    Args:
        text (str): text sentence ** 음운 변환을 자모 단위로 분석하기 때문에 한글 자모는 스트링에서 단독으로 오지 않는다고 가정 (ㄱ,ㄴ,ㄷ,ㅣ,ㅗ,ㅜ, etc), 에러는 안 남

    Returns:
        text (str): normalized text

    Examples:
        >>> text = '꽃잎은 먹을수록 맛없다.'
        >>> normalize_pronunciation(text)
        '꼰닢은 먹을쑤록 마덦다.'
    '''
    # 형태소 분석이 필요한 것(실질 vs 형식, 한자어, 등)은 아쉬운 대로 딕셔너리 형태로 처리
    text = normalize_with_dictionary(text, 'pronounce_norm_pron', "chunks")

    # 데이터가 부족한 겹받침 발음을 정규식으로 전처리
    text = normalize_gyeopbatchim(text)

    # ㄹ로 끝나는 어간 발음을 정규식으로 전처리
    text = normalize_rieul_batchim(text)

    return text


def normalize_gyeopbatchim(text):
    '''
    겹받침을 표준 발음법에 맞게 적절하게 발음시킨다. (형태소 분석이 필요한 ㄺ, ㄼ, ㄻ 등의 경우 제외)

    Args:
        text (str): text sentence ** 음운 변환을 자모 단위로 분석하기 때문에 한글 자모는 스트링에서 단독으로 오지 않는다고 가정 (ㄱ,ㄴ,ㄷ,ㅣ,ㅗ,ㅜ, etc), 에러는 안 남

    Returns:
        text (str): normalized text

    Examples:
        >>> text = '너무 집중해서 개가 팔을 핥는지도 몰랐다.'
        >>> normalize_gyeopbatchim(text)
        '너무 집중해서 개가 팔을 할른지도 몰랐다.'
    '''
    text = jamo.j2hcj(jamo.h2j(text))
    text = re.sub(r'ㄾㄴ', 'ㄹㄹ', text)  # ㄾㄴ 연쇄 to ㄹㄹ 연쇄: ㄴ의 유음화 (핥는 --> 할른) 표준 발음법 제20항
    text = re.sub(r'ㄿ(?!ㅇ|ㅎ)', 'ㅂ', text)  # ㄿ 겹받침 to ㅂ before 자음 or 어말: 종성의 발음 (읊소 --> 읍소) 제11항
    text = re.sub(r'ㄿㅇ', 'ㄹㅍ', text)  # ㄿ 겹받침 to ㄹㅍ before 형식 형태소 모음: 종성의 연음 (읊어도 --> 을퍼도) 제14항
    text = re.sub(r'ㄵ(ㄷ|ㄱ(?!ㅕ|ㅣ)|ㅅ|ㅈ)', lambda x: 'ㄴ' + chr(ord(x.group(1)) + 1), text)  # 어간 ㄵ 뒤 초성의 된소리화  (앉자 --> 안짜) c.f. 접미사 '기'가 따라올 때 제외 제24항
    text = re.sub(r'ㄽ(?!ㅇ)', 'ㄹ', text)  # ㄽ 겹받침 to ㄹ before 자음 or 어말: 종성의 발음 (외곬만 --> 외골만) 제10항
    text = re.sub(r'ㄽㅇ', 'ㄹㅆ', text)  # ㄽ 겹받침 to ㄹㅆ before 형식 형태소 모음: 종성의 연음 (외곬으로만 --> 외골쓰로만) 제14항
    text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ]+', lambda x: jamo2han(x.group()), text)

    return text


def normalize_rieul_batchim(text):
    '''
    ㄹ 종성의 관형사형이나 어미를 표준 발음법에 맞게 적절히 발음시킨다.
    [표준 발음법 제27항]
    1) 관형사형 '-(으)ㄹ' 뒤에 연결되는 'ㄱ,ㄷ,ㅂ,ㅅ,ㅈ'은 된소리로 발음한다. 다만, 끊어서 말할 적에는 예사소리로 발음한다. ==> 형태소 분석을 요해서 '-할' 형태만 우선 처리
    2) '-(으)ㄹ'로 시작되는 어미의 경우에도 이에 준한다.

    Args:
        text (str): text sentence ** 음운 변환을 자모 단위로 분석하기 때문에 한글 자모는 스트링에서 단독으로 오지 않는다고 가정 (ㄱ,ㄴ,ㄷ,ㅣ,ㅗ,ㅜ, etc), 에러는 안 남

    Returns:
        text (str): normalized text

    Examples:
        >>> text = '삶이 그대를 속일지라도.'
        >>> normalize_rieul_batchim(text)
        '삶이 그대를 속일찌라도.'
    '''
    text = jamo.j2hcj(jamo.h2j(text))
    # 합성 시 '-할'과 뒤의 단어 사이에 휴지가 너무 긴 탓에 된소리화가 부자연스럽게 들려서 우선 주석 처리
    # text = re.sub(r'(?<=ㅎㅏㄹ )(ㄷ|ㄱ|ㅂ|ㅅ|ㅈ)', lambda x: chr(ord(x.group(1)) + 1), text)  # 제27항 1)에서 아쉬운 대로 '-할'만이라도 추가. 다만을 참고해 스페이스 하나일 때만 된소리화
    pattern = re.compile(jamo.j2hcj(jamo.h2j('ㄹ(걸|밖에|세라|수록|지언정|지라도|진대)')))  # 제27항 2)에서 언급된 어미들
    text = re.sub(pattern, lambda x: 'ㄹ' + chr(ord(x.group(1)[0]) + 1) + x.group(1)[1:], text)
    text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ]+', lambda x: jamo2han(x.group()), text)

    return text


def drop_incompletes(text: str) -> str:
    '''
    자음, 모음 뿐인 한글을 제거한다.

    Args:
        text (str): text sentence

    Returns:
        text (str): normalized text

    Examples:
        >>> text = 'ㄱ, ㄴ을 보시면 상세하게 설명되어 있습니다. ㅘㅣㅗserious?'
        >>> drop_incompletes(text)
        ', 을 보시면 상세하게 설명되어 있습니다. serious?'
    '''
    return re.sub(r'[ㅏ-ㅣㄱ-ㅎ]', "", text)


def normalize_character(text):
    '''
    영어 자음만 올 경우, 알파벳 읽듯이 읽어준다. 단독으로 온 자모음은 삭제한다.

    Args:
        text (str): text sentence

    Returns:
        text (str): normalized text

    Examples:
        >>> text = 'HDD를 SSD로 바꾸었습니다.'
        >>> normalize_character(text)
        '에이치디디를 에스에스디로 바꾸었습니다.'
    '''
    text = re.sub(r'[a-zA-Z]', lambda x: alpha_to_han[x.group().upper()], text)
    # text = re.sub(r'[ㄱ-ㅎ]', lambda x: jaeum_to_han[x.group()], text)  # read jaeum to hangul
    return text


def normalize_english(text):
    '''
    normalizes english that are not in the dictionary (모음이 하나라도 포함되는 경우만 정규화. 자음만 있으면 normalize_character에서 알파벳 방식으로 정규화)

    Args:
        text (str): text sentence

    Returns:
        text (str): normalized text

    Examples:
        >>> text = '댓 MEANS 테이크 A 백 SEAT'
        >>> normalize_english(text)
        '댓 민스 테이크 아 백 싯'
    '''
    text = re.sub(r'[a-zA-Z]*[aeiouyAEIOUY]+[a-zA-Z]*', lambda x: jamo2han(eng2jamo(x.group())), text)

    return text


def eng2jamo(word):
    '''
    word 단위 영어의 미국식 발음을 추측한 후, 외래어 표기법에 가깝게 자모로 반환하는 함수
    자음과 모음으로 나눈 후 for문을 돌려 한글 자모로 치환한다.

    Input :
        word(str) : word 단위 영어 (적절한 결과는 안 나오지만 비영어 문자 및 line 단위도 에러 없이 처리)

    Returns :
        word(str) : 한글 자모

    Examples:
        >>> word = 'marry'
        >>> eng2jamo(word)
        'ㅁㅐㄹㅣ'
    '''
    # 음소로 쪼개기 전에 공통적인 부분 전처리
    word = "@" + word.lower() + "%"  # '@' = BOW, '%' = EOW
    word = re.sub(r'([^aeiouwycg])\1(?!le%)', r'\1', word)  # delete duplicate consonants except for 1) cc and gg, and 2) when before le% (muddle --> muddle, shopping --> shoping, summer --> sumer, string --> string)
    word = re.sub(r'r(?=[^aeiouwy]|e%)', r'#', word)  # mark /r/ as silent r '#' when 1) comes before consonant, 2) takes the form of [aeiou]re%
    word = re.sub(r'sh(?=[aeiouwy])', r'sy', word)  # make 'sh' to /sy/ before vowel (샤, 시, 섀, 셰, 슈, etc.)
    word = re.sub(r'@(w)([hr])', r'@\2\1', word)  # change 'wr', and 'wh' at BOW to 'rw' and 'hw' so that it sounds /r/ and /hw/ (white, write, wrap)
    word = re.sub(r'(?<!c)c(?=[eiy])', r's', word)  # make 'c', 'sc', to /s/ 'e' and 'i', and 'y', but not cc
    word = re.sub(r'(?<!g)g(?=[eiy])', r'j', word)  # make 'g', 'dg' to /j/ before 'e' and 'i', and 'y', but not gg
    phoneme_list = re.findall(r'(?<=[aeiouyw])[^aeiouyw]+e%|[aeiouyw]+|[^aeiouwy]+', word)  # silent e ('e'로 끝나는 단어)는 영어에서 특별한 지위를 가지므로 따로 처리
    # print("phonemes in the given word: ", phoneme_list)
    kr_word = ''
    vowel = ''

    # 딕셔너리에 없는 음소의 경우, 자음은 'ㅇ'으로, 모음은 'ㅡ'로 변환
    for phoneme in phoneme_list:
        if phoneme.endswith('le%'):  # [^aeiouyw]+le pattern (cuddle, middle, muscle, hustle, humble, apple, maple, tuple, etc.)
            consonant = re.search(r'.*(?=l)', phoneme).group()
            # 모음 변환
            if vowel in eng_vowel_to_jamo and consonant.startswith('#'):  # r controlled vowel, as in startle
                kr_word += eng_vowel_to_jamo[vowel][2]
            elif vowel in eng_vowel_to_jamo and len(consonant) == 2:  # 단모음 as in apple
                kr_word += eng_vowel_to_jamo[vowel][3]
            elif vowel in eng_vowel_to_jamo:  # 장모음 as in maple, fable
                kr_word += eng_vowel_to_jamo[vowel][1]
            else:
                kr_word += eng_longv_to_jamo.get(vowel, 'ㅡ')  # 기타 모음, as in poodle
            # 자음 변환
            if len(consonant) == 0:  # as in tale, pile
                kr_word += 'ㄹ'
            else:
                kr_word += eng_cons_to_jamo.get(consonant[0], 'ㅇ')
                if len(consonant) >= 2 and not (consonant[0] == 's' or consonant[0] == consonant[1]):  # as in humble, kindle, startle, but NOT fiddle, muscle
                    kr_word += eng_cons_to_jamo.get(consonant[1], 'ㅇ')  # 3개 이상의 자음군은 영어 음운에서 못 오므로 무시
                kr_word += 'ㅡㄹ'
        elif phoneme.endswith('e%'):  # [^aeiouyw]+e pattern (change, fake, tape, etc.)
            consonant = re.search(r'[^aeiouyw]+', phoneme).group()
            # 모음 변환
            if consonant.startswith('#') and vowel in eng_vowel_to_jamo and len(consonant) >= 2:  # r controlled vowel, as in nurse, purse
                kr_word += eng_vowel_to_jamo[vowel][2]
            elif vowel in eng_vowel_to_jamo and len(consonant) >= 2:  # 단모음, as in sponge, judge, bridge, hence, resistance
                kr_word += eng_vowel_to_jamo[vowel][3]
            elif vowel in eng_vowel_to_jamo:  # 장모음
                kr_word += eng_vowel_to_jamo[vowel][1]
            else:  # 기타 모음
                kr_word += eng_longv_to_jamo.get(vowel, 'ㅡ')
            # 자음 변환
            if consonant == '#' :
                kr_word += 'ㅇㅓ'
            elif consonant.endswith('j'):
                kr_word += eng_cons_to_jamo.get(consonant.split('j')[0], '')  # as in sponge, purge, bridge
                kr_word += 'ㅈㅣ'
            else:
                kr_word += eng_cons_to_jamo.get(consonant[0], 'ㅇ')
                if len(consonant) >= 2:
                    kr_word += eng_cons_to_jamo.get(consonant[1], 'ㅇ')
                if consonant[-1] not in 'mnl' :
                    kr_word += 'ㅡ'
        elif phoneme[0] in 'aeiouwy' :  # 모음 저장; 모음의 발음 뒤의 자음에 의해 결정된다
            if kr_word[-1] == 'ㅊ' and phoneme[0] == 'w' :  # as in matchwood (외래어 표기법 제9항; 자음 뒤에 w가 올 때엔 두 음절로 갈라적는다)
                kr_word += 'ㅣㅇ'
            elif kr_word[-1] not in 'ㅇㄱㅋㅎ' and phoneme[0] == 'w' :  # as in swarm, twerk, swoln, swing (위와 동일, 단 g, h, k는 한 음절로 적는다.)
                kr_word += 'ㅡㅇ'
            vowel = phoneme
        else:  # 일반적인 자모음
            cons_list = re.findall(r'^@$|[st]ch|[gcs]{2}|dj|ght|[cs]hr?|g[nh]%|[ptg]h|@[gpk]n|[nc]k|ng|[td]s%|l[mn]|[^@]', phoneme)
            plosive_batchim = True  # 외래어 표기법 제1항의 특정 조건을 만족할 경우 plosive sound(p, t, k)를 받침으로 적는다
            # 모음 변환
            if vowel in eng_vowel_to_jamo:
                if cons_list[0] == 'ght' and vowel == 'i' :  # 'ight' pattern as in fright, fight, might
                    kr_word += 'ㅏㅇㅣ'
                elif cons_list[0] == '#' :  # r controlled vowels; as in part, harp
                    kr_word += eng_vowel_to_jamo[vowel][2]
                elif cons_list[0] == '%' :  # 단어가 모음으로 끝날 때
                    kr_word += eng_vowel_to_jamo[vowel][0]
                else:  # 단모음
                    kr_word += eng_vowel_to_jamo[vowel][3]
            else:
                kr_word += eng_longv_to_jamo.get(vowel, "ㅡ")
                if cons_list == ['#', '%']:
                    kr_word += 'ㅇㅓ'
            # 자음 변환
            for curr, next in zip(cons_list, cons_list[1:] + ['^']):  # '^' == 자음 뒤에 모음이 온다는 표지
                # print(curr, next)
                if curr in ['t', 'p', 'c', 'k', 'ck'] and next not in ['l', 'm', 'n', 'r', '^'] and plosive_batchim:  # 외래어 표기법 제1항
                    kr_word += eng_cons_to_jamo_batchim[curr]
                else:
                    kr_word += eng_cons_to_jamo.get(curr, 'ㅇ')
                    if curr in ['sh', 'ch', 'tch'] and next != '^' :
                        kr_word += 'ㅣ'
                    elif curr == 'ng' and next == '^' :  # as in penguin
                        kr_word += 'ㄱ'
                    elif curr == 'ng' and next == 'l' :  # as in hanglide
                        kr_word += 'ㄱㅡ'
                    elif curr not in ['l', 'm', 'n', 'ng', 'gn%', 'lm', 'ln', '#'] and next != '^' :  # as in string, drizzle, but NOT tolkin, helm
                        kr_word += 'ㅡ'
                plosive_batchim = False  # 무성 파열음이 자음군의 첫번째 위치에 올 때만 종성으로 적도록 한다
            vowel = ''

    # print(kr_word)

    return kr_word


def jamo2han(word):
    '''
    word 단위의 자모의 연쇄(ㄱㅏㄴ)를 음절(간)로 바꾸는 함수, 비자모 문자는 삭제 (normalize_english()에서 ㄹㄹ 발음인 'l' 및 fjdksjkfl 이런 식의 랜덤 인풋 대비용)

    Input :
        word(str) : word 단위 자모 (비자모는 삭제하기 때문에, line 단위에서 에러가 발생하지는 않으나 원하는 결과는 보장되지 않음)

    Returns :
        word(str) : word 단위 한글

    Examples:
        >>> word = 'ㅇㅔㄴㅆㅣㅅㅗㅍㅡㅌㅡ'
        >>> jamo2han(word)
        '엔씨소프트'
        >>> word = 'ㄹㅏ어ㅏ아아앙ㅇㅏㄴㄴㅕ@@@@'
        >>> jamo2han(word)
        '라안녀'
    '''
    if len(word) < 2:
        return ""
    elif not (0x3131 <= ord(word[0]) <= 0x314e and 0x314f <= ord(word[1]) <= 0x3163):  # 자음+모음 패턴이 아닐 경우 삭제
        return jamo2han(word[1:])
    elif (len(word) == 3 and 0x3131 <= ord(word[2]) <= 0x314e) or (len(word) > 3 and 0x3131 <= ord(word[2]) <= 0x314e and 0x3131 <= ord(word[3]) <= 0x314e):
        return jamo.j2h(*word[0:3]) + jamo2han(word[3:])  # 종성이 있는 경우 (자음+모음+자음)
    else:
        return jamo.j2h(*word[0:2]) + jamo2han(word[2:])  # 종성이 없는 경우 (자음+모음)


__DICT_ACTIONS = {
    "key_only": {
        "type": "basic",
        "upper": False,
    },
    "chunks": {
        "type": "chunk",
        "upper": False,
    },
    "chunks_upper": {
        "type": "chunk",
        "upper": True,
    },
}


def normalize_with_dictionary(text: str, lang: str, act: str = 'chunks') -> str:
    '''
    Normalize if a specific character contains key of dictionary of given language.

    Args:
        text (str) : text sentence
        lang (dict): dictionary language (e.g. 'etc', 'english', 'universe')
        act  (str) : pattern 방식과 대문자로 처리 여부를 구분하기 위한 key입니다.
                     should be in ["key_only", "chunks", "chunks_upper", for_service]

    Returns:
        text (str): normalized text

    Examples:
        >>> text = '1+1이다.'
        >>> etc_dictionary = {'1+1':'원플러스원'}
        >>> normalize_with_dictionary(text, 'etc', 'key_only')
        '원플러스원이다.'
    '''

    assert act in __DICT_ACTIONS, "Given act '{}' is not valid.".format(act)

    map = get_dict(lang, escaped=False)
    is_upper = __DICT_ACTIONS[act]["upper"]
    pat = get_regex_pattern(lang, __DICT_ACTIONS[act]["type"], ignorecase=is_upper)

    def convert_if_exists(m: Match) -> str:
        target = m.group()
        # ALL KEYS of original dictionary should be UPPERCASE in order to use `is_upper`
        if is_upper:
            target = target.upper()

        if target not in map:
            return target
        return map[target]

    if pat.search(text) is not None:
        return pat.sub(convert_if_exists, text)
    else:
        return text


def normalize_date(text):
    """ Detect date(yyyy[-/.]mm[-/.]dd) pattern in a sentence. Then, changing it to date pattern in english.

    Args:
        text ([str]): input text

    Returns:
        [str]: processed text
    """
    date_pattern = re.compile(r'([12]\d{3})[-/.]([1-9]|0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])')
    text = re.sub(date_pattern, lambda x: f'{x.group(1)}년 {x.group(2)}월 {x.group(3)}일', text)
    return text


def normalize_internet(text):
    """normalize internet address pattern.
       * 입력 text에 대한 가정 없음.

    Args:
        text (str): text sentence

    Examples:
        >>> text = 'www.ncsoft.com'
        >>> res = normalize_internet(text)
        'www dot ncsoft dot com'
    """
    def insert_dot(group):
        p = re.compile(r'\.')
        group = re.sub(p, ' dot ', group)
        return group
    pattern = re.compile(r'[a-zA-Z]+\.[a-zA-Z]+')

    while pattern.findall(text):
        text = re.sub(pattern, lambda x: insert_dot(x.group()), text)

    return text


def normalize_numsequence(text):
    """normalize sequence of number pattern. It means to delete dash characters.
       * 입력 text에 대한 가정 없음.

    Args:
        text (str): text sentence

    Examples:
        >>> text = '010-1111-1111'
        >>> res = normalize_numsequence(text)
        '영일영 일일일일 일일일일'
    """
    def delete_dash(group, deco=' '):
        p = re.compile(r'\-')
        group = re.sub(p, deco, group)

        n_p = re.compile(r'[0-9]+')
        group = re.sub(n_p, lambda x: numeral(x.group(), type='normal'), group)

        return group

    # pattern = re.compile(r'[0-9]+\-[0-9]+\-[0-9]+')
    # text = re.sub(pattern, lambda x: delete_dash(x.group()), text)

    pattern = re.compile(r'([0-9]+\-){3,}([0-9]+)')
    text = re.sub(pattern, lambda x: delete_dash(x.group(), '다시 '), text)

    pattern = re.compile(r'([0-9]+\-){2,3}([0-9]+)')
    text = re.sub(pattern, lambda x: delete_dash(x.group(), ' '), text)

    return text


def normalize_range(text):
    """normalize the text including a range of numbers.
       * 입력 text에 대한 가정 없음.

    Args:
        text (str): text sentence

    Examples:
        >>> text = '1~12개의 콩'
        >>> res = normalize_range(text)
        '일에서 열두개의 콩'
    """
    def insert_range(group):
        p = re.compile(r'\~')
        group = re.sub(p, '에서 ', group)

        n_p = re.compile(r'[0-9]+')
        group = re.sub(n_p, lambda x: numeral(x.group(), type='dec'), group)

        return group
    pattern = re.compile(r'[0-9]+\~[0-9]+')

    text = re.sub(pattern, lambda x: insert_range(x.group()), text)

    return text


def normalize_emoji(text):
    """normalize emoji pattern

    Args:
        text ([type]): [description]
    """
    emoji_pattern_dict = {
        # "unicode" : re.compile('(\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff])'),
        "str" : re.compile(r':\)|:-\)|:\(|:-\(|;\);-\)|:-O|8-|:P|:D|:\||:S|:\$|:@|8o\||\+o\(|\(H\)|\(C\)|\(\?\)|[\^\*\@\-\~\>]+[\.\,\_\^]+[\^\*\@\-\~\<]?')
    }
    for pattern in emoji_pattern_dict.values():
        text = re.sub(pattern, '', text)
    return text


def normalize_patterns(text):
    """normalize text with certain patterns.
       * 입력 text에 대한 가정 없음.

    Args:
        text (str): text sentence

    Examples:
        >>> text = '내 전화번호는 031-233-4455이야 13~14시 사이에 전화해. 이메일 주소는 nc@ncsoft.com'
        >>> res = normalize_patterns(text)
        '내 전화번호는 031 233 4455이야 13에서 14시 사이에 전화해. 이메일 주소는 nc@ncsoft dot com'
    """
    text = normalize_date(text)
    text = normalize_internet(text)
    text = normalize_numsequence(text)
    text = normalize_emoji(text)
    text = normalize_range(text)
    return text


# deprecated?
# def normalize_quote(text):
#     '''모든 따옴표를 `로 통일'''
#     def fn(found_text):
#         from nltk import sent_tokenize  # NLTK doesn't along with multiprocessing

#         found_text = found_text.group()
#         unquoted_text = found_text[1:-1]

#         sentences = sent_tokenize(unquoted_text)
#         return " ".join(["'{}'".format(sent) for sent in sentences])

#     return re.sub(quote_checker, fn, text)


re_number = r"[+-]?\d+(?:,\d+)*(?:\.\d+)*"  # +-,.는 한 번만 인식, (,\d+)* : 컴마가 오는 숫자의 반복, (\.\d+)* : 소수점 뒤의 숫자 (,\d{3}이 되게 할지는 고민)


def unit_to_pattern(unit_word_list):
    unit_word_list.sort(key=len, reverse=True)
    unit_word_pattern = "(" + "|".join(unit_word_list) + ")"
    return unit_word_pattern


# kr_unit_native_list : kr_unit_sino_list 내 단위를 포함하는 단위 리스트
#                       그 중 고유어로 발음하는 단위들.
#                       예 ) 1개월 -> 일개월
kr_unit_native_list = ["개월", "개년", "번지"]
re_kr_unit_native = unit_to_pattern(kr_unit_native_list)

# kr_unit_sino_list : 그 중 한자어로 발음하는 단위들.
#                       예 ) 1시 -> 한 시
kr_unit_sino_list = ["시", "명", "가지", "살", "마리", "포기", "송이", "수", "톨", "통", "개", "벌", "척", "채", "다발",
                     "그루", "자루", "줄", "켤레", "그릇", "잔", "마디", "상자", "사람", "곡", "병", "판",
                     "군데", "권", "닢", "대", "두", "모", "모금", "뭇", "발", "발짝", "방", "번", "술", "쌈",
                     "움쿰", "정", "짝", "첩", "축", "건", "돌", "배", "곳", "차례"]
re_kr_unit_sino = unit_to_pattern(kr_unit_sino_list)


def normalize_number(text):
    '''
    normalize a text with numbers
    * 입력 text에 대한 가정 없음.

    Args:
        text (str): text sentence

    Returns:
        text (str): normalized text

    Examples:
        >>> text = '최근 1년'
        >>> normalize_number(text)
        '최근 일년.'
    '''
    text = normalize_with_dictionary(text, 'unit', "chunks")
    text = re.sub(re_number + re_kr_unit_native,
                  lambda x: num2kor(x.group(), native=False), text)  # 숫자가 한자어 방식으로 읽는 단위와 함께 존재
    text = re.sub(re_number + re_kr_unit_sino,
                  lambda x: num2kor(x.group(), native=True), text)  # 숫자가 고유어 방식으로 읽는 단위와 함께 존재
    text = re.sub(re_number,
                  lambda x: num2kor(x.group(), native=False), text)  # 숫자가 단독으로 존재
    return text


def numtokor_sino(numb_list):
    ''' 입력으로 받은 숫자문자열들을 포함하는 리스트를 한자어(일, 이,...)로 세는 함수
        * numb_list는 string이 아니라 list 입니다.
        * numb_list의 원소들은 '한 자리'의 '숫자 문자열'을 가정하고 있습니다.

    Args:
        numb_list(list) : 숫자를 원소로 하는 list, 숫자는 1자리씩 나뉘어짐. ex) ['1','2','3']
    Returns:
        res(str) : 숫자발음

    Examples:
        >>> numb_list = ['1','2','3']
        >>> numtokor_sino(numb_list)
        '일이삼'
    '''
    res = ''
    len_numb = len(numb_list)
    dec_list = reversed(range(len_numb))
    for i, d in zip(dec_list, numb_list):
        if d == '1' :
            res += num_to_kor[str(10 ** i)]
        elif d == '0' :
            if len_numb == 1:  # 0 단독일 때,
                res += num_to_kor[str(0)]
            pass
        else:
            res += num_to_kor[d]
            if i > 0:
                res += num_to_kor[str(10 ** i)]
    return res


def numtokor_native(numb_list, counter=False):
    ''' 고유어(하나, 둘...)로 숫자를 세는 함수, 100 미만의 숫자만 고유어로 읽습니다.
        그 이상의 숫자는 한자어로 읽습니다.
        * numb_list는 string이 아니라 list 입니다.
        * numb_list의 원소들은 '한 자리'의 '숫자 문자열'을 가정하고 있습니다.
        * numb_list의 최대 길이는 4입니다. 그 이상 길이를 입력할 경우 빈 string 결과를 리턴합니다.
          이는 numeral 메소드에서 입력 숫자를 최대 길이 4만큼 쪼개고 numtokor_native 메소드를 반복 실행하여 숫자를 처리하기 때문입니다.

    Args:
        numb_list(list) : 숫자 문자열을 원소로 하는 list, 숫자는 1자리씩 나뉘어짐. ex) ['2','3']
        counter(bool) : 원 문자열에 단위 존재 유무, 고유어 발음 구분에 쓰임.
    Returns:
        res(str) : 숫자발음
    '''
    res = ''
    len_numb = len(numb_list)
    if len_numb > 2:  # 두자리 초과하는 숫자인 경우 한자어로 읽기.
        res = numtokor_sino(numb_list)
    elif len_numb > 5:
        pass
    else:
        dec_list = reversed(range(len_numb))
        for i, d in zip(dec_list, numb_list):
            # 단위가 없을 때, '쉰하나' + 스물세번째 처럼 두자리숫자 중 1의자리 숫자가 0이 아닌경우
            if (not counter) or ((i == 1) and (numb_list[-1] != '0')):
                selector = -1
            else:
                selector = 0
            if d == '0' and len_numb > 1:  # 1의자리가 0인 경우는 '영'으로 발음하지 않음
                continue
            res += num_to_kor_native[str(int(d) * (10**i))][selector]

    return res


def numeral(numb, type, native=False, counter=False):
    ''' 읽기 방법, 고유어/한자어에 따라 숫자를 한글로 변환.
        24자리 이상의 숫자는 하나씩 읽어나가는 (type = normal) 방식으로 변환.
        100 미만에 해당하는 수는 native에 따라 고유어/한자어로 읽음.
        100 이상의 수는 한자어 읽기 방식을 따른다.
        * numb는 '숫자(정수) 문자열'임을 가정합니다. 숫자 외 문자가 포함되면 처리과정 중 에러를 발생시킬 것입니다.

    Args:
        numb(str) : str number
        type(str) : type of transformation
            1) 'dec' : 만, 억, 조 단위를 사용하는 한자식 읽기방법
            2) 'normal' : 숫자를 하나씩 읽어 나가는 방법
        native(bool) : 고유어 여부
        counter(bool) : 원 문자열에 단위 존재 유무, numtokor_native에서 고유어 발음 구분에 쓰임.

    Returns:
        res(str) : 숫자발음
    '''
    numb_list = list(numb)
    len_numb = len(numb_list)
    # 24자리 이상의 숫자는 normal 타입으로 변경하여 읽기
    if len_numb > 24:
        type = 'normal'
    res = ''
    if type == 'dec' :
        quotient, remainder = divmod(len_numb, 4)
        quater_split = [remainder] + [4] * quotient  # ex) 134004 -> 13 / 4004 -> [2, 4]
        if quotient > 0:
            local_big_dec = big_dec[-quotient:]     # ex) '만' 단위
        for idx, i in enumerate(quater_split):
            if i:
                if (idx == len(quater_split) - 1) and len(numb_list[:i]) < 3 and native:
                    n = numb_list[:i]
                    res += numtokor_native(n, counter)  # 100의 자리 미만에 해당하는 수만 고유어로 읽는다.
                else:
                    temp_res = numtokor_sino(numb_list[:i])
                    res += temp_res
                    if (temp_res == ''):
                        pass
                    elif (idx != len(quater_split) - 1):
                        res = res + local_big_dec[idx] + ' '
                numb_list = numb_list[i:]
        if res.endswith(' '):  # 문자의 마지막이 공란으로 남아있는 경우에 공란 삭제 (예: '사억 ' -> '사억')
            res = res[:-1]

    elif type == 'normal' :
        for d in numb_list:
            res += num_to_kor[d]

    return res


def float_conversion(numb_str, res, native, counter=False):
    """소수점을 기준으로 정수부, 소수부를 체크.
       소수점이 3개 이상인 경우, 정수부, 소수부1, 소수부2, ... 소수부n 형식으로 나눠짐.
       정수부는 한자어로 읽고 소수부는 고유어로 읽는다.
       * numb_str은 '숫자(소수 가능) 문자열'을 가정합니다. '.' 외의 문자가 포함될 경우 에러 발생.

    Args:
        numb_str (string): 숫자 문자열
        res (string): 입력 문자열, 입력 문자열에 결과 문자열을 추가하여 최종 출력함.
        native(bool) : 고유어 여부
        counter(bool) : 원 문자열에 단위 존재 유무, 고유어 발음 구분에 쓰임.

    Returns:
        res (string): 결과 문자열
    """
    # 소수 인지 확인
    float_str_list = []
    check_float = numb_str.split('.')
    for i in range(len(check_float)):
        if i == 0:
            digit_str = check_float[i]
        else:
            float_str_list.append(check_float[i])

    # 소수일 때는, 고유어로 읽지 않는다.
    if len(float_str_list):
        if int(digit_str) == 0:
            digit_str = '0'
        res += numeral(str(int(digit_str)), type='dec', native=False)
        for float_str in float_str_list:
            res += '쩜 '
            res += numeral(float_str, type='normal', native=False)
    else:
        if int(digit_str) == 0:
            digit_str = '0'
        res += numeral(str(int(digit_str)), type='dec', native=native, counter=counter)

    return res


def num2kor(numb_str, native=False):
    ''''숫자' 혹은 '숫자 + 단위'로 이루어진 문자열을 한글 발음으로 처리.
        +, - 가 숫자 앞에 존재할 경우, 그 개수만큼 '플러스','마이너스'로 변환.
        * numb_str은 '(+, -) + 숫자 + 단위 문자열'을 가정합니다. 숫자만 존재할 경우 에러 발생.
        * 여기서 단위는 최대 2글자를 지니고, 숫자 바로 뒤에오는 모든 문자열을 의미합니다.
        * 단위문자열이 단위 변환 딕셔너리 unit_to_kor1에 포함되지 않는 경우에는 변환되지 않습니다.

    Args:
        numb_str(str) : 입력받은 문자열, '숫자 + 단위' 혹은 '숫자'
        native(bool) : 고유어 여부

    Returns:
        res (string): 결과 문자열
    '''
    res = ''
    counter = False
    # print(numb_str)
    # 단위를 찾고 숫자와 단위 문자열로 분리
    count_filter = '[가-힣a-zA-Z]{1,2}'  # 최대 두글자 단위 지원
    count_str = re.search(count_filter, numb_str)
    if count_str is not None:
        counter = True
    numb_str = re.sub(count_filter, '', numb_str)

    # +, - 처리
    while 1:
        if numb_str.startswith("+"):
            res += '플러스 '
            numb_str = numb_str[1:]
        elif numb_str.startswith("-"):
            res += '마이너스 '
            numb_str = numb_str[1:]
        else:
            break

    # ',' 처리
    numb_str = re.sub(',', '', numb_str)

    # 소수 여부 체크, 변환
    res = float_conversion(numb_str, res, native, counter)

    # 단위 문자열은 숫자 뒤에 추가
    if counter:
        res += count_str.group()

    return res


# NORMALIZE_DICT = {'patterns'       : {'f': normalize_patterns, 'a': None},
#                   'number'         : {'f': normalize_number, 'a': None},
#                   'etc_dictionary' : {'f': normalize_with_dictionary, 'a': etc_dict},
#                   'eng_dictionary' : {'f': normalize_with_dictionary, 'a': eng_dict},
#                   'english'        : {'f': normalize_english, 'a': None},
#                   'character'      : {'f': normalize_character, 'a': None},
#                   'pronunciation'  : {'f': normalize_pronunciation, 'a': None},
#                   'period'         : {'f': join_period, 'a': None}}

if __name__ == '__main__' :
    # print(numeral('12344320', type='dec'))
    # print(numeral('10008900', type='normal'))
    # print(num2kor('788990103.003323'))
    # print(num2kor('44,000,000,000'))
    # print(normalize_number('엠브라텔사는 위성방송 채널의 숫자를 98년부터 지금보다 2배나 늘릴 계획.'))
    print(remove_residual("みんなお疲れ様でした . 帰りましょう、私たちの要塞に  !"))