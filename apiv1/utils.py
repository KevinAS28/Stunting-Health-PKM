import os, base64, re, json, random
from datetime import (datetime as dt, time as tm)
import time

from django.core.handlers.wsgi import WSGIRequest
from django.conf import settings
from django.db import models

import xlsxwriter
import requests


if settings.DEBUG:
    STATIC_DIR = settings.STATICFILES_DIRS[0]
else:
    STATIC_DIR = settings.STATIC_ROOT

def now_str(separator='_', attrs=['year', 'month', 'day', 'hour', 'minute', 'second']):
    all_attrs = [str(getattr(dt.now(), i)) for i in attrs]
    return separator.join(all_attrs)

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

def delete_file(file_path:str):
    full_path = os.path.join(STATIC_DIR, file_path)
    if not os.path.isfile(full_path):
        return -1
    os.remove(full_path)

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

def process_content_items(item_type_name, title, content, items, host):
    pattern = re.compile(r'({([a-z|A-Z|0-9|_|-]+)})')
    tags_urls = dict()
    content = content.replace('\\', '')
    for i, m in enumerate(pattern.finditer(content)):
        full_match, match = m.groups()
        match, m_type = match.split('_')
        extension = items[match]['extension']
        fn, fp, url = save_static(m_type, extension, title, items[match]['content'], i)
        url = url.format(host)
        tags_urls[full_match] = url

    article_parsed = multiple_replace(content, tags_urls, regex=False)
    article_parsed_path = os.path.join(item_type_name, valid_filename(f'{title}_{now_str()}.html', '_'))
    write_file(article_parsed_path, article_parsed.encode('utf-8'))
    return article_parsed, article_parsed_path, tags_urls

def process_article(request: WSGIRequest):
    data = json.loads(request.body)
    title = data['title']
    
    article_parsed, article_parsed_path, tags_urls = process_content_items('articles', title, data['article_content'], data['article_items'], request.get_host())

    # pattern = re.compile(r'({([a-z|A-Z|0-9|_|-]+)})')
    # tags_urls = dict()
    # data['article_content'] = data['article_content'].replace('\\', '')
    # for i, m in enumerate(pattern.finditer(data['article_content'])):
    #     full_match, match = m.groups()
    #     match, m_type = match.split('_')
    #     extension = data['article_items'][match]['extension']
    #     fn, fp, url = save_static(m_type, extension, title, data['article_items'][match]['content'], i)
    #     url = url.format(request.get_host())
    #     tags_urls[full_match] = url

    # article_parsed = multiple_replace(data['article_content'], tags_urls, regex=False)
    # article_parsed_path = os.path.join('articles', valid_filename(f'{title}_{data["date"]}.html', '_'))
    # write_file(article_parsed_path, article_parsed.encode('utf-8'))

    cover_name, cover_path, cover_url = save_static('img', data['cover']['extension'], f"{title}_cover", data['cover']['content'], 0)

    return article_parsed_path, title, cover_path, tags_urls, article_parsed

def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


def auto_set_obj_attrs(obj, attrs: dict, ignore_not_found=True):
    for key, value in attrs.items():
        if (not hasattr(obj, key)) and (not ignore_not_found):
            raise AttributeError(f'attribute {key} not found in selected object {str(obj)} and has been not ignored')
        setattr(obj, key, value)
    return obj

def queryset_to_excel(queryset_list):
    # Create a workbook and add a worksheet.
    file_path = f'/tmp/{time.time()}_{random.random()}.xlsx'
    workbook = xlsxwriter.Workbook(file_path)
    
    for queryset in queryset_list:
        if len(queryset)==0:
            continue
        sample_object = queryset[0]
        columns = [i for i in sample_object._meta.get_fields()]
        # print(columns)
        worksheet = workbook.add_worksheet(sample_object._meta.db_table) 

        for i, col in enumerate(columns):
            worksheet.write(0, i, col.verbose_name.lower())
        
        for i0, data_obj in enumerate(queryset):
            for i1, col in enumerate(columns):
                col = col.attname
                cell_data = getattr(data_obj, col)

                if isinstance(cell_data, models.Model):
                    cell_data = cell_data.id
                
                if not is_jsonable(cell_data):
                    cell_data = str(cell_data)
                    
                worksheet.write(i0+1, i1, cell_data)

        workbook.close()  

    
    # # Iterate over the data and write it out row by row.
    # for item, cost in (expenses):
    #     worksheet.write(row, col,     item)
    #     worksheet.write(row, col + 1, cost)
    #     row += 1

    # # Write a total using a formula.
    # worksheet.write(row, 0, 'Total')
    # worksheet.write(row, 1, '=SUM(B1:B4)')
    return file_path
    

if __name__=='__main__':
    print(valid_filename('r4u191rd  u58cb@$RF&^NU(!N&U(#!C.jp3eg'))
