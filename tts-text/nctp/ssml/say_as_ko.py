from nctp.korean import num2kor  # for Korean
import re

digit_list = ["영", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]

phone_num_list = ["공", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]

month_list = [
    "일월",
    "이월",
    "삼월",
    "사월",
    "오월",
    "유월",
    "칠월",
    "팔월",
    "구월",
    "시월",
    "십일월",
    "십이월",
]

eng_to_kor = {
    "A": "에이",
    "B": "비",
    "C": "씨",
    "D": "디",
    "E": "이",
    "F": "에프",
    "G": "쥐",
    "H": "에이치",
    "I": "아이",
    "J": "제이",
    "K": "케이",
    "L": "엘",
    "M": "엠",
    "N": "엔",
    "O": "오",
    "P": "피",
    "Q": "큐",
    "R": "알",
    "S": "에스",
    "T": "티",
    "U": "유",
    "V": "브이",
    "W": "더블유",
    "X": "엑스",
    "Y": "와이",
    "Z": "지",
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
        # -/.로 구분된 연(4자리~1자리), 월(01, 11, 9 등), 일(01, 13, 31 등)
        date_pattern = re.compile(
            r"(\d{4}|\d{3}|\d{2}|\d)[-/.](0[1-9]|1[0-2]|[1-9])[-/.](0[1-9]|[12]\d|3[01]|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{num2kor(x.group(1))}년 {month_list[int(x.group(2))-1]} {num2kor(x.group(3))}일",
            text,
        )
    elif format == "ym":
        date_pattern = re.compile(r"(\d{4}|\d{3}|\d{2}|\d)[-/.](0[1-9]|1[0-2]|[1-9])")
        result = re.sub(
            date_pattern,
            lambda x: f"{num2kor(x.group(1))}년 {month_list[int(x.group(2))-1]}",
            text,
        )
    elif format == "md":
        date_pattern = re.compile(
            r"(0[1-9]|1[0-2]|[1-9])[-/.](0[1-9]|[12]\d|3[01]|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{month_list[int(x.group(2))-1]} {num2kor(x.group(2))}일",
            text,
        )

    return result


def num2hour(text, format=24):
    hour = int(text)
    hourList = [
        "영",
        "한",
        "두",
        "세",
        "네",
        "다섯",
        "여섯",
        "일곱",
        "여덟",
        "아홉",
        "열",
        "열한",
        "열두",
        "십삼",
        "십사",
        "십오",
        "십육",
        "십칠",
        "십팔",
        "십구",
        "이십",
        "이십일",
        "이십이",
        "이십삼",
        "이십사",
    ]

    if format == "hms12" or format == "hm12":
        if hour > 12:
            hour -= 12
            return "오후 " + hourList[hour]
        else:
            return "오전 " + hourList[hour]
    elif format == "hms" or format == "hm":
        if hour > 12:
            hour -= 12
            return hourList[hour]
        else:
            return hourList[hour]
    else:
        return hourList[hour]


def normalize_time(text, format):
    # 시간:분:초 형식 정규식
    # 시간: 01, 11, 23, 9
    # 분: 07, 9, 29
    # 초: 분이랑 같음
    date_pattern = re.compile(
        r"(\d:[0]+\d|[1]\d|2[0123]|[1-9]):([0]+\d|[1-5]\d|[1-9]):([0]+\d|[1-5]\d|[1-9])"
    )

    if format == "hms":
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}시 {num2kor(x.group(2))}분 {num2kor(x.group(3))}초",
            text,
        )
    elif format == "hm":
        date_pattern = re.compile(
            r"([0]+\d|[1]\d|2[0123]|[1-9]):([0]+\d|[1-5]\d|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}시 {num2kor(x.group(2))}분",
            text,
        )
    elif format == "hms12":
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}시 {num2kor(x.group(2))}분 {num2kor(x.group(3))}초",
            text,
        )
    elif format == "hm12":
        date_pattern = re.compile(
            r"([0]+\d|[1]\d|2[0123]|[1-9]):([0]+\d|[1-5]\d|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}시 {num2kor(x.group(2))}분",
            text,
        )
    elif format == "hms24":
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}시 {num2kor(x.group(2))}분 {num2kor(x.group(3))}초",
            text,
        )
    elif format == "hm24":
        date_pattern = re.compile(
            r"([0]+\d|[1]\d|2[0123]|[1-9]):([0]+\d|[1-5]\d|[1-9])"
        )
        result = re.sub(
            date_pattern,
            lambda x: f"{num2hour(x.group(1),format)}시 {num2kor(x.group(2))}분",
            text,
        )
    elif format == "ms":
        date_pattern = re.compile(r"([0]+\d|[1-5]\d|[1-9]):([0]+\d|[1-5]\d|[1-9])")
        result = re.sub(
            date_pattern,
            lambda x: f"{num2kor(x.group(2))}분 {num2kor(x.group(3))}초",
            text,
        )
    return result


def process_sayas_ko(text_n_attr):
    if text_n_attr[2][0] == "Attribute : ":
        if text_n_attr[2][1] == "interpret-as":
            value = text_n_attr[2][2]
            if value == "number":
            # say-as의 interpret-as 값이 number인 경우 처리 하는 부분
            # 우리말 숫자/한자어 숫자인 경우 처리
                if (
                    text_n_attr[3][0] == "Attribute : "
                    and text_n_attr[3][1] == "format"
                ):
                    format = text_n_attr[3][2]
                    if format == "korean":
                        return [num2kor(text_n_attr[1][0], True)]
                    elif format == "chinese":
                        return [num2kor(text_n_attr[1][0], False)]
                else:
                    raise Exception("Error in the second attribute")
            elif value == "date":
            # say-as의 interpret-as 값이 date인 경우 처리 하는 부분
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
            # say-as의 interpret-as 값이 time인 경우 처리 하는 부분
                if (
                    text_n_attr[3][0] == "Attribute : "
                    and text_n_attr[3][1] == "format"
                ):
                    format = text_n_attr[3][2]
                    return [normalize_time(text_n_attr[1][0], format)]
                else:
                    raise Exception("Error in the second attribute")
            elif value == "characters":
            # say-as의 interpret-as 값이 characters인 경우 처리 하는 부분
                # for c in text_n_attr[1][0]:
                translated_list = [
                    eng_to_kor[letter.upper()] for letter in text_n_attr[1][0]
                ]
                return [" ".join(translated_list)]
            elif value == "digits":
            # say-as의 interpret-as 값이 digits인 경우 처리 하는 부분
                if text_n_attr[1][0].isdigit():
                    digits_list = [
                        digit_list[int(digit)] for digit in text_n_attr[1][0]
                    ]
                    return [" ".join(digits_list)]
                else:
                    raise Exception("Error : a non-numeric character exists")
            elif value == "telephone":
            # say-as의 interpret-as 값이 telephone인 경우 처리 하는 부분
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
                    # 지역번호가 02인 경우 예외처리
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