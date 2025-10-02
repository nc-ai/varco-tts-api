import re
import pyopenjtalk as jtalk  # for Japanese


digit_list = [
    "ゼロ",
    "イチ",
    "ニ",
    "サン",
    "ヨン",
    "ゴ",
    "ロク",
    "ナナ",
    "ハチ",
    "キュウ",
    "ジュウ",
]

phone_num_list = [
    "ゼロ",
    "イチ",
    "ニ",
    "サン",
    "ヨン",
    "ゴ",
    "ロク",
    "ナナ",
    "ハチ",
    "キュウ",
    "ジュウ",
]

eng_to_jap = {
    "A": "エー",
    "B": "ビー",
    "C": "シー",
    "D": "ディー",
    "E": "イー",
    "F": "エフ",
    "G": "ジー",
    "H": "エイチ",
    "I": "アイ",
    "J": "ジェー",
    "K": "ケー",
    "L": "エル",
    "M": "エム",
    "N": "エヌ",
    "O": "オー",
    "P": "ピー",
    "Q": "キュー",
    "R": "アール",
    "S": "エス",
    "T": "ティー",
    "U": "ユー",
    "V": "ヴィー",
    "W": "ダブリュー",
    "X": "エックス",
    "Y": "ワイ",
    "Z": "ゼット",
    " ": "",
}


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
            lambda x: f"{jtalk.g2p(x.group(1)+'年',kana=True)}{jtalk.g2p(x.group(2)+'月',kana=True)}{jtalk.g2p(x.group(3)+'日',kana=True)}",
            text,
        )
    elif format == "ym":
        date_pattern = re.compile(r"(\d{4}|\d{3}|\d{2}|\d)[-/.](0[1-9]|1[0-2]|[1-9])")
        result = re.sub(
            date_pattern,
            lambda x: f"{jtalk.g2p(x.group(1)+'年',kana=True)}{jtalk.g2p(x.group(2)+'月',kana=True)}",
            text,
        )
    elif format == "md":
        date_pattern = re.compile(
            r"(0[1-9]|1[0-2]|[1-9])[-/.](0[1-9]|[12]\d|3[01]|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{jtalk.g2p(x.group(1)+'月',kana=True)}{jtalk.g2p(x.group(2)+'日',kana=True)}",
            text,
        )
    return result


def num2hour(text, format=24):
    hour = int(text)
    hourList = [
        "レイジ",  # 0時
        "イチジ",  # 1時
        "ニジ",  # 2시
        "サンジ",  # 3시
        "ヨジ",  # 4시
        "ゴジ",  # 5시
        "ロクジ",  # 6시
        "シチジ",  # 7시
        "ハチジ",  # 8시
        "クジ ",  # 9시
        "ジュウジ",  # 10시
        "ジュウイチジ",  # 11시
        "ジュウニジ",  # 12시
        "ジュウサンジ",  # 13시
        "ジュウヨジ",  # 14시
        "ジュウゴジ",  # 15시
        "ジュウロクジ",  # 16시
        "ジュウシチジ",  # 17시
        "ジュウハチジ",  # 18시
        "ジュウクジ",  # 19시
        "ニジュウジ",  # 20시
        "ニジュウイチジ",  # 21시
        "ニジュウニジ",  # 22시
        "ニジュウサンジ",  # 23시
        "ニジュウヨジ",  # 24시
    ]

    if format == "hms12" or format == "hm12":
        if hour > 12:
            hour -= 12
            return "午後 " + hourList[hour]
        else:
            return "午前 " + hourList[hour]
    elif format == "hms" or format == "hm":
        if hour > 12:
            hour -= 12
            return hourList[hour]
        else:
            return hourList[hour]
    else:
        return hourList[hour]


def num2min(text):
    min = int(text)
    return jtalk.g2p(str(min) + "分", kana=True)


def num2sec(text):
    sec = int(text)
    return jtalk.g2p(str(sec) + "秒", kana=True)


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


def process_sayas_jp(text_n_attr):
    if text_n_attr[2][0] == "Attribute : ":
        if text_n_attr[2][1] == "interpret-as":
            value = text_n_attr[2][2]
            if value == "date":
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
                translated_list = [
                    eng_to_jap[letter.upper()] for letter in text_n_attr[1][0]
                ]
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