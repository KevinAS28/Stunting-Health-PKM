# Generated by Django 4.0.3 on 2022-06-01 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0004_stuntplace_alter_userprofile_authentication_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='email',
            field=models.CharField(blank=True, default='', max_length=30, null=True),
        ),
    ]
