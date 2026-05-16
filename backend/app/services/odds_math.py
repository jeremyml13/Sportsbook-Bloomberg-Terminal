def american_to_implied_probability(odds: int) -> float:
    if odds == 0:
        raise ValueError("American odds cannot be zero.")

    if odds > 0:
        return round(100 / (odds + 100), 4)

    return round(abs(odds) / (abs(odds) + 100), 4)


def calculate_line_movement(opening_line: float | None, current_line: float | None) -> float | None:
    if opening_line is None or current_line is None:
        return None

    return round(current_line - opening_line, 2)


def calculate_line_velocity(previous_line: float | None, current_line: float | None, hours_elapsed: float) -> float | None:
    if previous_line is None or current_line is None or hours_elapsed <= 0:
        return None

    return round((current_line - previous_line) / hours_elapsed, 3)


def calculate_book_disagreement(lines: list[float]) -> float:
    if not lines:
        return 0.0

    return round(max(lines) - min(lines), 2)


def calculate_volatility(lines: list[float]) -> float:
    if len(lines) < 2:
        return 0.0

    mean = sum(lines) / len(lines)
    variance = sum((line - mean) ** 2 for line in lines) / len(lines)
    return round(variance**0.5, 3)
