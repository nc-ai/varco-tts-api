
from unidecode import unidecode
from tn.chinese.normalizer import Normalizer
from nctp.dictionary.twn_pid_sDict import twn_dict
from tn.chinese.normalizer import Normalizer
from nctp.ncg2pt.prosody_predictor import ProsodyPredictor
from nctp.ncg2pt.taiwanese_handler import TaiwaneseProcessor
import re
import os
TWN_SYMBOLS = list(twn_dict.keys())
NCTTS_TM = os.environ.get("NCTTS_TM")

normalizer = Normalizer(traditional_to_simple=False)
try:
    fp_prosody = f"{NCTTS_TM}/taiwanese_processor/prosody2id.txt"
    fp_polyphone = f"{NCTTS_TM}/taiwanese_processor/polyphone_phone.txt"
    fp_model  = f"{NCTTS_TM}/taiwanese_processor/19.pt"
    prosody_predictor = ProsodyPredictor(fp_prosody=fp_prosody, fp_polyphone=fp_polyphone, fp_model=fp_model)
    try:
        del artifactory_obj
    except: pass
except:
    raise FileNotFoundError("필수 체크포인트를 먼저 다운로드 하세요")

PROSODY_LABEL = re.compile(r"#[0-9]")

def remove_prosody(text):
    prds = re.findall(PROSODY_LABEL, text)
    if len(prds) > 0:
        text = re.sub(PROSODY_LABEL, "", text)
    return text

def twn_normalize(text):
    new_text = []
    text = text.replace(" ", "_")
    cur_char = ""
    text = list(text)
    while True:
        try:
            cur_char = text.pop(0)
            if cur_char == "#":
                cur_char += text.pop(0)
            new_text.append(cur_char)
        except:
            break
    cur_text = "".join([c if "#" not in c else " " for c in new_text])
    prosodies = [c for c in new_text if "#" in c]
    text = normalizer.normalize(cur_text).replace("。", ".").replace("，", ",").replace("、", ",").replace("？", "?").replace("！", "!").replace("：", ",").replace("；", ",")

    result = []
    for c in text:
        if c == " ":
            result.append(prosodies.pop(0))
        else:
            result.append(c)

    return "".join(result).replace("_", " ")

def twn_normalize_new(text):
    pattern = r'(#[0-4]{1})' #prosody 문자 #0~4 남기기 위해 
    pattern_target01 =r'(\d+年|\d+月|\d+日)'  #연월일 ex> 86年8月18日
    pattern_target02 = r'[^\u4E00-\u9FFF]+' # 중국어가 아닌 문자
    words = re.split(pattern, text)
    for idx, word in enumerate(words):
        if not word.startswith("#"):    
            words[idx] = re.sub(pattern_target01,lambda x: normalizer.normalize(x.group()), word)
            words[idx] = re.sub(pattern_target02,lambda x: normalizer.normalize(x.group()), word)
    text = "".join(words)
    return text

def prosody_predict(text):
    # return prosody_predictor(text)
    # 수정: 영어는 prosody 안하기
    pattern = r'([a-zA-Z ]+)'
    words = re.split(pattern, text)
    for idx, word in enumerate(words):
        if not word.strip(): # 공백문자만 있는 경우
            words[idx]=""
            continue
        if not re.search(pattern,word): # 한자
            if idx == len(words)-1:    #4(문장 끝 라벨) 삭제
                words[idx] = prosody_predictor(word.replace(" ","")).replace("#4", "") # 
            else:       # 단어 경계 #4(문장 끝 라벨) -> #1 바꿈.
                words[idx] = re.sub("#4$","",prosody_predictor(word.replace(" ","")))
        else: #영어
            words[idx] = re.sub(" +"," ",words[idx].strip()) #
            if idx != 0: words[idx] = "#1"+words[idx]  # 영어 단어 경계 #1 추가
            if idx != len(words): words[idx] = words[idx]+"#1"  # 영어 단어 경계 #1 추가
    text = "".join(words)+"#4"  # #4(문장 끝 라벨) 추가
    return text
    

def handle_baker_like(text):
    # Text: 한자|병음 형식
    QUATO = r'[《》「」\"\'\“\”（）]'
    text = re.sub(QUATO, "", text)
    text = text.replace("。", ".").replace("，", ",").replace("、", ",").replace("？", "?").replace("！", "!").replace("：", ",").replace("；", ",").replace("；", ",")
    han, phn = text.split("|")
    sym = TaiwaneseProcessor.get_phoneme_from_char_and_pinyin(han, phn.split(" "))
    return sym




if __name__ == "__main__":
    from nctp.ncg2pc.chinese_handler import ChineseProcessor
    from nctp.text_processor import TextProcessor, MultiTextProcessor
    from nctp.common import Language
    import os
    os.environ["NCTTS_TM"] = "/SGV/users/mkyu/proj/NCTTSs/NCTTS-bitbang/tts-engine/nctts.tm"

    processor = TextProcessor("taiwanese", "baker", use_g2p=False)


    text = "在下面！ 你永远无法打败我。 绝不。"
    text = "右蛮#1舞#1袅袅#3， 左琼#2歌#1昔昔#4。"
    text = "你们#1尝尝#2我#1做的#1麻辣拌#3,和#1外面的#1比起来#2味道#1怎么样啊#4?|ni3 men5 chang2 chang2 wo3 zuo4 de5 ma2 la4 ban4 han4 wai4 mian4 de5 bi6 qi3 lai2 wei4 dao4 zen3 me5 yang4 a5"
    text = "央视#1《是真的吗#3》栏目#1记者#1采访了#1相关#1专家#4.|yang1 shi4 shi4 zhen1 de5 ma5 lan2 mu4 ji4 zhe3 cai6 fang3 le5 xiang1 guan1 zhuan1 jia1"
    # han, phn = text.split("|")
    # text2 = "五万元"

    piny = processor.normalize(text)
    print(piny)
    sym  = processor.symbolize(piny, options=[])
    print([(p, s) for p, s in zip(piny, sym)])
