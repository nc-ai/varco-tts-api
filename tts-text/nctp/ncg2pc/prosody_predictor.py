# Copyright (c) 2022, Binbin Zhang (binbzha@qq.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# NOTE: WeNetTTS 에서 가져온 모델입니다.
# https://github.com/wenet-e2e/wetts/blob/main/wetts/frontend/model.py
# Prosody Label이 없는 경우 사용됩니다!!

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel
from transformers import AutoTokenizer
import os

IGNORE_ID = -100
NCTTS_TM = os.environ.get("NCTTS_TM")

class FrontendModel(nn.Module):
    def __init__(self, num_polyphones: int, num_prosody: int):
        super(FrontendModel, self).__init__()
        self.bert = AutoModel.from_pretrained("bert-base-chinese")
        for param in self.bert.parameters():
            param.requires_grad_(False)
        self.transform = nn.TransformerEncoderLayer(
            d_model=768, nhead=8, dim_feedforward=2048, batch_first=True
        )
        self.phone_classifier = nn.Linear(768, num_polyphones)
        self.prosody_classifier = nn.Linear(768, num_prosody)
        self.eval()

    def _forward(self, x):
        mask = x["attention_mask"] == 0
        bert_output = self.bert(**x)
        x = self.transform(bert_output.last_hidden_state, src_key_padding_mask=mask)
        phone_pred = self.phone_classifier(x)
        prosody_pred = self.prosody_classifier(x)
        return phone_pred, prosody_pred

    def forward(self, x):
        return self._forward(x)

    def export_forward(self, x):
        assert x.size(0) == 1
        x = {
            "input_ids": x,
            "token_type_ids": torch.zeros(1, x.size(1), dtype=torch.int64),
            "attention_mask": torch.ones(1, x.size(1), dtype=torch.int64),
        }
        phone_logits, prosody_logits = self._forward(x)
        phone_pred = F.softmax(phone_logits, dim=-1)
        prosody_pred = F.softmax(prosody_logits, dim=-1)
        return phone_pred, prosody_pred

class ProsodyPredictor(object):
    def __init__(self, fp_prosody, fp_polyphone, fp_model):
        prosodies = open(fp_prosody, 'r', encoding='utf-8').read().split("\n")
        if prosodies[-1].strip() == "": prosodies.pop(-1)
        polyphones = open(fp_polyphone, 'r', encoding='utf-8').read().split("\n")
        if polyphones[-1].strip() == "": polyphones.pop(-1)
        polyphones_dict = {k:v for v, k in enumerate(polyphones)}
        prosodies_dict = {v.split(" ")[0]:v.split(" ")[1] for v in prosodies}

        self.prosodies_val = {v:k for k, v in prosodies_dict.items()}
        self.polyphones_val = {v:k for k, v in polyphones_dict.items()}
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")

        model = FrontendModel(len(polyphones), len(prosodies))
        model.load_state_dict(torch.load(fp_model, map_location="cpu"), strict=False)
        model.eval()

        self.model = model
        self.puncs = {
            "_": 0,
            "eos": 1,
            "~": 69,
            "!": 70,
            "！": 70,
            "'": 71,
            ",": 74,
            "，":74,
            "-": 75,
            "。": 76,
            "?": 79,
            "？": 79,
            "、":74,
            ".": 76,
        }

    @torch.no_grad()
    def __call__(self, text):
        """
            input:
                text(str|list): input text -> batchfy를 위해 list로 랩핑합니다.
                    ex) 妈妈当时表示，儿子开心得像花儿一样。
            return:
                text(str): prosody predicted
                    ex) 妈妈#2当时#1表示#3，儿子#2开心得#1像#1花儿一样#4。

        """
        if type(text) == str:
            text = [text]
        batch_inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            is_split_into_words=True,
            return_tensors="pt",
        )
        _, prd = self.model.export_forward(batch_inputs['input_ids'])
        prd = prd.argmax(dim=-1)
        pred = [self.prosodies_val[str(int((p)))] for p in prd[0, 1:-1]]
        out = []
        
        for i, (p, rd) in enumerate(zip(text[0], pred)):
            out.append(p)
            if rd == "#0":  continue
            if p in self.puncs:
                if str(out[-2]).startswith("#"):
                    out[-2] = rd
                else:
                    out.insert(-1, rd)
            else:
                out.append(rd)
        return "".join(out)

if __name__ == "__main__":
    import re

    def fix_prosodic_label(text):
        return re.sub(r"#[0-9]", "", text)

    print(AutoTokenizer.from_pretrained(pretrained_model_name_or_path=f"{NCTTS_TM}/bert"))
    fp_prosody = f"{NCTTS_TM}/taiwanese_processor/prosody2id.txt"
    fp_polyphone = f"{NCTTS_TM}/taiwanese_processor/polyphone_phone.txt"
    fp_model  = f"{NCTTS_TM}/taiwanese_processor/19.pt"
    bert_path = f"{NCTTS_TM}/bert"
    prosody_predictor = ProsodyPredictor(fp_prosody=fp_prosody, fp_polyphone=fp_polyphone, fp_model=fp_model,)
    print(prosody_predictor("喔，少俠！我就知道你會再來找我。封印的經典？那、那是什麼？我、我不知道啊。"))
    print(fix_prosodic_label(prosody_predictor("喔，少俠！我就知道你會再來找我。封印的經典？那、那是什麼？我、我不知道啊。")))
