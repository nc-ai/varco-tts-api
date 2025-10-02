from collections import OrderedDict
from nctp.ncg2pk.rule_class import PronunciationRule
import nctp.ncg2pk.applyer_class as applyer_class
import nctp.ncg2pk.rule_book as rule_book

RULE_INFORM = OrderedDict({
    "ㄴ첨가" : {
        "rule_dict" : rule_book.add_nieun_dict,
        "applyer" : applyer_class.AddnieunApplyer
    },
    "ㄴ의 유음화" : {
        "rule_dict" : rule_book.yooeum_nieun_dict,
        "applyer"   : applyer_class.YooeumnieunApplyer
    },
    "초성의 된소리화" : {
        "rule_dict" : rule_book.doinsori_dict,
        "applyer"   : applyer_class.DoinsoriApplyer
    },
    "종성의 발음" : {
        "rule_dict" : rule_book.jongseong_dict,
        "applyer"   : applyer_class.JongseongApplyer
    },
    "ㅎ의 발음" : {
        "rule_dict" : rule_book.hieut_dict,
        "applyer"   : applyer_class.HieutApplyer
    },
    "ㄹ 의 비음화" : {
        "rule_dict"  : rule_book.rieul_nasalization_dict,
        "applyer"    : applyer_class.RieulnasalApplyer
    },
    "종성의 비음화" : {
        "rule_dict" : rule_book.jongseong_nasalization_dict,
        "applyer"   : applyer_class.JongseongnasalApplyer
    }
})
VALRULE_INFORM = OrderedDict({
    "종성 검증" : {
        "rule_dict" : rule_book.jongseong_validate_dict,
        "applyer"   : applyer_class.JongseongValApplyer
    }
})


class SingleTone(object):
    __instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_.__instance, class_): # for singleton
            class_.__instance = object.__new__(class_, *args, **kwargs)
        return class_.__instance


class RuleManager(SingleTone):
    def __init__(self):
        self.apply_step = self._def_appsteps(RULE_INFORM)
        self.val_step   = self._def_appsteps(VALRULE_INFORM)

    def _def_appsteps(self, rule_inform_dict):
        return [self._make_applyer(rule_name, rule_inform_dict) for rule_name in rule_inform_dict.keys()]        

    def _make_applyer(self, rule_name, rule_inform_dict):
        return rule_inform_dict[rule_name]["applyer"](self._load_rule(rule_name, rule_inform_dict))

    def _load_rule(self, rule_name, rule_inform_dict):
        return PronunciationRule(rule_name, rule_inform_dict[rule_name]["rule_dict"])

    def apply(self, sent_chain, jamo_indices, verbose):
        self._rule_apply(sent_chain, jamo_indices, verbose)
        self._val_apply(sent_chain, jamo_indices, verbose)

    def _rule_apply(self, sent_chain, jamo_indices, verbose):
        for head_idx, tail_idx in zip(jamo_indices[:-1], jamo_indices[1:]):
            if sent_chain[head_idx].end:
                continue
            self._apply(self.apply_step, sent_chain[head_idx], sent_chain[tail_idx], verbose)

    def _val_apply(self, sent_chain, jamo_indices, verbose):
        for idx in jamo_indices:
            self._apply(self.val_step, sent_chain[idx], None, verbose)

    def _apply(self, steps, head, tail, verbose):
        for step in steps:
            step.apply(head, tail, verbose)
