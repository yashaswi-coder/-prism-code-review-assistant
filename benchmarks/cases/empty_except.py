def parse_number(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
