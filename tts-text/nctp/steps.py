from nctp.common import NormalizeStep
from nctp.common import Language
from typing import Dict, List, Union


class StepSupplyer:
    def __init__(self):
        self.lang_to_step: Dict[Language, Step] = {
            Language.korean: KoreanStep(),
            Language.korean_ipa: KoreanStep(),
            Language.english: EnglishStep(),
            Language.multi: MultiLangStep(),
            Language.english_arpabet: EnglishStep(),
            Language.english_ipa: EnglishStep(),
            Language.japanese_prosody: JapaneseStep(),
            Language.chinese: ChineseStep(),
            Language.taiwanese: TaiwaneseStep(),
        }

    def get_step(self, language: Language, step_name: str) -> List[NormalizeStep]:
        assert language in self.lang_to_step
        return self.lang_to_step[language].step(step_name)


class Step:
    def __init__(self):
        self.step_dict = {}

    def step(self, step: str):
        return self.step_dict[step]


class MultiLangStep(Step):
    DEFAULT_STEP: List[NormalizeStep] = [
            NormalizeStep.drop_incompletes,
            NormalizeStep.collapse_linebreak,
            NormalizeStep.remove_parentheses,
            NormalizeStep.collapse_special_characters,
            NormalizeStep.patterns,
            NormalizeStep.etc_dictionary,
            NormalizeStep.number,
            # NormalizeStep.english, # 임시로 제외.
            NormalizeStep.pronunciation,
            NormalizeStep.lowercase,
            NormalizeStep.expand_abbreviations,
            NormalizeStep.period,
            NormalizeStep.collapse_special_characters
    ]

    def __init__(self):
        self.step_dict = {
            "default": self.DEFAULT_STEP,
            "nctts": self.DEFAULT_STEP
        }

    def step(self, step: str):
        key = step if step in self.step_dict else 'default'
        return self.step_dict[key]


class KoreanStep(Step):
    DEFAULT_STEP: List[NormalizeStep] = [
            NormalizeStep.convert_ellipsis,
            NormalizeStep.handle_style_tag,
            NormalizeStep.handle_puncs_spaces,
            NormalizeStep.drop_incompletes,
            NormalizeStep.collapse_linebreak,
            NormalizeStep.remove_parentheses,
            NormalizeStep.collapse_special_characters,
            NormalizeStep.patterns,
            NormalizeStep.etc_dictionary,
            NormalizeStep.number,
            NormalizeStep.eng_dictionary,
            # NormalizeStep.english, # 임시로 제외.
            NormalizeStep.character,
            NormalizeStep.pronunciation,
            NormalizeStep.period,
            NormalizeStep.collapse_special_characters
    ]
    UNIVERSE_STEP: List[NormalizeStep] = [
            NormalizeStep.drop_incompletes,
            NormalizeStep.collapse_linebreak,
            NormalizeStep.collapse_special_characters_service,
            NormalizeStep.universe_dictionary,
            NormalizeStep.remove_parentheses,
            NormalizeStep.patterns,
            NormalizeStep.etc_dictionary,
            NormalizeStep.number,
            NormalizeStep.eng_dictionary,
            # NormalizeStep.english, # 임시로 제외.
            NormalizeStep.character,
            NormalizeStep.pronunciation,
            NormalizeStep.period,
            NormalizeStep.collapse_special_characters_service
    ]
    G2P_STEP: List[NormalizeStep] = [
            # NormalizeStep.pronunciation을 제외 -> pronounce step에서 발음규칙 처리
            NormalizeStep.drop_incompletes,
            NormalizeStep.collapse_linebreak,
            NormalizeStep.remove_parentheses,
            NormalizeStep.collapse_special_characters,
            NormalizeStep.patterns,
            NormalizeStep.etc_dictionary,
            NormalizeStep.number,
            NormalizeStep.eng_dictionary,
            NormalizeStep.character,
            NormalizeStep.convert_ellipsis,
            NormalizeStep.handle_style_tag,
            NormalizeStep.period,
            
    ]
    E2K_STEP: List[NormalizeStep] = [
            NormalizeStep.drop_incompletes,
            NormalizeStep.collapse_linebreak,
            NormalizeStep.universe_dictionary,
            NormalizeStep.remove_parentheses,
            # NormalizeStep.collapse_special_characters_service,
            # NormalizeStep.patterns,
            NormalizeStep.etc_dictionary,
            NormalizeStep.number,
            NormalizeStep.eng_dictionary,
            NormalizeStep.english,
            NormalizeStep.character,
            NormalizeStep.pronunciation,
            # NormalizeStep.period,
            NormalizeStep.collapse_special_characters_service,
            NormalizeStep.convert_ellipsis,
            NormalizeStep.handle_style_tag,
    ]


    def __init__(self):
        self.step_dict = {
            "default": self.DEFAULT_STEP,
            "nctts": self.DEFAULT_STEP,
            "universe": self.UNIVERSE_STEP,
            "g2p": self.G2P_STEP,
            "e2k": self.E2K_STEP
        }

    def step(self, step: str):
        key = step if step in self.step_dict else 'default'
        return self.step_dict[key]


class EnglishStep(Step):
    DEFAULT_STEP: List[NormalizeStep] = [
            NormalizeStep.convert_ellipsis,
            NormalizeStep.handle_style_tag,
            NormalizeStep.handle_puncs_spaces,
            NormalizeStep.collapse_linebreak,
            NormalizeStep.remove_parentheses,
            NormalizeStep.collapse_special_characters,
            # NormalizeStep.to_ascii,
            NormalizeStep.lowercase,
            NormalizeStep.expand_numbers,
            NormalizeStep.expand_abbreviations,
            NormalizeStep.collapse_special_characters,
    ]
    UNIVERSE_STEP: List[NormalizeStep] = [
            NormalizeStep.handle_puncs_spaces,
            NormalizeStep.collapse_linebreak,
            NormalizeStep.remove_parentheses,
            NormalizeStep.collapse_special_characters,
            # NormalizeStep.to_ascii,
            NormalizeStep.lowercase,
            NormalizeStep.expand_numbers,
            NormalizeStep.expand_abbreviations,
            NormalizeStep.collapse_special_characters
    ]

    def __init__(self):
        self.step_dict = {
            "default": self.DEFAULT_STEP,
            "nctts": self.DEFAULT_STEP,
            "universe": self.UNIVERSE_STEP,
            "g2p": self.DEFAULT_STEP
        }

    def step(self, step: str):
        key = step if step in self.step_dict else 'default'
        return self.step_dict[key]


class JapaneseStep(Step):
    DEFAULT_STEP: List[NormalizeStep] = [
        NormalizeStep.jpn_num_normalize,
        NormalizeStep.convert_ellipsis,
        NormalizeStep.handle_style_tag,
        NormalizeStep.handle_puncs_spaces,
        NormalizeStep.remove_bracket,
        NormalizeStep.convert_enumeration,
        NormalizeStep.remove_quotation,
        NormalizeStep.period,
    ]

    def __init__(self):
        self.step_dict = {
            "default": self.DEFAULT_STEP,
            "nctts": self.DEFAULT_STEP,
            "universe": self.DEFAULT_STEP,
            "g2p": self.DEFAULT_STEP
        }

    def step(self, step: str):
        key = step if step in self.step_dict else 'default'
        return self.step_dict[key]


class ChineseStep(Step):
    DEFAULT_STEP: List[NormalizeStep] = [
        NormalizeStep.handle_style_tag,
        NormalizeStep.handle_puncs_spaces,
        NormalizeStep.convert_ellipsis,
        NormalizeStep.remove_bracket,
        NormalizeStep.convert_enumeration,
        NormalizeStep.remove_quotation,
        NormalizeStep.chn_normalize,
        NormalizeStep.period,
    ]
    PROSODY_STEP: List[NormalizeStep] = [
        NormalizeStep.handle_puncs_spaces,
        NormalizeStep.handle_style_tag,
        NormalizeStep.convert_ellipsis,
        NormalizeStep.remove_bracket,
        NormalizeStep.convert_enumeration,
        NormalizeStep.remove_quotation,
        NormalizeStep.remove_prosody,
        NormalizeStep.chn_normalize,
        NormalizeStep.chn_prosody,
        NormalizeStep.period,
    ]
    BAKER_STEP: List[NormalizeStep] = [
        NormalizeStep.handle_style_tag,
        NormalizeStep.convert_ellipsis,
        NormalizeStep.remove_bracket,
        NormalizeStep.convert_enumeration,
        NormalizeStep.remove_quotation,
        NormalizeStep.chn_baker,
    ]


    def __init__(self):
        self.step_dict = {
            "default": self.DEFAULT_STEP,
            "default_prosody": self.PROSODY_STEP,
            "baker": self.BAKER_STEP,
            "nctts": self.DEFAULT_STEP,
            "universe": self.DEFAULT_STEP,
            "g2p": self.DEFAULT_STEP,
        }

    def step(self, step: str):
        key = step if step in self.step_dict else 'default'
        return self.step_dict[key]

class TaiwaneseStep(Step):
    DEFAULT_STEP: List[NormalizeStep] = [
        NormalizeStep.handle_style_tag,
        NormalizeStep.convert_ellipsis,
        NormalizeStep.handle_puncs_spaces,
        NormalizeStep.remove_bracket,
        NormalizeStep.convert_enumeration,
        NormalizeStep.remove_quotation,
        NormalizeStep.twn_normalize,
        NormalizeStep.period,
    ]
    PROSODY_STEP: List[NormalizeStep] = [
        NormalizeStep.handle_style_tag,
        NormalizeStep.convert_ellipsis,
        NormalizeStep.handle_puncs_spaces,
        NormalizeStep.remove_bracket,
        NormalizeStep.convert_enumeration,
        NormalizeStep.remove_quotation,
        NormalizeStep.remove_prosody,
        # NormalizeStep.twn_normalize, # bug: 종종 몇 개 한자를 없애버리는 현상 발견함.
        NormalizeStep.twn_normalize_new,
        NormalizeStep.twn_prosody,
        NormalizeStep.period,
    ]
    BAKER_STEP: List[NormalizeStep] = [
        NormalizeStep.handle_style_tag,
        NormalizeStep.convert_ellipsis,
        NormalizeStep.remove_bracket,
        NormalizeStep.convert_enumeration,
        NormalizeStep.remove_quotation,
        NormalizeStep.twn_baker,
    ]


    def __init__(self):
        self.step_dict = {
            "default": self.DEFAULT_STEP,
            "default_prosody": self.PROSODY_STEP,
            "baker": self.BAKER_STEP,
            "nctts": self.DEFAULT_STEP,
            "universe": self.DEFAULT_STEP,
            "g2p": self.DEFAULT_STEP,
        }

    def step(self, step: str):
        key = step if step in self.step_dict else 'default'
        return self.step_dict[key]

__SS = StepSupplyer()


def step_selector(language: Language, step: Union[None, str, List[NormalizeStep]]):
    if step is None:
        n_step = __SS.get_step(language, "default")
    elif isinstance(step, list):
        n_step = step
    elif isinstance(step, str):
        n_step = __SS.get_step(language, step)
    return n_step


if __name__ == "__main__":
    res = step_selector(Language.korean, 'default')
