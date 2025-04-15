from django.contrib import admin
from django.utils.html import format_html
from django import forms

from superapp.apps.admin_portal.admin import SuperAppModelAdmin
from superapp.apps.admin_portal.sites import superapp_admin_site
from superapp.apps.admin_portal.widgets import PasswordToggleWidget
from superapp.apps.email.models import EmailAddress


class EmailAddressForm(forms.ModelForm):
    class Meta:
        model = EmailAddress
        fields = '__all__'
        widgets = {
            'smtp_password': PasswordToggleWidget(),
            'imap_password': PasswordToggleWidget(),
        }


@admin.register(EmailAddress, site=superapp_admin_site)
class EmailAddressAdmin(SuperAppModelAdmin):
    form = EmailAddressForm
    list_display = ['email', 'name', 'smtp_server', 'is_active', 'created_at']
    list_filter = ['is_active', 'smtp_connection_type', 'imap_connection_type']
    search_fields = ['email', 'name', 'smtp_server']
    readonly_fields = ['created_at', 'updated_at', 'aws_ses_help_text',]
    fieldsets = (
        (None, {
            'fields': ('email', 'name', 'is_active')
        }),
        ('SMTP Configuration', {
            'fields': ('smtp_connection_type', 'smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', )
        }),
        ('IMAP Configuration', {
            'fields': ('imap_connection_type', 'imap_server', 'imap_port', 'imap_username', 'imap_password', 
                      'use_idle', 'idle_folder')
        }),
        ('AWS SES Setup Guide', {
            'fields': ('aws_ses_help_text',),
            'classes': ('collapse',),
            'description': 'Instructions for setting up AWS SES for email sending and receiving'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def aws_ses_help_text(self, obj):
        """
        Display help text for AWS SES setup with Tailwind CSS styling that works in both light and dark modes
        """
        help_text = """
        <div class="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div class="bg-blue-600 dark:bg-blue-800 text-white px-6 py-4">
                <h3 class="text-xl font-bold">Setting up AWS SES for Email Sending and Receiving</h3>
            </div>
            
            <div class="p-6 space-y-6">
                <!-- Prerequisites Section -->
                <div>
                    <h4 class="text-lg font-semibold text-blue-700 dark:text-blue-400 border-b border-gray-200 dark:border-gray-700 pb-2 mb-3">Prerequisites:</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                        <li>An AWS account with access to SES (Simple Email Service)</li>
                        <li>Verified domain or email address in SES</li>
                        <li>If your account is in the SES sandbox, you can only send to verified email addresses</li>
                    </ul>
                </div>
                
                <!-- SMTP Configuration Section -->
                <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <h4 class="text-lg font-semibold text-blue-700 dark:text-blue-400 border-b border-gray-200 dark:border-gray-600 pb-2 mb-3">SMTP Configuration for AWS SES:</h4>
                    <ol class="list-decimal pl-6 space-y-3 text-gray-700 dark:text-gray-300">
                        <li>Go to AWS SES Console → SMTP Settings</li>
                        <li>Create SMTP credentials (these are different from your regular AWS credentials)</li>
                        <li>
                            <p class="mb-2">Use the following settings:</p>
                            <div class="bg-white dark:bg-gray-800 p-4 rounded border border-gray-200 dark:border-gray-600">
                                <ul class="space-y-2">
                                    <li><span class="font-semibold text-gray-800 dark:text-gray-200">SMTP Server:</span> <span class="text-gray-700 dark:text-gray-300">email-smtp.[your-region].amazonaws.com (e.g., email-smtp.us-east-1.amazonaws.com)</span></li>
                                    <li><span class="font-semibold text-gray-800 dark:text-gray-200">SMTP Port:</span> <span class="text-gray-700 dark:text-gray-300">587 (TLS) or 465 (SSL)</span></li>
                                    <li><span class="font-semibold text-gray-800 dark:text-gray-200">SMTP Username:</span> <span class="text-gray-700 dark:text-gray-300">Your SES SMTP username</span></li>
                                    <li><span class="font-semibold text-gray-800 dark:text-gray-200">SMTP Password:</span> <span class="text-gray-700 dark:text-gray-300">Your SES SMTP password</span></li>
                                    <li><span class="font-semibold text-gray-800 dark:text-gray-200">Use TLS:</span> <span class="text-gray-700 dark:text-gray-300">Yes (for port 587)</span></li>
                                    <li><span class="font-semibold text-gray-800 dark:text-gray-200">Use SSL:</span> <span class="text-gray-700 dark:text-gray-300">Yes (for port 465)</span></li>
                                </ul>
                            </div>
                        </li>
                    </ol>
                </div>
                
                <!-- Email Receiving Section -->
                <div>
                    <h4 class="text-lg font-semibold text-blue-700 dark:text-blue-400 border-b border-gray-200 dark:border-gray-700 pb-2 mb-3">Setting up Email Receiving with AWS SES and IMAP:</h4>
                    <p class="mb-4 text-gray-700 dark:text-gray-300">AWS SES doesn't provide IMAP access directly. You have two options:</p>
                    
                    <!-- Option 1 -->
                    <div class="mb-6 bg-green-50 dark:bg-green-900/30 p-4 rounded-lg">
                        <h5 class="text-md font-semibold text-green-700 dark:text-green-400 mb-2">Option 1: Use Amazon WorkMail (recommended)</h5>
                        <ol class="list-decimal pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                            <li>Set up Amazon WorkMail in the same region as your SES</li>
                            <li>Create a WorkMail organization and add your domain</li>
                            <li>Create mailboxes for your verified email addresses</li>
                            <li>
                                <p class="mb-2">Use the following IMAP settings:</p>
                                <div class="bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-600">
                                    <ul class="space-y-1">
                                        <li><span class="font-semibold text-gray-800 dark:text-gray-200">IMAP Server:</span> <span class="text-gray-700 dark:text-gray-300">outlook.office365.com (WorkMail uses Exchange)</span></li>
                                        <li><span class="font-semibold text-gray-800 dark:text-gray-200">IMAP Port:</span> <span class="text-gray-700 dark:text-gray-300">993</span></li>
                                        <li><span class="font-semibold text-gray-800 dark:text-gray-200">IMAP Username:</span> <span class="text-gray-700 dark:text-gray-300">Your WorkMail email address</span></li>
                                        <li><span class="font-semibold text-gray-800 dark:text-gray-200">IMAP Password:</span> <span class="text-gray-700 dark:text-gray-300">Your WorkMail password</span></li>
                                    </ul>
                                </div>
                            </li>
                        </ol>
                    </div>
                    
                    <!-- Option 2 -->
                    <div class="bg-yellow-50 dark:bg-yellow-900/30 p-4 rounded-lg">
                        <h5 class="text-md font-semibold text-yellow-700 dark:text-yellow-400 mb-2">Option 2: Use SES Rule Sets with S3 and Lambda</h5>
                        <ol class="list-decimal pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                            <li>Create an S3 bucket to store incoming emails</li>
                            <li>Create a Receipt Rule Set in SES that saves emails to your S3 bucket</li>
                            <li>Set up a Lambda function to process emails from S3 and insert them into your database</li>
                            <li>For this option, leave the IMAP fields blank as you'll be using AWS services directly</li>
                        </ol>
                    </div>
                </div>
                
                <!-- Moving out of Sandbox Section -->
                <div class="bg-purple-50 dark:bg-purple-900/30 p-4 rounded-lg mt-6">
                    <h4 class="text-lg font-semibold text-purple-700 dark:text-purple-400 border-b border-gray-200 dark:border-gray-700 pb-2 mb-3">Moving out of the SES Sandbox:</h4>
                    <p class="mb-2 text-gray-700 dark:text-gray-300">To send emails to non-verified addresses, request production access by:</p>
                    <ol class="list-decimal pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                        <li>Go to AWS SES Console → Sending Statistics</li>
                        <li>Click "Request Production Access"</li>
                        <li>Fill out the form with your use case details</li>
                        <li>Wait for AWS approval (typically 1-2 business days)</li>
                    </ol>
                </div>
                
                <!-- Best Practices Section -->
                <div class="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-lg">
                    <h4 class="text-lg font-semibold text-blue-700 dark:text-blue-400 border-b border-gray-200 dark:border-gray-700 pb-2 mb-3">Best Practices:</h4>
                    <ul class="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                        <li>Monitor your sending reputation in the SES dashboard</li>
                        <li>Set up feedback notifications for bounces and complaints</li>
                        <li>Implement proper SPF, DKIM, and DMARC records for your domain</li>
                        <li>Start with low sending volumes and gradually increase</li>
                    </ul>
                </div>
            </div>
        </div>
        """
        return format_html(help_text)
