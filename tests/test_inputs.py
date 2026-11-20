import pytest

from prism.inputs import MAX_BYTES, InputError, decode_upload, sanitize_file_name, validate_source


def test_empty_and_whitespace_rejected():
    for text in ("", "   \n\t"):
        with pytest.raises(InputError):
            validate_source(text)


def test_nul_byte_rejected():
    with pytest.raises(InputError):
        validate_source("x = 1\x00")


def test_oversize_rejected():
    with pytest.raises(InputError):
        validate_source("x" * (MAX_BYTES + 1))


def test_non_py_extension_rejected():
    with pytest.raises(InputError):
        sanitize_file_name("notes.txt")


def test_file_name_is_reduced_to_safe_basename():
    assert sanitize_file_name("../../etc/evil dir/app.py") == "app.py"
    assert sanitize_file_name(None) == "pasted_code.py"


def test_upload_must_be_utf8():
    with pytest.raises(InputError):
        decode_upload(b"\xff\xfe\x00bad", "x.py")


def test_valid_upload_roundtrip():
    text, name = decode_upload(b"x = 1\n", "ok.py")
    assert (text, name) == ("x = 1\n", "ok.py")
