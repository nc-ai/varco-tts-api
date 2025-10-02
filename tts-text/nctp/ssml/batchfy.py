
import os
from typing import Dict, List, Optional, Union
from collections import OrderedDict
import json
import re

import numpy as np

from nctp.symbols import E_VEF, S_VEF, S_VEF_IDX, E_VEF_IDX, BREAK, BREAK_IDX, CommonSymbols, SPACE
from nctp.text_processor import MultiTextProcessor, TextProcessor
from nctp.ssml.process_parsed import EmojiBatchfy, VoiceEffect, BreakEffect
from nctp.ssml.ssml_parser import process_ssml_str

cosym = CommonSymbols()

def symbolize_and_chunk(ssml_text, ssml_config, m_proc: MultiTextProcessor):
    parsed_list = process_ssml_str(ssml_text, config=ssml_config)
    batch = EmojiBatchfy()
    _ = batch.process_parsed_list(parsed_list)
    symbols = m_proc.input2symbol(batch.effect_string, options=[], language='ko')
    refined_symbols, styles = make_styles(symbols, batch.effect_queue)
    # refined_symbols, styles = make_styles_without_symbol(symbols, batch.effectQueue)
    return refined_symbols, styles

def make_styles(symbols, effect_queue):
    '''
    symbols에서 voiceeffect용 심볼 지우기,
    voiceeffect용 심볼 지워진 symbols 가지고 style 만들기
    '''
    refined_symbols = symbols
    length = len(refined_symbols)
    styles = {
        # 'style': np.zeros(length),
        # 'reverb': np.zeros(length),
        'duration': np.zeros(length),
        'speed': np.ones(length),
        'pitch': np.ones(length),
        'energy': np.ones(length)
    }

    effects_by_range = OrderedDict()
    for e in effect_queue:
        if isinstance(e, VoiceEffect):
            r = (e.start, e.end)
            if r not in effects_by_range:
                effects_by_range[r] = []
            effects_by_range[r].append(e)
    start_effect = False
    first_time = False
    for i, s in enumerate(refined_symbols):
        if s == S_VEF_IDX: # voice effect start symbol
            start_effect = True
            first_time = True
            r, effects = effects_by_range.popitem(last=False)
        elif s == E_VEF_IDX: # voice effect end symbol
            start_effect = False

        if start_effect and first_time:
            first_time = False
        elif start_effect and not first_time:
            for e in effects:
                if e.type in styles:
                    styles[e.type][i] = float(e.value)

    return refined_symbols, styles

def make_styles_without_symbol(symbols: List[int], effect_queue):
    # refined_symbols = symbols
    refined_symbols = []
    styles = {
        # 'style': [],
        # 'reverb': [],
        'duration': [],
        'speed': [],
        'pitch': [],
        'energy': []
    }

    effects_by_range = OrderedDict()
    break_effect = list()
    for e in effect_queue:
        if isinstance(e, VoiceEffect):
            r = (e.start, e.end)
            if r not in effects_by_range:
                effects_by_range[r] = []
            effects_by_range[r].append(e)
        if isinstance(e, BreakEffect):
            break_effect.append(e.length)
    start_effect = False
    first_time = False

    for i, s in enumerate(symbols):
        if s == S_VEF_IDX: # voice effect start symbol
            start_effect = True
            first_time = True
            r, effects = effects_by_range.popitem(last=False)
        elif s == E_VEF_IDX: # voice effect end symbol
            start_effect = False
        else:
            # start/end symbol이 아닌 경우에는 symbol append            
            refined_symbols.append(s)
            for k in styles:
                if k == "duration":
                    styles[k].append(0.0)
                else:
                    styles[k].append(1.0)
        if s == BREAK_IDX:
            def convert(x): # 통계적으로 찾은 점화식입니다.
                if x <= 150:
                    x = x+25
                else: 
                    x = (x+200)/2
                return x / (1000. * 256. / 22050.) + 3
            sil = break_effect.pop(0)
            styles["duration"][-1] = convert(float(sil)) 
            refined_symbols[-1] = cosym.sym2num[SPACE] # -4 -> 10 (space)로 변경
        
        if start_effect and first_time:
            first_time = False
        elif start_effect and not first_time:
            for e in effects:
                if e.type in styles:
                    styles[e.type][-1] = float(e.value)
    styles = {k: np.array(v, dtype=np.float64) for k, v in styles.items()}

    return refined_symbols, styles


def split_all(text, sep):
    items = []
    surrounded = []
    
    pattern = rf'([{sep}])(.*?)([{sep}])'
    
    pos = 0
    for match in re.finditer(pattern, text):
        start, end = match.span()
        
        if pos < start:
            items.append(text[pos:start])
            surrounded.append(False)
            
        items.append(match.group(2))
        surrounded.append(True)
        
        pos = end
        
    if pos < len(text):
        items.append(text[pos:])
        surrounded.append(False)
        
    return items, surrounded

class SSMLTextProcessor:
    def __init__(
            self, m_proc: MultiTextProcessor,
            ssml_config: Optional[Union[Dict, str]]=None
        ):
        self._m_proc = m_proc
        if ssml_config is None:            
            with open(f"{os.path.dirname(os.path.abspath(__file__))}/config-nc-ssml.json", "r") as f:
                data = f.read()
                self._ssml_config = json.loads(data)
        elif isinstance(ssml_config, str):
            with open(ssml_config, "r") as f:
                data = f.read()
                self._ssml_config = json.loads(data)
        else:
            self._ssml_config = ssml_config
        self._m_proc.symbols.update({S_VEF: S_VEF_IDX, E_VEF: E_VEF_IDX, BREAK: BREAK_IDX})
        for lang, proc in sorted(self._m_proc.processors.items()):
            proc._symbols.update({S_VEF: S_VEF_IDX, E_VEF: E_VEF_IDX, BREAK: BREAK_IDX}) # added break symbol
        self._DEFAULT_NAME = 'NC_Game/FeyActress'
        self._DEFAULT_LANGUAGE = 'ko'

    def parse(self, ssml_text):
        parsed_list = process_ssml_str(ssml_text, config=self._ssml_config)
        batch = EmojiBatchfy()

        for l in parsed_list:
            # parsed_list를 순회하며 탐색
            if len(l) == 3 and l[1] == 'language':
                language_id = l[2].lower() # ssml language id is generalized (240613)

        _ = batch.process_parsed_list(parsed_list, lang=language_id) # parsing은 언어 별로 진행되어야 함. (240711)
        return batch, parsed_list
    
    def input2symbol(
            self, batch, use_voice_effect_symbol=False,
            options=[], translator=None, language=None, code_switching=False
        ):
        
        symbols = self._m_proc.input2symbol(
            batch.effect_string, options=options,
            translator=translator, language=language, code_switching=code_switching
        )
        if use_voice_effect_symbol:
            refined_symbols, styles = make_styles(symbols, batch.effect_queue)
        else:
            refined_symbols, styles = make_styles_without_symbol(symbols, batch.effect_queue)
        return refined_symbols, styles


if __name__=='__main__':
    import json

    # ssml_str = '''<speak>안녕하세요.<nc:voiceeffect speed="1.2">빠른 말</nc:voiceeffect>
    # <voice name="NC_Base/NcFemale" language="EN">합성 문장을 <nc:voiceeffect energy="1.2">입력하세요.</nc:voiceeffect></voice>
    # <nc:voiceeffect pitch="1.2">좋은 하루입니다</nc:voiceeffect>
    # <voice name="NC_Base/NcFemale">합성 문장을 입력하세요.</voice>
    # </speak>'''
    ssml_str = '''<speak>안녕하세요.<nc:voiceeffect pitch="1.3" speed="1.2">빠른 말</nc:voiceeffect>
    <voice name="NC_Base/NcFemale" language="EN">합성 문장을 <nc:voiceeffect energy="1.2">입력하세요.</nc:voiceeffect></voice>
    <nc:voiceeffect pitch="1.2">좋은 하루입니다</nc:voiceeffect>
    <voice name="NC_Base/NcFemale">합성 문장을 입력하세요.</voice>
    </speak>'''
    # ssml_str = '''<speak><nc:voiceeffect pitch="1.3" speed="1.2">안녕하세요. 좋은 아침이에요.</nc:voiceeffect></speak>'''


    nctp_params = {
        "korean": {
            "language": "korean",
            "normalize_step": "default",
            "use_g2p": False,
        },
        "english": {
            "language": "english_arpabet",
            "normalize_step": "default",
            "use_g2p": True,
        },
        "japanese": {
            "language": "japanese_prosody",
            "normalize_step": "default",
            "use_g2p": True,
        },
        "chinese": {
            "language": "chinese",
            "normalize_step": "default_prosody",
            "use_g2p": True,
        },
    }
    procs = {}
    for k, v in nctp_params.items():
        procs[k] = TextProcessor(
            language=v['language'],
            normalize_step=v['normalize_step'] if type(v['normalize_step']) is str or type(v['normalize_step']) is list else list(v['normalize_step']),
            use_g2p=v['use_g2p']
        )
    m_proc = MultiTextProcessor(procs)
    print(f"multi text processor symbols: {m_proc.symbols}")

    global cur_val2sym
    cur_val2sym = m_proc.processors['korean']._val2syms
    ssml_tp = SSMLTextProcessor(m_proc)

    # with open(f"{os.path.dirname(os.path.abspath(__file__))}/config-nc-ssml.json", "r") as f:
    #     data = f.read()
    #     ssml_config = json.loads(data)
    # symbols, styles = symbolize_and_chunk(ssml_str, ssml_config, m_proc)

    # ssml_tp = SSMLTextProcessor(m_proc)
    # symbols, styles, name, language = ssml_tp.input2symbol(ssml_str)

    # for i in range(len(symbols)):
    #     o = f"{cur_val2sym[symbols[i]]}"
    #     for k, v in styles.items():
    #         o += f" {k}: {v[i]}"
    #     print(o)

    ssml_str = '''<speak language="EN">Hello. This is a test sentence.<nc:voiceeffect pitch="1.3" speed="1.2">Fast words.</nc:voiceeffect></speak>'''
    symbols, styles, name, language = ssml_tp.input2symbol(ssml_str)    
    for i in range(len(symbols)):
        o = f"{m_proc.processors['english']._val2syms[symbols[i]]}"
        for k, v in styles.items():
            o += f" {k}: {v[i]}"
        print(o)