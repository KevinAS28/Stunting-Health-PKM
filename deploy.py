import os
from datetime import datetime as dt

def log(msg, end='\n'):
    with open('deploypy_log.txt', 'a+') as fd:
        fd.write(f'{dt.now()}\n{msg}{end}\n{"*"*15}')
    print(msg+end)

os_commands = [
    'python3 manage.py makemigrations',
    'python3 manage.py migrate',
    
]

def unzip_static():
    if os.path.isfile('static.zip'):
        os.system('unzip -o static.zip')


if __name__=='__main__':
    
    for command in os_commands:
        try:
            log(f'running command: {command}')
            os.system(command)
        except Exception as e:
            log(f'ERROR command: {command}: {str(e)}')
            exit(1)

    log('unzipping static...')
    unzip_static()

exit(0)