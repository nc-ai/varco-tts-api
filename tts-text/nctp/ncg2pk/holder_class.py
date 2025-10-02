from abc import *
from collections import OrderedDict
from nctp.ncg2pk.utils import tag_to_def
from jamo import h2j, j2h, j2hcj


class CharHolder(metaclass=ABCMeta):
    def __init__(self, letter : chr, tag : chr):
        self._char = letter
        self.len = len(h2j(letter))
        self.decompose_tag(tag)

    def decompose_tag(self, tag):
        self.tag_abb, self.tags, self.def_tags = tag_to_def(tag)

    @abstractmethod
    def get_char(self):
        return 1


class SpecialHolder(CharHolder):
    def __init__(self, letter : chr, tag : chr):
        super(SpecialHolder, self).__init__(letter, tag)

    def get_char(self):
        return self._char


class JamoHolder(CharHolder):
    def __init__(self, letter : chr, tag : chr):
        super(JamoHolder, self).__init__(letter, tag)
        self.jamo_dict = OrderedDict({'cho': None, 'joong': None, 'jong': 0})
        self.chojoongjong()
        self.eos = False
        self.before_space = False
        self.end = False

    def chojoongjong(self):
        assert self.len > 1, "Uncomplete Character is coming. {}".format(self._char)

        if self.len > 1:
            for i, key in zip(range(self.len), self.jamo_dict.keys()):
                self.jamo_dict[key] = j2hcj(h2j(self._char))[i]

    def _jamo2han(self):
        return j2h(self.jamo_dict["cho"], self.jamo_dict["joong"], self.jamo_dict["jong"])

    def get_char(self):
        return self._jamo2han()
