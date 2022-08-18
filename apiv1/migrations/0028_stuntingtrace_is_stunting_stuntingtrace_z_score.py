# Generated by Django 4.0.3 on 2022-08-18 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0027_stuntingtrace_created_at_stuntingtrace_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='stuntingtrace',
            name='is_stunting',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='stuntingtrace',
            name='z_score',
            field=models.FloatField(default=3.75),
            preserve_default=False,
        ),
    ]
