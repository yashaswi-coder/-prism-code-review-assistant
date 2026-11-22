def parse_integer(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
