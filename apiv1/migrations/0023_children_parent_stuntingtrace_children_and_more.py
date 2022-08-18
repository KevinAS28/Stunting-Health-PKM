# Generated by Django 4.0.3 on 2022-08-05 07:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('token_authentication', '0002_alter_userauthentication_role'),
        ('apiv1', '0022_children_reporter_articles'),
    ]

    operations = [
        migrations.AddField(
            model_name='children',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.userprofile'),
        ),
        migrations.AddField(
            model_name='stuntingtrace',
            name='children',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.children'),
        ),
        migrations.AlterField(
            model_name='funstuntuseranswer',
            name='question',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.funstuntqa'),
        ),
        migrations.AlterField(
            model_name='funstuntuseranswer',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.userprofile'),
        ),
        migrations.AlterField(
            model_name='healthworker',
            name='work_place',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.stuntplace'),
        ),
        migrations.AlterField(
            model_name='stuntingtrace',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.userprofile'),
        ),
        migrations.AlterField(
            model_name='stuntplacereview',
            name='stunt_place',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.stuntplace'),
        ),
        migrations.AlterField(
            model_name='stuntplacereview',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.userprofile'),
        ),
        migrations.AlterField(
            model_name='stuntreminder',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apiv1.userprofile'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='authentication',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='token_authentication.userauthentication'),
        ),
        migrations.DeleteModel(
            name='Articles',
        ),
        migrations.DeleteModel(
            name='Reporter',
        ),
    ]