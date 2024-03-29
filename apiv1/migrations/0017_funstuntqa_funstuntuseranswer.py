# Generated by Django 4.0.3 on 2022-08-01 09:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0016_delete_test'),
    ]

    operations = [
        migrations.CreateModel(
            name='FunStuntQA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_file', models.CharField(max_length=50)),
                ('level', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='FunStuntUserAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.IntegerField()),
                ('answer_is_correct', models.BooleanField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='apiv1.funstuntqa')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='apiv1.userprofile')),
            ],
        ),
    ]
