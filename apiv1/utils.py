import enum
import os, base64, re, json

from django.conf import settings
import requests
from sympy import integer_log

if settings.DEBUG:
    STATIC_DIR = settings.STATICFILES_DIRS[0]
else:
    STATIC_DIR = settings.STATIC_ROOT

def make_dir(path, no_end=True):
    if no_end:
        path = os.path.join(*(os.path.split(path)[:-1]))
        
    if os.path.isdir(path):
        return True

    funs = [os.makedirs, os.mkdir]
    success = 0
    for f in funs:
        try:
            f(path)
            success += 1
        except:
            pass
    if success>0:
        return True
    return False

def read_b64_file(file_path:str) -> str:
    full_path = os.path.join(STATIC_DIR, file_path)
    if os.path.isfile(full_path):
        with open(full_path, 'rb+') as f:
            b64_img = base64.b64encode(f.read()).decode('ascii')
            return b64_img
    else:
        return -1

def write_b64_file(file_path:str, b64_content) -> int:
    full_path = os.path.join(STATIC_DIR, file_path)
    make_dir(full_path, no_end=True)
    with open(full_path, 'wb+') as file_fd:
        if type(b64_content)==str:
            b64_content = b64_content.encode('ascii')
        return file_fd.write(base64.b64decode(b64_content))

def read_file(file_path:str) -> int:
    full_path = os.path.join(STATIC_DIR, file_path)
    print('PATH', full_path)
    if os.path.isfile(full_path):
        with open(full_path, 'rb+') as f:
            return f.read()
    else:
        return -1

def write_file(file_path:str, data:bytes) -> bytes:
    full_path = os.path.join(STATIC_DIR, file_path)
    make_dir(full_path, no_end=True)
    with open(full_path, 'wb+') as f:
        return f.write(data)
    

def valid_filename(filename, replacement=''):
    return re.sub(r'[^a-z|^A-Z|^0-9|^\.|\_|\-]', replacement, filename)

def multiple_replace(text:str, str_subs:dict, regex=True):
    if not regex:
        str_subs = {re.escape(k):v for k,v in str_subs.items()}

    pattern = re.compile("|".join(str_subs.keys()))

    def _multiple_replace(match):
        for k,v in str_subs.items():
            if re.match(k, match.group(0)):
                return v
        # raise ValueError(f'No match for: {match.group(0)}')
        return match.group(0)

    return pattern.sub(_multiple_replace, text)

def save_static(category, extension, title, content, num=0, encode_b64=False):
    file_name = valid_filename(f'{title}_{category}_{num}.{extension}')
    file_path = f"{category}/{file_name}"
    if encode_b64:
        content = base64.b64encode(content)
    write_b64_file(file_path, content)
    url = 'http://{}/static/'+file_path
    return file_name, file_path, url
    

def get_place_photo(photo_reference, key):
    PLACE_PHOTO_API = 'https://maps.googleapis.com/maps/api/place/photo'
    params = {
        'photo_reference': photo_reference,
        'key': key,
        'maxheight': 1000,
        'maxwidth': 1000
    }
    image_content = requests.get(PLACE_PHOTO_API, params=params).content
    fn, fp, url = save_static('img_maps', 'png', photo_reference, image_content, 0, encode_b64=True)
    return fn, fp, url



def get_place_detail_photos(place_id, key, host, max_photos=3):
    PLACE_DETAIL_API = 'https://maps.googleapis.com/maps/api/place/details/json'
    
    place_detail_parameters = {
        'key': key,
        'place_id': place_id
    }

    place = json.loads(requests.get(PLACE_DETAIL_API, params=place_detail_parameters).text)
    print(place)
    if 'result' in place:
        place = place['result']
        
        if not ('photos') in place:
            place['photos'] = []

        get_max_photos = lambda max_count, photos: min((max_count, len(photos)))
        
        photos = [get_place_photo(place['photos'][i]['photo_reference'], key)[2].format(host) for i in range(get_max_photos(max_photos, place['photos']))]
    else:
        photos = []
    return {'place_detail': place, 'photos_urls': photos}


if __name__=='__main__':
    print(valid_filename('r4u191rd  u58cb@$RF&^NU(!N&U(#!C.jp3eg'))
