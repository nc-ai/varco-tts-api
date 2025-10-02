from nctp.ncg2pk.utils import mapping, tag_checker, chj_finder
from nctp.ncg2pk.holder_class import JamoHolder
from nctp.ncg2pk.rule_class import PronunciationRule
from nctp.ncg2pk.utils import mapping

from abc import *


class RuleApplyer(metaclass=ABCMeta):
    def __init__(self, rule_cls: PronunciationRule):
        self.rule_cls = rule_cls

    def apply(self, head, tail, verbose):
        for sub_rule in self.rule_cls.sub_rules:
            self._apply(sub_rule, head, tail, verbose)

    def _apply(self, sub_rule, head, tail, verbose):
        for idx in range(len(sub_rule)):
            rule_id = sub_rule.rule_id
            L_c, R_c, L_p, R_p = sub_rule.get_cond_pattern(idx)
            matched_indices = self._matching_chars(L_c, R_c, head, tail)
            if matched_indices: # 조건에 맞게 해당 자,모음을 지닐 경우
                bool_judges = sub_rule.get_bool_judge(idx)
                if len(bool_judges["L"]) != 0 or len(bool_judges["R"]) != 0:
                    L_bools, R_bools = self._bool_processor(bool_judges, L_c, R_c, head, tail)
                else:
                    L_bools, R_bools = [], []

                if self._determinator(matched_indices, L_bools, R_bools, rule_id):
                    self._mapping(head, tail, L_p, R_p, matched_indices, rule_id, verbose)
            else: # 조건에는 맞지만 해당 자,모음을 지니지 않으면
                continue

    def _matching_chars(self, L_c, R_c, head, tail):
        matched_indices = {
            "L_cho" : self._matching("cho", L_c, head),
            "L_joong" : self._matching("joong", L_c, head),
            "L_jong" : self._matching("jong", L_c, head)
        }
        if tail is not None:
            matched_indices.update({
                "R_cho"  : self._matching("cho", R_c, tail),
                "R_joong": self._matching("joong", R_c, tail),
                "R_jong" : self._matching("jong", R_c, tail)
            })
        if -1 in matched_indices.values():
            return False
        else:
            return matched_indices

    def _matching(self, keyword: str, cond_pattern: dict, char_cls: JamoHolder) -> int:
        if keyword in cond_pattern.keys():
            idx = chj_finder(cond_pattern[keyword], char_cls.jamo_dict[keyword])               
        else:
            idx = 0
        return idx

    def _bool_processor(self, bool_judges: dict, L_c, R_c, head, tail) -> tuple:
        L_bools = [bool_judge.judge(L_c, head) for bool_judge in bool_judges["L"]]
        if tail is not None:
            R_bools = [bool_judge.judge(R_c, tail) for bool_judge in bool_judges["R"]]
        else:
            R_bools = []
        return L_bools, R_bools

    def _determinator(self, matched_indices: dict, L_bools, R_bools, rule_id=None):
        matching_bools = L_bools + R_bools
        if False in matching_bools:
            return False
        else:
            return True

    @abstractmethod
    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        return True

    @staticmethod
    def _get_idx(matched_indices):
        return (matching_idx for matching_idx in matched_indices)


class AddnieunApplyer(RuleApplyer):
    def __init__(self, rule_cls: PronunciationRule):
        super(AddnieunApplyer, self).__init__(rule_cls)

    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(tail, "cho", R_p["cho"][matched_indices["R_cho"]], rule_id, verbose)


class YooeumnieunApplyer(RuleApplyer):
    def __init__(self, rule_cls: PronunciationRule):
        super(YooeumnieunApplyer, self).__init__(rule_cls)

    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)
        mapping(tail, "cho", R_p["cho"][matched_indices["L_jong"]], rule_id, verbose) # L_idx 맞음


class DoinsoriApplyer(RuleApplyer):
    def __init__(self, rule_cls: PronunciationRule):
        super(DoinsoriApplyer, self).__init__(rule_cls)

    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(tail, "cho", R_p["cho"][matched_indices["R_cho"]], rule_id, verbose)


class JongseongApplyer(RuleApplyer):
    def __init__(self, rule_cls: PronunciationRule):
        self._map_dict = {
            "rule_11"           : self._map_11,
            "rule_17"           : self._map_11,
            "rule_10_a"         : self._map_10_a,
            "rule_9_10_11"      : self._map_91011,
            "rule_17_2"         : self._map_17_2,
            "rule_14"           : self._map_141315,
            "rule_13"           : self._map_141315,
            "rule_15"           : self._map_141315,
            "rule_14_13_12_adv" : self._map_141315,
        }
        super(JongseongApplyer, self).__init__(rule_cls)

    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        variables = (head, tail, L_p, R_p, matched_indices, rule_id, verbose)
        self._map_dict[rule_id](*variables)

    def _map_11(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)
        mapping(tail, "cho", R_p["cho"][matched_indices["R_cho"]], rule_id, verbose)

    def _map_17(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)
        mapping(tail, "cho", R_p["cho"][matched_indices["R_cho"]], rule_id, verbose)
        mapping(tail, "joong", R_p["joong"][matched_indices["R_joong"]], rule_id, verbose)

    def _map_10_a(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)

    def _map_91011(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)

    def _map_17_2(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)
        mapping(tail, "cho", R_p["cho"][matched_indices["L_jong"]], rule_id, verbose) # L_idx_j 맞음
        mapping(tail, "joong", R_p["joong"][matched_indices["L_jong"]], rule_id, verbose) # L_idx_j 맞음

    def _map_141315(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)
        mapping(tail, "cho", R_p["cho"][matched_indices["L_jong"]], rule_id, verbose)


class HieutApplyer(RuleApplyer):
    def __init__(self, rule_cls: PronunciationRule):
        self._map_dict = {
            "rule_12_1"         : self._map_12_1,
            "rule_12_2"         : self._map_12_2,
        }
        super(HieutApplyer, self).__init__(rule_cls)

    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        variables = (head, tail, L_p, R_p, matched_indices, rule_id, verbose)
        self._map_dict[rule_id](*variables)

    def _map_12_1(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)
        mapping(tail, "cho", R_p["cho"][matched_indices["L_jong"]], rule_id, verbose)

    def _map_12_2(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)
        mapping(tail, "cho", R_p["cho"][matched_indices["R_cho"]], rule_id, verbose)


class RieulnasalApplyer(RuleApplyer):
    def __init__(self, rule_cls: PronunciationRule):
        super(RieulnasalApplyer, self).__init__(rule_cls)

    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(tail, "cho", R_p["cho"][matched_indices["R_cho"]], rule_id, verbose)


class JongseongnasalApplyer(RuleApplyer):
    def __init__(self, rule_cls: PronunciationRule):
        super(JongseongnasalApplyer, self).__init__(rule_cls)

    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["R_cho"]], rule_id, verbose) # R_idx_c 맞음
        mapping(tail, "cho", R_p["cho"][matched_indices["R_cho"]], rule_id, verbose)


class JongseongValApplyer(RuleApplyer):
    def __init__(self, rule_cls: PronunciationRule):
        super(JongseongValApplyer, self).__init__(rule_cls)

    def _mapping(self, head, tail, L_p, R_p, matched_indices, rule_id, verbose):
        mapping(head, "jong", L_p["jong"][matched_indices["L_jong"]], rule_id, verbose)