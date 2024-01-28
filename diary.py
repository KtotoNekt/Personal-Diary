import os
import zipfile

from odf import text, teletype
from odf.opendocument import load
from os.path import abspath, join, exists, splitext
from datetime import datetime
from encryption import decrypt_file


def _read_odt(filepath: str):
    try:
        doc = load(filepath)
    except zipfile.BadZipfile:
        return print("Не удалось прочитать файл")

    content = ""
    for element in doc.getElementsByType(text.P):
        content += teletype.extractText(element) + "\n"

    return content


def _read_txt(filepath: str):
    with open(filepath, "r") as fp:
        content = ""
        for line in fp.readlines():
            content += line

    return content


def _write_txt(path: str, content):
    with open(path, "w") as fp:
        fp.write(content)


def get_date(value: datetime):
    return value.date().strftime('%Y-%m-%d')


def _get_filepath(date: str):
    return abspath(join("records", date + ".txt"))


def exists_record(date: str) -> bool:
    return exists(_get_filepath(date))


def import_record(date: str, filepath: str):
    _, extname = splitext(filepath)
    match extname:
        case ".odt":
            content = _read_odt(filepath)
        case ".txt":
            content = _read_txt(filepath)
        case _:
            content = ""

    _write_txt(_get_filepath(date), content)


def read_record(date: str, key=None):
    path = _get_filepath(date)
    if key:
        try:
            return decrypt_file(key, path)
        except:
            print("Файл не удалось расшифровать")

    return _read_txt(path)


def _modify_record(date: str, content: str):
    path = _get_filepath(date)
    _write_txt(path, content)


def create_record(content: str):
    _modify_record(get_date(datetime.now()), content)


def edit_record(date: str, content: str):
    _modify_record(date, content)


def delete_record(date: str):
    filepath = _get_filepath(date)
    os.remove(filepath)
