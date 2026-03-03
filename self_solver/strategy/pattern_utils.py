from collections import Counter

SOLVED_PATTERN = 242


def pattern_to_base3(pattern: int) -> str:
    digits = []
    for i in range(5):
        digits.append(str((pattern // (3 ** i)) % 3))
    return "".join(digits)


def calculate_pattern(guess: str, answer: str) -> int:
    pattern = [0] * 5
    answer_letter_counts = Counter(answer)

    for i in range(5):
        if guess[i] == answer[i]:
            pattern[i] = 2
            answer_letter_counts[guess[i]] -= 1

    for i in range(5):
        if pattern[i] == 0 and answer_letter_counts.get(guess[i], 0) > 0:
            pattern[i] = 1
            answer_letter_counts[guess[i]] -= 1

    return pattern[0] + pattern[1] * 3 + pattern[2] * 9 + pattern[3] * 27 + pattern[4] * 81


def calculate_pattern_base3(guess: str, answer: str) -> str:
    return pattern_to_base3(calculate_pattern(guess, answer))
