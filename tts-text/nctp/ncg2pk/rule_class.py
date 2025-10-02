from nctp.ncg2pk.holder_class import JamoHolder
from nctp.ncg2pk.utils import mapping, tag_checker
from abc import *


class Rule(metaclass=ABCMeta):
    def __init__(self, rule_name):
        self.rule_name = rule_name

    @abstractmethod
    def condition(self):
        return True


class PronunciationRule(Rule):
    def __init__(self, rule_name: str, rule_dict: dict):
        super().__init__(rule_name)
        self.rule_dict = rule_dict
        self.rule_ids = rule_dict.keys()
        self._sub_rules = []
        self._make_sub_rules()

    def _make_sub_rules(self):
        for rule_id in self.rule_ids:
            self.sub_rules.append(SubRule(rule_id, self.rule_dict[rule_id]))

    @property
    def condition(self):
        return self.rule_dict

    @property
    def sub_rules(self):
        return self._sub_rules


class SubRule(Rule):
    def __init__(self, rule_id: str, sub_rule_list: list):
        self.rule_id = rule_id
        self._sub_rule_list = sub_rule_list
        self.cond_keys = self._cond_key_builder()
        self.boolsteps = self._boolstep_builder()
        self.cond_pattern = self._cond_pattern_builder()

    def __len__(self):
        return len(self._sub_rule_list)

    @property
    def condition(self):
        return self._sub_rule_list

    def get_cond_key(self, idx) -> tuple:
        return self.cond_keys[idx]

    def get_cond_pattern(self, idx) -> tuple:
        return self.cond_pattern[idx]

    def get_bool_judge(self, idx) -> dict:
        return self.boolsteps[idx]

    def _cond_key_builder(self) -> list:
        cond_keys = []
        for sub_rule in self._sub_rule_list:
            L_cond_key = only_cond_key(sub_rule["condition"]["L"].keys())
            R_cond_key = only_cond_key(sub_rule["condition"]["R"].keys())
            cond_keys.append((L_cond_key, R_cond_key))
        return cond_keys

    def _boolstep_builder(self) -> list:
        boolsteps = []
        for idx in range(len(self._sub_rule_list)):
            boolstep_dict = {}
            L_cond_key, R_cond_key = self.get_cond_key(idx)
            boolstep_dict["L"] = boolstep_finder(L_cond_key)
            boolstep_dict["R"] = boolstep_finder(R_cond_key)
            boolsteps.append(boolstep_dict)
        return boolsteps

    def _cond_pattern_builder(self) -> list:
        cond_pattern = []
        for sub_rule in self._sub_rule_list:
            cond_pattern.append(extractor(sub_rule))
        return cond_pattern


class BoolDeterminator(metaclass=ABCMeta):
    @abstractmethod
    def judge(self, cond_pattern: dict, char_cls: JamoHolder):
        return True


class TagBoolJudge(BoolDeterminator):
    def judge(self, cond_pattern: dict, char_cls: JamoHolder):
        return tag_checker(char_cls.tags, char_cls.tag_abb, cond_pattern["tag"])


class TagBoolJudge_firstone(BoolDeterminator):
    """ special case for TagBoolJudge
        Determine whether fullfill condition or not with a forehead tag within
        tags field in JamoHolder class.
    """
    def judge(self, cond_pattern: dict, char_cls: JamoHolder):
        first_tag, first_tag_abb = self._tag_extractor(char_cls)
        return tag_checker(first_tag, first_tag_abb, cond_pattern["tag"])

    def _tag_extractor(self, char_cls: JamoHolder):
        first_tag = char_cls.tags[0]
        first_tag_abb = first_tag[0]
        return [first_tag], first_tag_abb


class BeforeSpaceBoolJudge(BoolDeterminator):
    def judge(self, cond_pattern: dict, char_cls: JamoHolder):
        return char_cls.before_space is cond_pattern["before_space"]


class EosBoolJudge(BoolDeterminator):
    def judge(self, cond_pattern: dict, char_cls: JamoHolder):
        return char_cls.eos is cond_pattern["eos"]


def boolstep_finder(cond_key : dict):
    boolsteps = []
    if "before_space" in cond_key:
        boolsteps.append(BeforeSpaceBoolJudge())

    if "first_tag" in cond_key:
        boolsteps.append(TagBoolJudge_firstone())
    elif "tag" in cond_key:
        boolsteps.append(TagBoolJudge())

    if "eos" in cond_key:
        boolsteps.append(EosBoolJudge())

    return boolsteps


def only_cond_key(keys: list):
    chj_list = ["cho", "joong", "jong"]
    return list(set(keys) - set(chj_list))


def extractor(rule_dict: dict):
    L_c = rule_dict["condition"]["L"]
    R_c = rule_dict["condition"]["R"]
    L_p = rule_dict["process"]["L"]
    R_p = rule_dict["process"]["R"]
    return L_c, R_c, L_p, R_p


if __name__ == "__main__":
    from nctp.ncg2pk.rule_book import *
    add_nieun_cls = PronunciationRule("ㄴ첨가", rule_dict=add_nieun_dict)
    for sub_rule in add_nieun_cls.sub_rules:
        for rule in sub_rule.condition:
            import pdb; pdb.set_trace()