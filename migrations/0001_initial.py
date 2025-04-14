# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('name', models.CharField(blank=True, max_length=255, verbose_name='name')),
                ('company', models.CharField(blank=True, max_length=255, verbose_name='company')),
                ('job_title', models.CharField(blank=True, max_length=255, verbose_name='job title')),
                ('phone_number', models.CharField(blank=True, max_length=50, verbose_name='phone number')),
                ('notes', models.TextField(blank=True, verbose_name='notes')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='metadata')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
            ],
            options={
                'verbose_name': 'contact',
                'verbose_name_plural': 'contacts',
                'ordering': ['name', 'email'],
            },
        ),
        migrations.CreateModel(
            name='EmailAddress',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('name', models.CharField(blank=True, max_length=255, verbose_name='display name')),
                ('smtp_server', models.CharField(max_length=255, verbose_name='SMTP server')),
                ('smtp_port', models.PositiveIntegerField(default=587, verbose_name='SMTP port')),
                ('smtp_username', models.CharField(max_length=255, verbose_name='SMTP username')),
                ('smtp_password', models.CharField(max_length=255, verbose_name='SMTP password')),
                ('use_tls', models.BooleanField(default=True, verbose_name='use TLS')),
                ('use_ssl', models.BooleanField(default=False, verbose_name='use SSL')),
                ('imap_server', models.CharField(blank=True, max_length=255, verbose_name='IMAP server')),
                ('imap_port', models.PositiveIntegerField(default=993, verbose_name='IMAP port')),
                ('imap_username', models.CharField(blank=True, max_length=255, verbose_name='IMAP username')),
                ('imap_password', models.CharField(blank=True, max_length=255, verbose_name='IMAP password')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
            ],
            options={
                'verbose_name': 'email address',
                'verbose_name_plural': 'email addresses',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('direction', models.CharField(choices=[('incoming', 'Incoming'), ('outgoing', 'Outgoing')], default='outgoing', max_length=10, verbose_name='direction')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('sending', 'Sending'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('failed', 'Failed'), ('received', 'Received')], default='draft', max_length=10, verbose_name='status')),
                ('message_id', models.CharField(blank=True, max_length=255, verbose_name='message ID')),
                ('from_email', models.EmailField(max_length=254, verbose_name='from email')),
                ('from_name', models.CharField(blank=True, max_length=255, verbose_name='from name')),
                ('to_emails', models.JSONField(default=list, verbose_name='to emails')),
                ('cc_emails', models.JSONField(blank=True, default=list, verbose_name='cc emails')),
                ('bcc_emails', models.JSONField(blank=True, default=list, verbose_name='bcc emails')),
                ('subject', models.CharField(max_length=255, verbose_name='subject')),
                ('body_text', models.TextField(blank=True, verbose_name='body text')),
                ('body_html', models.TextField(blank=True, verbose_name='body HTML')),
                ('attachments', models.JSONField(blank=True, default=list, verbose_name='attachments')),
                ('headers', models.JSONField(blank=True, default=dict, verbose_name='headers')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='metadata')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='sent at')),
                ('delivered_at', models.DateTimeField(blank=True, null=True, verbose_name='delivered at')),
                ('error_message', models.TextField(blank=True, verbose_name='error message')),
                ('error_code', models.CharField(blank=True, max_length=50, verbose_name='error code')),
                ('raw_message', models.TextField(blank=True, verbose_name='raw message')),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emails', to='email.contact', verbose_name='contact')),
                ('email_address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emails', to='email.emailaddress', verbose_name='email address')),
            ],
            options={
                'verbose_name': 'email',
                'verbose_name_plural': 'emails',
                'ordering': ['-created_at'],
            },
        ),
    ]
