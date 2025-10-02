from collections import OrderedDict
from nctp.dictionary import json_to_dict

universe_dict_raw = json_to_dict("universe_eng_dict", upper=True)

universe_dict = OrderedDict(sorted(universe_dict_raw.items(), key=lambda x: len(x[0]), reverse=True))
