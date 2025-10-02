from nctp.dictionary import json_to_dict
from collections import OrderedDict

eng_arpabet_dict = OrderedDict(json_to_dict("eng_arpabet"))
eng_ipa_dict = OrderedDict(json_to_dict("eng_ipa"))
