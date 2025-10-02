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
import re

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
        self.puncs = ";；:~-😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉🐢🍊🍋 "
        self.puncs_pat = r"[;；:~\-😦😧😐😑😃😄😔😞😫😱😤😬🙈🙉🐢🍊🍋 ]"

    def find_occurrence_at_index(self, s, index):
        # Ensure the index is within the bounds of the string
        if index < 0 or index >= len(s):
            return -1  # Invalid index
        
        char = s[index]
        count = 0
        
        # Iterate through the string up to the given index
        for i in range(index + 1):
            if s[i] == char:
                count += 1
        
        return count

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
        text = text.replace(".", "。").replace(",", "、").replace("?", "？").replace("!", "！").replace(",", "：").replace("，", "、")
        space_pos = re.finditer(self.puncs_pat, text)
        x = list()
        for pos in space_pos:
            sym = pos.group()
            back_idx = pos.start() - 1
            if back_idx < 0:
                back_idx = 0
            try:
                if back_idx == 0:
                    back_sym = "S"
                    back_sym_nocur = 0
                else:
                    back_sym = text[back_idx]
                    back_sym_nocur = self.find_occurrence_at_index(text, back_idx)
            except Exception as e:
                back_sym = "E"
                back_sym_nocur = -1
            x.append(
                (sym, back_sym, back_sym_nocur)
            )

        text = re.sub(self.puncs_pat, "", text)
        if type(text) == str:
            text = [text]
        batch_inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            is_split_into_words=True,
            return_tensors="pt",
        )
        
        # print(batch_inputs, batch_inputs['input_ids'].shape)
        _, prd = self.model.export_forward(batch_inputs['input_ids'])
        prd = prd.argmax(dim=-1)
        pred = [self.prosodies_val[str(int((p)))] for p in prd[0, 1:]]
        out = []
        # print(len(text[0]), len(pred))
        for i, (p, rd) in enumerate(zip(text[0], pred)):
            out.append(p)
            if rd == "#0":  continue
            if p in self.puncs:
                out.insert(-1, rd)
            else:
                out.append(rd)
        
        tmp = "".join(out)
        tmp = re.sub(r"#[0-9]", "_", tmp)
        # insert removed puncs
        for cand in x:
            target = cand[0]
            ref = cand[1]
            ref_pos = cand[2]
            if ref == ".": # .은 정규식에서 모든 문자
                ref = "\."
            if ref == "E":
                position = -1
            elif ref == "S":
                position = 0
            else:
                position = list(re.finditer(ref, tmp))[ref_pos-1].start() + 1
                if position >= len(out):
                    position = len(out) - 1
                if "#" in out[position]:
                    position += 1
            out.insert(position if position > 0 else 0, target)
            tmp = "".join(out)
            tmp = re.sub(r"#[0-9]", "_", tmp)
        
        # 보정1, 중간에 출현하는 #4는 #3으로 바꿔 휴지구간으로 지정한다.
        n_s4 = sum([1 if sym=="#4" else 0 for sym in out])
        out = "".join(out).replace("。", ".").replace("，", ",").replace("、", ",").replace("？", "?").replace("！", "!").replace("：", ",")
        if n_s4 > 1:
            out = re.sub(r"#4", "#3", out, n_s4 - 1)
        # 보정2, 반점과 #3이 만나지 않는 경우, #3을 강제로 삽입한다.
        out = re.sub(r"([\u4E00-\u9FFF]),",  r'\1#3,', out)
        # 보정3, 물음표, 느낌표 뒤에는 무조건 #3이 오도록 한다.
        out = re.sub(r"(#[0-2])(!|\?)", r"#3\1", out)
        out = re.sub(r"(!|\?)(#[0-2])", r"\1#3", out)

        return out

if __name__ == "__main__":
    # print(AutoTokenizer.from_pretrained(pretrained_model_name_or_path=f"{NCTTS_TM}/bert"))
    fp_prosody = f"{NCTTS_TM}/taiwanese_processor/prosody2id.txt"
    fp_polyphone = f"{NCTTS_TM}/taiwanese_processor/polyphone_phone.txt"
    fp_model  = f"{NCTTS_TM}/taiwanese_processor/19.pt"
    bert_path = f"{NCTTS_TM}/bert"
    prosody_predictor = ProsodyPredictor(fp_prosody=fp_prosody, fp_polyphone=fp_polyphone, fp_model=fp_model)
    print(prosody_predictor("要如何共享倉庫？噓！這是商業機密。"))
