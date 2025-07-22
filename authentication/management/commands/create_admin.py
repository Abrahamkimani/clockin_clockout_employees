from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser with phone number and password (for Render deploys)'

    def handle(self, *args, **options):
        User = get_user_model()
        phone_number = '0769629949'
        password = '1234567890'
        email = 'admin@example.com'
        if not User.objects.filter(phone_number=phone_number).exists():
            User.objects.create_superuser(
                phone_number=phone_number,
                password=password,
                email=email,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Superuser created.'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists.'))
