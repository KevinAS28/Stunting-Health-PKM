from apiv1.models import *
import apiv1.stuntech_core as stcore
from token_authentication import models as ta_models
import pandas as pd
from datetime import date
import random

df = pd.read_csv('dummy/baby-names.csv')[['name', 'sex']].iloc[0:50000]
df['sex'] = df['sex'].apply(lambda sex: 0 if sex.strip()=='boy' else 'girl')
for i in range(25):
    df = df.sample(frac=1).reset_index(drop=True)
all_childs = []
all_parents = []
for index, row in df.iterrows():
    parent_name = f'par_{index+1}'
    role = ta_models.UserRole.objects.get(role_name='user')
    # role.save()
    auth = ta_models.UserAuthentication(username=parent_name, password=parent_name, role=role)
    auth.save()
    parent = UserProfile(authentication=auth, name=parent_name, email=f'{parent_name}@gmail.com')
    parent.save()
    child = Children(name=row['name'], born_date=date(year=random.randrange(2018, 2023), month=random.randrange(1, 13), day=random.randrange(1, 29)), gender=row['sex'], active=True, parent=parent)
    child.save()
    all_childs.append(child)
    all_parents.append(parent)
    week = int(random.choice(list(range(0, 60, 4))))
    height = random.randrange(40, 160)
    try:
        growth_level, z_score = stcore.stunting_classification(row['sex'], int(week/4), height)
    except:
        print('error: ', int(week/4))
        break
    trace = StuntingTrace(user=parent, week=week, height=height, weight=random.randrange(1, 35), age_day=week*4, exclusive_asi=True, disease_history=False, immunization_history=False, children=child, z_score=z_score, growth_level=growth_level)
    trace.save()
    # break
# print('success')
# all_childrens = 