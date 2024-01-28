from cryptography.fernet import Fernet
from os.path import abspath, join


def _get_filepath(date: str):
    return abspath(join("records", date + ".txt"))


def if_encryption_enable(storage, date):
    if storage.encryption_enable and storage.crypto_key:
        encrypt_file(storage.crypto_key, _get_filepath(date))


def fernet(func):
    def create_fernet(key: bytes, *args, **kwargs):
        try:
            f = Fernet(key)
            return func(f, *args, **kwargs)
        except ValueError:
            raise Exception("Неверный формат ключа")

    return create_fernet


def generate_and_save_key(path):
    key = Fernet.generate_key()
    with open(path, "wb") as fp:
        fp.write(key)
    return key


def get_key(path):
    with open(path, "rb") as fp:
        key = fp.read()

    f = Fernet(key)
    return key


@fernet
def encrypt_file(f: Fernet, path: str):
    with open(path, "r") as fp:
        content = fp.read()
    with open(path, "wb") as fp:
        fp.write(f.encrypt(bytes(content, "UTF-8")))


@fernet
def decrypt_file(f: Fernet, path: str):
    with open(path, "rb") as fp:
        content = fp.read()

    return f.decrypt(content).decode()


# encrypt_file(get_key("crypto.key"), "2024-01-26.txt", False)
# print(decrypt_file(get_key("crypto.key"), "2024-01-26.txt"))
