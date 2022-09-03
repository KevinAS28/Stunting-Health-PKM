import os
import pandas as pd
import math
# from django.conf import settings

# tb = pd.read_csv(os.path.join(settings.BASE_DIR, 'apiv1', 'stunt_boy.csv'))
# tg = pd.read_csv(os.path.join(settings.BASE_DIR, 'apiv1', 'stunt_girl.csv'))

tb = pd.read_csv('stunt_boy.csv')
tg = pd.read_csv('stunt_girl.csv')

def stunting_classification(sex, age_month, height):
    if sex==0:
        table = tb
        # print('trace: boy table')
    else:
        table = tg
        # print('trace: girl table')

    data = table.loc[table['age_month']==age_month].iloc[0]

    median = float(data['Median'])
    # print('trace: median: ', median)
    if height < median:
        sd = float(data['-1_SD'])
    elif height > median:
        sd = float(data['3_SD'])
    else:
        return 1, 0

    # print('trace sd: ', sd)

    z_score = (((height-median)/abs(median-sd)))
    # print('trace z_score ori:', z_score)
    # z_score = float(str(z_score)[:3]) if z_score < 0 else float(str(z_score)[:2])
    # print('trace z_score ROUNDED:', z_score)
    
    # if sex==0:
    #     if z_score < -3.05:
    #         return -2, z_score
    #     elif -3.05 <= z_score < -2:
    #         return -1, z_score      
    #     elif -2 <= z_score <= 2:
    #         return 1, z_score
    #     else:
    #         return 2, z_score
    # else:
    #     if z_score <= -3.05:    # Beda tipis
    #         return -2, z_score
    #     elif (-3.05 < z_score < -2):
    #         return -1, z_score      
    #     elif -2 <= z_score <= 2:
    #         return 1, z_score
    #     else:
    #         return 2, z_score       

    # if z_score < -3.1:
    #     return -2, z_score
    # elif -3.1 <= z_score < -2:
    #     return -1, z_score      
    # elif -2 <= z_score <= 2:
    #     return 1, z_score
    # else:
    #     return 2, z_score

    if height < data['-3_SD']:
        return -2, z_score
    elif data['-3_SD'] <= height < data['-2_SD']:
        return -1, z_score
    elif data['-2_SD'] <= height < data['2_SD']:
        return 1, z_score
    else:
        return 2, z_score

if __name__=='__main__':
    #1: cewe, 0: cowo.
    test_table = [
        ([0, 0, 60], 2),
        ([1, 0, 53], 2),
        ([1, 0, 43.6], -1),
        ([1, 0, 43.7], -1),
        ([1, 0, 43.5], -2),
        ([0, 0, 46.1], 1),

        ([0, 52, 110], 1),
        ([1, 24, 76], -1),
        ([1, 52, 91.6], -2),
        ([1, 52, 91.7], -1),
        ([0, 24, 78], -1),
        ([0, 24, 77.9], -2),
    ]
    #FORMAT: gender, bulan, tinggi, hasil

    salah = False
    for test in test_table:
        status, z_score = stunting_classification(*test[0])
        if status!=test[1]:
            print(f'SALAH: {test}, {status}, {z_score}')
            salah = True
    if not salah:
        print('TESTING SMUA BERHASIL')

    
    # print(stunting_classification(1, 0, 53))