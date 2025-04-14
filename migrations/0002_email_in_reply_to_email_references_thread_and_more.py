# Generated by Django 5.1.8 on 2025-04-08 17:14

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='in_reply_to',
            field=models.CharField(blank=True, max_length=255, verbose_name='in reply to'),
        ),
        migrations.AddField(
            model_name='email',
            name='references',
            field=models.TextField(blank=True, verbose_name='references'),
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('subject', models.CharField(max_length=255, verbose_name='subject')),
                ('participants', models.JSONField(default=list, verbose_name='participants')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='metadata')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
                ('is_archived', models.BooleanField(default=False, verbose_name='is archived')),
                ('last_message_at', models.DateTimeField(blank=True, null=True, verbose_name='last message at')),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='threads', to='email.contact', verbose_name='primary contact')),
                ('email_address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='threads', to='email.emailaddress', verbose_name='email address')),
            ],
            options={
                'verbose_name': 'thread',
                'verbose_name_plural': 'threads',
                'ordering': ['-last_message_at', '-created_at'],
            },
        ),
        migrations.AddField(
            model_name='email',
            name='thread',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='emails', to='email.thread', verbose_name='thread'),
        ),
    ]
