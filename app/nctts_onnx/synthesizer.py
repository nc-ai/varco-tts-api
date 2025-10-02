# app/resnet/handler.py

import numpy as np
import os
import onnxruntime as ort
import json5
import warnings
from const import MODEL_PATH, MAX_TTS_TEXT_LEN
from logger import setup_logger  # setup_logger가 있는 모듈
from nctp.text_processor import TextProcessor, MultiTextProcessor

import sys
from contextlib import contextmanager

@contextmanager
def suppress_c_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    os.dup2(devnull, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(devnull)
@contextmanager
def suppress_output():
    """stdout + stderr 숨기기"""
    devnull = open(os.devnull, "w")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = devnull, devnull
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        devnull.close()
        
# 로거 생성
Logger = setup_logger()

ort.set_default_logger_severity(3) # ERROR 이상만

class Syntheseizer:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        try:
            self.config = json5.load(open(os.path.join(model_path,"config.json5")))
            self.version = self.config.get("version")
            self.languages = self.config.get("languages")
            self.lang_code_list = list(self.languages.keys())
            self.voices = self.config.get("voices")
            self.voice_id_list = list(self.voices.keys())
        except Exception as e:
            Logger.error(f"failed to initialize config.")
            raise Exception(f"failed to initialize config.")
        self._load_model()
        ##########################################
        ## nctp 
        ##########################################
        NCTTS_TM = os.getenv("NCTTS_TM")
        # Logger.info(f"NCTP NCTTS_TM PATH: {NCTTS_TM}")
        try:
            procs = {}
            for k, v in self.config.get("nctp_params").items():
                procs[k] = TextProcessor(language=v['language'], normalize_step=v['normalize_step'] if type(v['normalize_step']) is str or type(v['normalize_step']) is list else list(v['normalize_step']), use_g2p=v['use_g2p'])
            self.m_proc = MultiTextProcessor(procs)    
        except Exception as e:
            Logger.error(f"failed to initialize text processing.")
            raise Exception(f"failed to initialize text processing.")
        self._warmup()
        
    def _load_model(self):
        ##########################################
        ## TTS 모델 로드
        ##########################################
        CUDA_VISIBLE_DEVICES = os.getenv("CUDA_VISIBLE_DEVICES")
        # Logger.info(f"CUDA_VISIBLE_DEVICES:  {CUDA_VISIBLE_DEVICES}")
        Logger.info(f"model load started.")
        try:
            if "CUDAExecutionProvider" not in ort.get_available_providers():
                Logger.error(f"Failed to load with GPU")
                raise Exception("Failed to load with GPU")
            so = ort.SessionOptions()
            so.log_severity_level = 3 # 로그 ERROR 이상만 출력
            so.log_verbosity_level = 0
            so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL #세 션을 전역(global) 객체로 두고, 요청마다 새 세션을 만들지 않도록
            self.sess_am = ort.InferenceSession(
                os.path.join(self.model_path,"am.onnx"), sess_options=so,
                providers=[
                    ("CUDAExecutionProvider", {"device_id": 0}),  # 0번 GPU
                    "CPUExecutionProvider"                        # 실패시 CPU fallback
                ],
            )
            # vocoder
            self.sess_voc = ort.InferenceSession(
                os.path.join(self.model_path,"vocoder.onnx"), sess_options=so,
                providers=[
                    ("CUDAExecutionProvider", {"device_id": 0}),  # 0번 GPU
                    "CPUExecutionProvider"                        # 실패시 CPU fallback
                ],
            )
            if "CUDAExecutionProvider" not in self.sess_am.get_provider_options():
                Logger.error(f"Failed to load with GPU")
                raise Exception("Failed to load with GPU")
        except Exception as e:
            Logger.error(f"model load failed.")
            raise Exception("model load failed.")
        Logger.info(f"model load finished.")
        
    def _warmup(self):
        Logger.info("model warm-up started.")
        try:
            first_voice_id = next(iter(self.voices))
            _, _ = self.infer(first_voice_id,"ko_KR","[l]하하하[/l] 그림자왕? 리세온? 무슨 말이야? 난... 그냥... 난 누구인지도 몰라. 이 망토도, 이 단검도... 모두 낯설기만 해.")
        except Exception as e:
            Logger.error(f"warm-up failed.")
            raise Exception("warm-up failed.")
        Logger.info("model warm-up finished.")
    

    def infer(self, voice_id, lang_code, text, emotion="neutral"):
        if voice_id not in self.voice_id_list:
            raise ValueError(f"voice_id '{voice_id}' does not exist.")
        if not self.voices[voice_id]["emotion"].get(emotion, False):
            raise ValueError(f"'{emotion}' emotion is not supported by the selected voice_id '{voice_id}'.")
        if lang_code not in self.lang_code_list:
            raise ValueError(f"Unsupported language: {lang_code}. "
                            f"Supported languages are: {', '.join(self.lang_code_list)}")
        if len(text) > MAX_TTS_TEXT_LEN:
            raise ValueError(f"Input text too long ({len(text)} > {MAX_TTS_TEXT_LEN} characters).")
        try:
            voice_id = self.voices[voice_id]["emotion"][emotion]
            wav, sr = self._synth(voice_id, lang_code, text)
            return wav, sr
        except Exception as e:
            raise Exception(f"Internal error occurred.")
        
    def _synth(self, voice_id, lang_code, text):
        voice_index = self.voices[voice_id]['voice_index']
        language = self.languages[lang_code]["language"]
        lang_idx = self.languages[lang_code]["index"]
        with suppress_c_stderr():
            with suppress_output():
                text, style_dict = self.m_proc.processors[language].parse(text)
                symbol = self.m_proc.input2symbol(text, options=[], language=language)
                        
            if language == "taiwanese":
                symbol = np.array(symbol)
                plb = np.where((173 <= symbol) & (symbol <= 176))
                symbol = np.delete(symbol, plb)
                p = np.where( (symbol > 1) & (symbol < 10) )
                symbol = np.insert(symbol, p[0] + 1, 10)
                if symbol[-2] == 10:
                    symbol = np.delete(symbol, -2)
            symbol, punc, p_pid = self.m_proc.processors[language].split_punc(symbol, get_pure=True)
            symbol, tone, punc, _, t_pid = self.m_proc.processors[language].split_tone(symbol, punc=punc, get_pure=True)
            symbol, styletag, punc, tone, s_pid = self.m_proc.processors[language].split_style_tag(symbol, punc=punc, tone=tone, get_pure=True)
            text_lengths = np.array([len(symbol)])


            texts = np.pad(symbol, (0,750-symbol.shape[0]))
            punc = np.pad(punc, (0,750-symbol.shape[0]))
            tone = np.pad(tone, (0,750-symbol.shape[0]))
            styletag = np.pad(styletag, (0,750-symbol.shape[0]))

            texts = np.expand_dims(texts, 0)
            punc = np.expand_dims(punc, 0)
            tone = np.expand_dims(tone, 0)
            styletag = np.expand_dims(styletag, 0)
            speaker_ids = np.array([voice_index])
            lang_num = np.array([lang_idx])
            input_ = {'texts':texts,
            'puncs':punc,
            'tone':tone,
            'styletag':styletag,
            'text_lengths':text_lengths,
            'speaker_ids':speaker_ids,
            'lang_num':lang_num}
            # print(input_)
            output_names = [self.sess_am.get_outputs()[0].name, self.sess_am.get_outputs()[1].name]  # ganspeech
            mels, durations = self.sess_am.run(output_names, input_)
            mels = np.transpose(mels, (0,2,1))
            input_ = {'fmels':mels}
            output_names = [self.sess_voc.get_outputs()[0].name]
            wavs = self.sess_voc.run(output_names, input_)
            total_length = int(np.round(durations).sum())
            wavs = wavs[0][:total_length*1024]
        
        return wavs, 44100 #sr