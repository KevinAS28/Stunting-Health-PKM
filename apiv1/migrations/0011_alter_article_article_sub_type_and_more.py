# Generated by Django 4.0.3 on 2022-06-07 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0010_rename_article_types_article_article_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='article_sub_type',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='article',
            name='article_tags',
            field=models.CharField(default='', max_length=63),
        ),
    ]
