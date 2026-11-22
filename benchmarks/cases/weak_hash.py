import hashlib


def checksum(value: bytes) -> str:
    return hashlib.md5(value).hexdigest()
