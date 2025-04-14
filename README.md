# Django SuperApp - Sample App
### Getting Started
1. Setup the project using the instructions from https://django-superapp.bringes.io/
2. Setup `sample_app` app using the below instructions:
```bash
cd my_superapp;
cd superapp/apps;
django_superapp bootstrap-app \
    --template-repo https://github.com/django-superapp/django-superapp-sample-app ./sample_app;
cd ../../;
```

### Documentation
For a more detailed documentation, visit [https://django-superapp.bringes.io](https://django-superapp.bringes.io).
# django-superapp-email

A Django app component for sending and receiving emails. This component provides:

- Email synchronization with IMAP servers
- Outgoing email delivery through SMTP
- Real-time email synchronization using IMAP IDLE
- Email threading and conversation management
- Complete admin interface for managing emails, contacts, and email accounts

## Features

- Send and receive emails through configured email accounts
- Organize emails into conversation threads
- Store contacts from email communications
- Schedule email delivery and synchronization
- Support for real-time email monitoring
