import time
import argparse
from nctp.ncg2pk.pronounce import nc_g2pk
from nctp.text_processor import TextProcessor


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", default=False, type=int, help="print out detailed informantion about processing")
    parser.add_argument("-c", "--compare", default=False, type=int, help="Compare with open")
    args = parser.parse_args()
    return args


def get_input():
    def_input_text = "실행 로그에서 업그레이드, 신규 설치 및 제거, 업그레이드 대상 패키지 등의 정보를 출력하고 있습니다. 위 실행 예제는 미사용 패키지가 없는 상태를 보입니다."
    print("Please Insert the sentence, otherwise a default sentence will come out.")
    print("I want to play with a below sentence...")
    input_text = input()
    if len(input_text) == 0:
        input_text = def_input_text
    return input_text


def sent2phoneme(text_processor, text, verbose: bool):
    normalized = text_processor.normalize(text)
    cleaned = text_processor.clean(normalized)
    g2p_result = text_processor.pronounce(cleaned)

    return g2p_result


def tp_s2p(tp, input_text, verbose, print_time=True):
    start = time.time()
    output_text = sent2phoneme(tp, input_text, verbose=verbose)
    end = time.time()
    timer = end - start
    if print_time:
        print(f"nctp output : {output_text}")
        print("nctp process(new) time: {}".format(timer))
    else:
        return timer


def ncg2p_new(tp, input_text, verbose, print_time=True):
    # 구조화 후
    start = time.time()
    output_text = nc_g2pk(input_text, verbose=verbose)
    end = time.time()
    timer = end - start
    if print_time:
        print(f"nctp output : {output_text}")
        print("nctp process(new) time: {}".format(timer))
    else:
        return timer


def g2pk_full(g2p, input_text, verbose, print_time=True):
    start = time.time()
    output_text = g2p(input_text, verbose=verbose)
    end = time.time()
    timer = end - start
    if print_time:
        print(f"g2pk output : {output_text}")
        print("g2pk process time: {}".format(timer))
    else:
        return timer


def g2pk_phon(g2pk_copied, input_text, verbose, print_time=True):
    start = time.time()
    output_text = g2pk_copied(input_text, verbose=verbose)
    end = time.time()
    timer = end - start
    if print_time:
        print(f"g2pk_pronounce only output : {output_text}")
        print("g2pk_pronounce process(pronounce) time: {}".format(timer))
    else:
        return timer


if __name__ == "__main__":
    args = parse()
    while(True):
        input_text = get_input()

        verbose = args.verbose
        reference_g2pk = args.compare
        print(verbose, reference_g2pk)
        print(f"input text : {input_text}")

        if reference_g2pk:
            from g2pk import G2p
            from nctp.ncg2pk.g2pk_copied import G2p_copied

            g2p = G2p()
            g2pk_copied = G2p_copied()
            g2pk_full(g2p, input_text, verbose)
            g2pk_phon(g2pk_copied, input_text, verbose)

        tp = TextProcessor("korean", "g2p")
        sent2phoneme(tp, input_text, verbose)
        tp_s2p(tp, input_text, verbose)
        ncg2p_new(tp, input_text, verbose)