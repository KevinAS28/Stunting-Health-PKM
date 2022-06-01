import os, base64, re

from django.conf import settings

def read_base64(file_path:str) -> str:
    full_path = os.path.join(settings.STATIC_ROOT, file_path)
    if os.path.isfile(full_path):
        with open(full_path, 'rb+') as f:
            b64_img = base64.b64encode(f.read()).decode('ascii')
            return b64_img
    else:
        return f'Not Found: {full_path}'

def write_base64(file_path:str, b64_str:str) -> int:
    with open(os.path.join(settings.STATIC_ROOT, file_path), 'wb+') as file_fd:
        return file_fd.write(base64.b64decode(b64_str.encode('ascii')))

def valid_filename(filename):
    return re.sub(r'[^a-z|^A-Z|^0-9|^\.]', '', filename)


print(valid_filename('r4u191rd  u58cb@$RF&^NU(!N&U(#!C.jp3eg'))
