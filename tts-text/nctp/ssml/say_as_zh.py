import re
from tn.chinese.normalizer import (
    Normalizer as WeTextNormalizer,
)  # for Chinese # pip install WeTextProcessing

WeText = WeTextNormalizer()


digit_list = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
phone_num_list = [
    "零",
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
    "七",
    "八",
    "九",
]  # 중국어 (대만어) 중국에서는 전화번호읽을때 "一" 대신 "幺"(yāo)로 읽지만 대만에서는 주로 "一"을 사용


def normalize_date(text, format):
    """Detect date(yyyy[-/.]mm[-/.]dd) pattern in a sentence. Then, changing it to date pattern in english.

    Args:
        text ([str]): input text

    Returns:
        [str]: processed text
    """

    if format == "ymd":
        date_pattern = re.compile(
            r"(\d{4}|\d{3}|\d{2}|\d)[-/.](0[1-9]|1[0-2]|[1-9])[-/.](0[1-9]|[12]\d|3[01]|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{WeText.normalize(x.group(1)+'年')}{WeText.normalize(str(int(x.group(2)))+'月')}{WeText.normalize(str(int(x.group(3)))+'号')}",
            text,
        )
    elif format == "ym":
        date_pattern = re.compile(r"(\d{4}|\d{3}|\d{2}|\d)[-/.](0[1-9]|1[0-2]|[1-9])")
        result = re.sub(
            date_pattern,
            lambda x: f"{WeText.normalize(x.group(1)+'年')}{WeText.normalize(str(int(x.group(2)))+'月')}",
            text,
        )
    elif format == "md":
        date_pattern = re.compile(
            r"(0[1-9]|1[0-2]|[1-9])[-/.](0[1-9]|[12]\d|3[01]|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{WeText.normalize(x.group(1)+'月'+ str(int(x.group(2)))+'号')}",
            text,
        )

    return result


def num2hour(text, format=24):
    hour = int(text)
    hourList = [
        "零点",
        "一点",
        "两点",
        "三点",
        "四点",
        "五点",
        "六点",
        "七点",
        "八点",
        "九点",
        "十点",
        "十一点",
        "十二点",
        "十三点",
        "十四点",
        "十五点",
        "十六点",
        "十七点",
        "十八点",
        "十九点",
        "二十点",
        "二十一点",
        "二十二点",
        "二十三点",
        "二十四点",
    ]

    if format == "hms12" or format == "hm12":
        if hour > 12:
            hour -= 12
            return "下午 " + hourList[hour]
        else:
            return "上午 " + hourList[hour]
    elif format == "hms" or format == "hm":
        if hour > 12:
            hour -= 12
            return hourList[hour]
        else:
            return hourList[hour]
    else:
        return hourList[hour]


def num2min(text):
    sec = int(text)
    return WeText.normalize(str(sec)) + "分"


def num2sec(text):
    sec = int(text)
    return WeText.normalize(str(sec)) + "秒"


def normalize_time(text, format):
    date_pattern = re.compile(
        r"(\d:[0]+\d|[1]\d|2[0123]|[1-9]):([0]+\d|[1-5]\d|[1-9]):([0]+\d|[1-5]\d|[1-9])"
    )

    if format == "hms":
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}{num2min(x.group(2))}{num2sec(x.group(3))}",
            text,
        )
    elif format == "hm":
        date_pattern = re.compile(
            r"([0]+\d|[1]\d|2[0123]|[1-9]):([0]+\d|[1-5]\d|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}{num2min(x.group(2))}",
            text,
        )
    elif format == "hms12":
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}{num2min(x.group(2))}{num2sec(x.group(3))}",
            text,
        )
    elif format == "hm12":
        date_pattern = re.compile(
            r"([0]+\d|[1]\d|2[0123]|[1-9]):([0]+\d|[1-5]\d|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}{num2min(x.group(2))}",
            text,
        )
    elif format == "hms24":
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1), format)}{num2min(x.group(2))}{num2sec(x.group(3))}",
            text,
        )
    elif format == "hm24":
        date_pattern = re.compile(
            r"([0]+\d|[1]\d|2[0123]|[1-9]):([0]+\d|[1-5]\d|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1), format)}{num2min(x.group(2))}",
            text,
        )
    elif format == "ms":
        date_pattern = re.compile(r"([0]+\d|[1-5]\d|[1-9]):([0]+\d|[1-5]\d|[1-9])")
        result = re.sub(
            date_pattern,
            lambda x: f"{num2min(x.group(2))}{num2sec(x.group(3))}",
            text,
        )
    return result


def process_sayas_zh(text_n_attr):
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
                    if format == "ymd":
                        return [normalize_date(text_n_attr[1][0], format)]
                    elif format == "ym":
                        return [normalize_date(text_n_attr[1][0], format)]
                    elif format == "md":
                        return [normalize_date(text_n_attr[1][0], format)]
                    else:
                        raise Exception("Not supported date format")
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
            elif value == "telephone":
                onlydigit = [char for char in text_n_attr[1][0] if char.isdigit()]
                digits_list = [phone_num_list[int(letter)] for letter in onlydigit]
                if len(digits_list) >= 11:
                    return [
                        "".join(digits_list[:3])
                        + " "
                        + "".join(digits_list[3:7])
                        + " "
                        + "".join(digits_list[7:])
                    ]
                elif len(digits_list) == 10:
                    if digits_list[0:2] == ["0", "2"]:
                        return [
                            "".join(digits_list[:2])
                            + " "
                            + "".join(digits_list[2:6])
                            + " "
                            + "".join(digits_list[6:])
                        ]
                    else:
                        return [
                            "".join(digits_list[:3])
                            + " "
                            + "".join(digits_list[3:6])
                            + " "
                            + "".join(digits_list[6:])
                        ]
                elif len(digits_list) == 9:
                    return [
                        "".join(digits_list[:2])
                        + " "
                        + "".join(digits_list[2:5])
                        + " "
                        + "".join(digits_list[5:])
                    ]
                elif len(digits_list) <= 8 and len(digits_list) >= 4:
                    return [
                        "".join(digits_list[: len(digits_list) - 4])
                        + " "
                        + "".join(digits_list[-4:])
                    ]
                else:
                    return [+"".join(digits_list)]
        else:
            raise Exception("Error in the first attribute")
    else:
        raise Exception("Error in Attribute name")