import re

from nctp.ssml.text_norm.converters.Date import (
    Date as EnNormalizeDate,
)  # for English
from nctp.ssml.text_norm.converters.Time import Time as EnNormalizeTime
from nctp.ssml.text_norm.converters.Ordinal import Ordinal as EnNormalizeOrdinal
from nctp.ssml.text_norm.converters.Cardinal import (
    Cardinal as EnNormalizeCardinal,
)

eng_date = EnNormalizeDate()
eng_time = EnNormalizeTime()
eng_ordinal = EnNormalizeOrdinal()
eng_cardinal = EnNormalizeCardinal()


digit_list = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]

phone_num_list = [
    "oh",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]


def normalize_date(text, format):
    """Detect date(yyyy[-/.]mm[-/.]dd) pattern in a sentence. Then, changing it to date pattern in english.

    Args:
        text ([string]): input text
        format(string)

    Returns:
        [str]: processed text
    """

    if format == "ymd":
        parts = re.split(r"[-/.]", text)
        result = eng_date.convert(parts[0] + "/" + parts[1] + "/" + parts[2])
    elif format == "mdy":
        parts = re.split(r"[-/.]", text)
        result = eng_date.convert(parts[0] + "/" + parts[1] + "/" + parts[2])
    elif format == "dmy":
        parts = re.split(r"[-/.]", text)
        result = (
            eng_date.get_month(parts[1])
            + " "
            + eng_ordinal.convert(parts[0])
            + " "
            + eng_date.convert_year(parts[2])
        )
    elif format == "ym":
        parts = re.split(r"[-/.]", text)
        result = eng_date.get_month(parts[1]) + " " + eng_date.convert_year(parts[0])
    elif format == "my":
        parts = re.split(r"[-/.]", text)
        result = eng_date.get_month(parts[0]) + " " + eng_date.convert_year(parts[1])
    elif format == "md":
        parts = re.split(r"[-/.]", text)
        result = eng_date.get_month(parts[0]) + " " + eng_ordinal.convert(parts[1])
    return result


def normalize_time(text, format):
    if format == "hms":
        parts = re.split(r":", text)
        hour = int(parts[0])
        if hour > 12:
            result = (
                eng_cardinal.convert(str(hour - 12))
                + " "
                + eng_cardinal.convert(parts[1])
                + " "
                + eng_cardinal.convert(parts[2])
            )
        else:
            result = (
                eng_cardinal.convert(parts[0])
                + " "
                + eng_cardinal.convert(parts[1])
                + " "
                + eng_cardinal.convert(parts[2])
            )
    elif format == "hm":
        parts = re.split(r":", text)
        hour = int(parts[0])
        if hour > 12:
            result = (
                eng_cardinal.convert(str(hour - 12))
                + " "
                + eng_cardinal.convert(parts[1])
            )
        else:
            result = (
                eng_cardinal.convert(parts[0]) + " " + eng_cardinal.convert(parts[1])
            )
    elif format == "hms12":
        parts = re.split(r":", text)
        hour = int(parts[0])
        if hour > 12:
            result = (
                eng_cardinal.convert(str(hour - 12))
                + " "
                + eng_cardinal.convert(parts[1])
                + " "
                + eng_cardinal.convert(parts[2])
                + " P M"
            )
        else:
            result = (
                eng_cardinal.convert(parts[0])
                + " "
                + eng_cardinal.convert(parts[1])
                + " "
                + eng_cardinal.convert(parts[2])
                + " A M"
            )
    elif format == "hm12":
        parts = re.split(r":", text)
        hour = int(parts[0])
        if hour > 12:
            result = (
                eng_cardinal.convert(str(hour - 12))
                + " "
                + eng_cardinal.convert(parts[1])
                + " P M"
            )
        else:
            result = (
                eng_cardinal.convert(parts[0])
                + " "
                + eng_cardinal.convert(parts[1])
                + " A M"
            )
    elif format == "hms24":
        parts = re.split(r":", text)
        result = (
            eng_cardinal.convert(parts[0])
            + " "
            + eng_cardinal.convert(parts[1])
            + " "
            + eng_cardinal.convert(parts[2])
        )
    elif format == "hm24":
        parts = re.split(r":", text)
        result = eng_cardinal.convert(parts[0]) + " " + eng_cardinal.convert(parts[1])
    return result


def process_sayas_en(text_n_attr):
    if text_n_attr[2][0] == "Attribute : ":
        if text_n_attr[2][1] == "interpret-as":
            value = text_n_attr[2][2]
            if value == "digits":
                if text_n_attr[1][0].isdigit():
                    digits_list = [
                        digit_list[int(digit)] for digit in text_n_attr[1][0]
                    ]
                    return [" ".join(digits_list)]
                else:
                    raise Exception("Error : a non-numeric character exists")
            elif value == "date":
                if (
                    text_n_attr[3][0] == "Attribute : "
                    and text_n_attr[3][1] == "format"
                ):
                    format = text_n_attr[3][2]
                    return [normalize_date(text_n_attr[1][0], format)]
                else:
                    raise Exception("Error in the second attribute")
            elif value == "time":
                if (
                    text_n_attr[3][0] == "Attribute : "
                    and text_n_attr[3][1] == "format"
                ):
                    format = text_n_attr[3][2]
                    return [normalize_time(text_n_attr[1][0], format)]
                else:
                    raise Exception("Error in the second attribute")
            elif value == "characters":
                # for c in text_n_attr[1][0]:
                translated_list = [letter.upper() for letter in text_n_attr[1][0]]
                return [" ".join(translated_list)]
            elif value == "digits":
                if text_n_attr[1][0].isdigit():
                    digits_list = [
                        digit_list[int(digit)] for digit in text_n_attr[1][0]
                    ]
                    return [" ".join(digits_list)]
                else:
                    raise Exception("Error : a non-numeric character exists")
            elif value == "telephone":
                onlydigit = [char for char in text_n_attr[1][0] if char.isdigit()]
                digits_list = [phone_num_list[int(letter)] for letter in onlydigit]
                if len(digits_list) >= 11:
                    return [
                        " ".join(digits_list[:3])
                        + " "
                        + " ".join(digits_list[3:7])
                        + " "
                        + " ".join(digits_list[7:])
                    ]
                elif len(digits_list) == 10:
                    if digits_list[0:2] == ["0", "2"]:
                        return [
                            " ".join(digits_list[:2])
                            + " "
                            + " ".join(digits_list[2:6])
                            + " "
                            + " ".join(digits_list[6:])
                        ]
                    else:
                        return [
                            " ".join(digits_list[:3])
                            + " "
                            + " ".join(digits_list[3:6])
                            + " "
                            + "".join(digits_list[6:])
                        ]
                elif len(digits_list) == 9:
                    return [
                        " ".join(digits_list[:2])
                        + " "
                        + " ".join(digits_list[2:5])
                        + " "
                        + " ".join(digits_list[5:])
                    ]
                elif len(digits_list) <= 8 and len(digits_list) >= 4:
                    return [
                        " ".join(digits_list[: len(digits_list) - 4])
                        + " "
                        + " ".join(digits_list[-4:])
                    ]
                else:
                    return [+" ".join(digits_list)]
        else:
            raise Exception("Error in the first attribute")
    else:
        raise Exception("Error in Attribute name")