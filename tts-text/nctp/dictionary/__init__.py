import json
import json5
import os


json_f_dict = {
    "eng_arpabet"       : 'dict_json/eng_arpabet.json',
    "eng_ipa"           : 'dict_json/eng_ipa.json',
    "eng_dict"          : 'dict_json/eng_dict.json',
    "kor_ipa"           : 'dict_json/kor_ipa.json',
    "jpn_prosody"       : 'dict_json/jpn_prosody.json',
    "chinese"           : 'dict_json/chn_dict.json',
    "taiwanese"         : 'dict_json/twn_dict.json',
    "enp2twp_dict"      : 'dict_json/enp2twp_dict.json5',
    "QJ2BJ_dict"        : 'dict_json/QJ2BJ_dict.json5'
    

}


def json_to_dict(key, upper=False):
    """ json_f_dict 딕셔너리 value의 json file 경로로부터 dictionary 생성

    Args:
        key ([type]): json_f_dict의 key
        upper (bool, optional): dictionary내 key 대문자 치환할지 여부. Defaults to False.

    Returns:
        [dict]: dictionary
    """
    json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), json_f_dict[key])
    with open(json_file, encoding='utf-8') as jf:
        if json_file.endswith(".json"):
            dictionary = json.load(jf)
        elif json_file.endswith(".json5"):
            dictionary = json5.load(jf)
    if upper:
        upper_dict = {}
        for key in dictionary.keys():
            upper_dict[key.upper()] = dictionary[key]
        dictionary = upper_dict
        del upper_dict
    return dictionary
