
from unidecode import unidecode
from tn.chinese.normalizer import Normalizer
from nctp.dictionary.chi_pid_sDict import chi_dict
from tn.chinese.normalizer import Normalizer
from nctp.ncg2pc.prosody_predictor import ProsodyPredictor
from nctp.ncg2pc.chinese_handler import ChineseProcessor
import re
import os

CHI_SYMBOLS = list(chi_dict.keys())
NCTTS_TM = os.environ.get("NCTTS_TM")

normalizer = Normalizer()
try:
    fp_prosody = f"{NCTTS_TM}/chinese_processor/prosody2id.txt"
    fp_polyphone = f"{NCTTS_TM}/chinese_processor/polyphone_phone.txt"
    fp_model  =f"{NCTTS_TM}/chinese_processor/19.pt"
    prosody_predictor = ProsodyPredictor(fp_prosody=fp_prosody, fp_polyphone=fp_polyphone, fp_model=fp_model)
    try:
        del artifactory_obj
    except: pass
except Exception as e:
    print(e)
    raise FileNotFoundError("필수 체크포인트를 먼저 다운로드 하세요")

PROSODY_LABEL = re.compile(r"#[0-9]")

def remove_prosody(text):
    prds = re.findall(PROSODY_LABEL, text)
    if len(prds) > 0:
        text = re.sub(PROSODY_LABEL, "", text)
    return text

def chn_normalize(text):
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

def prosody_predict(text):
    return prosody_predictor(text)

def handle_baker_like(text):
    # Text: 한자|병음 형식
    QUATO = r'[《》「」\"\'\“\”（）]'
    text = re.sub(QUATO, "", text)
    text = text.replace("。", ".").replace("，", ",").replace("、", ",").replace("？", "?").replace("！", "!").replace("：", ",").replace("；", ",")
    han, phn = text.split("|")
    # proc = ChineseProcessor()
    sym = ChineseProcessor.get_phoneme_from_char_and_pinyin(han, phn.split(" "))
    return sym




if __name__ == "__main__":
    from nctp.ncg2pc.chinese_handler import ChineseProcessor
    from nctp.text_processor import TextProcessor, MultiTextProcessor
    from nctp.common import Language
    import os
    os.environ["NCTTS_TM"] = "/SGV/users/mkyu/proj/NCTTSs/NCTTS-bitbang/tts-engine/nctts.tm"

    processor = TextProcessor("chinese", "baker", use_g2p=False)

    proc = ChineseProcessor()

    text = "在下面！ 你永远无法打败我。 绝不。"
    text = "右蛮#1舞#1袅袅#3， 左琼#2歌#1昔昔#4。"
    text = "你们#1尝尝#2我#1做的#1麻辣拌#3,和#1外面的#1比起来#2味道#1怎么样啊#4?|ni3 men5 chang2 chang2 wo3 zuo4 de5 ma2 la4 ban4 han4 wai4 mian4 de5 bi6 qi3 lai2 wei4 dao4 zen3 me5 yang4 a5"
    # han, phn = text.split("|")
    # text2 = "五万元"

    piny = processor.normalize(text)
    print(piny)
    sym  = processor.symbolize(piny, options=[])
    print([(p, s) for p, s in zip(piny, sym)])
