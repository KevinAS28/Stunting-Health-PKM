import os
import pandas as pd
from django.conf import settings

tb = pd.read_csv(os.path.join(settings.BASE_DIR, 'apiv1', 'stunt_boy.csv'))
tg = pd.read_csv(os.path.join(settings.BASE_DIR, 'apiv1', 'stunt_girl.csv'))

def stunting_classification(sex, age_month, height):
    if sex==0:
        table = tb
    else:
        table = tg
    data = table.loc[table['age_month']==age_month].iloc[0]

    median = float(data['Median'])
    
    if height < median:
        sd = float(data['-1_SD'])
    elif height > median:
        sd = float(data['3_SD'])
    else:
        return 0, z_score

    z_score = ((height-median)/abs(median-sd))

    print(z_score)
    if z_score < -3:
        return -2, z_score
    elif -3 <= z_score < -2:
        return -1, z_score
    elif -2 <= z_score <= 2:
        return 1, z_score
    else:
        return 2, z_score

if __name__=='__main__':
    print(stunting_classification(0, 26, 90))