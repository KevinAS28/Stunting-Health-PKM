import os
from datetime import datetime as dt

def log(msg, end='\n'):
    with open('deploypy_log.txt', 'a+') as fd:
        fd.write(f'{dt.now()}\n{msg}{end}\n{"*"*15}')

os_commands = [
    'python3 manage.py makemigrations',
    'python3 manage.py migrate',
    
]

def unzip_static():
    if os.path.isfile('static.zip'):
        os.system('unzip static.zip')

for command in os_commands:
    try:
        os.system(command)
    except Exception as e:
        log(f'ERROR command: {command}: {str(e)}')
        exit(1)

exit(0)