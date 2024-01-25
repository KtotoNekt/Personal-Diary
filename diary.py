import os
import zipfile

from odf import text, teletype
from odf.opendocument import load, OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties
from os.path import abspath, join, exists, splitext
from datetime import datetime


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
            content += line + "\n"

    return content


def _write_odt(filepath: str, content: str):
    doc = OpenDocumentText()

    for paragraph_content in content.split("\n"):
        paragraph = text.P(text=paragraph_content)

        new_style = Style(name="BaseStyle", family="paragraph")
        text_properties = TextProperties(fontfamily="Times New Roman", fontsize="18pt")
        paragraph_properties = ParagraphProperties(textindent="1cm")

        new_style.addElement(text_properties)
        new_style.addElement(paragraph_properties)

        doc.styles.addElement(new_style)

        paragraph.setAttribute("stylename", new_style)

        doc.text.addElement(paragraph)

    doc.save(filepath)


def get_date(value: datetime):
    return value.date().strftime('%Y-%m-%d')


def _get_filepath(date: str):
    return abspath(join("records", date + ".odt"))


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

    _write_odt(_get_filepath(date), content)


def read_record(date: str):
    return _read_odt(_get_filepath(date))


def create_record(content: str):
    filename = _get_filepath(get_date(datetime.now()))
    _write_odt(filename, content)


def edit_record(date: str, content: str):
    filename = _get_filepath(date)
    _write_odt(filename, content)


def delete_record(date: str):
    filepath = _get_filepath(date)
    os.remove(filepath)
