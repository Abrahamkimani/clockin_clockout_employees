"""
Django management command to create sample data for testing.
Usage: python manage.py create_sample_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from authentication.models import User
from clients.models import Client
from sessions.models import ClockSession


class Command(BaseCommand):
    help = 'Create sample data for testing the application'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of sample users to create (default: 5)'
        )
        parser.add_argument(
            '--clients',
            type=int,
            default=10,
            help='Number of sample clients to create (default: 10)'
        )
        parser.add_argument(
            '--sessions',
            type=int,
            default=20,
            help='Number of sample sessions to create (default: 20)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample users
        users_count = options['users']
        self.create_sample_users(users_count)
        
        # Create sample clients
        clients_count = options['clients']
        self.create_sample_clients(clients_count)
        
        # Create sample sessions
        sessions_count = options['sessions']
        self.create_sample_sessions(sessions_count)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {users_count} users, {clients_count} clients, '
                f'and {sessions_count} sessions.'
            )
        )
    
    def create_sample_users(self, count):
        """Create sample practitioners."""
        departments = ['Mental Health', 'Crisis Intervention', 'Family Services', 'Case Management']
        positions = ['Clinical Therapist', 'Social Worker', 'Case Manager', 'Crisis Counselor']
        
        for i in range(count):
            user = User.objects.create_user(
                phone_number=f'+1555000{1000 + i}',
                email=f'practitioner{i+1}@wellness.com',
                password='testpass123',
                first_name=f'Practitioner{i+1}',
                last_name='TestUser',
                employee_id=f'EMP{1000 + i}',
                department=random.choice(departments),
                position=random.choice(positions),
                is_practitioner=True,
                is_supervisor=i == 0  # Make first user a supervisor
            )
            
            self.stdout.write(f'Created user: {user.get_full_name()} ({user.phone_number})')
    
    def create_sample_clients(self, count):
        """Create sample clients."""
        cities = ['Springfield', 'Riverside', 'Madison', 'Franklin', 'Georgetown']
        states = ['IL', 'CA', 'WI', 'TN', 'TX']
        care_levels = ['low', 'medium', 'high', 'crisis']
        
        # Base coordinates for Springfield, IL
        base_lat = 39.7817
        base_lng = -89.6501
        
        for i in range(count):
            # Generate random coordinates within ~50km of base location
            lat_offset = (random.random() - 0.5) * 0.9  # ~50km
            lng_offset = (random.random() - 0.5) * 0.9
            
            client = Client.objects.create(
                client_id=f'CLIENT{2000 + i}',
                first_name=f'Client{i+1}',
                last_name='TestClient',
                phone_number=f'+1555001{2000 + i}',
                email=f'client{i+1}@example.com',
                street_address=f'{100 + i} Test Street',
                city=random.choice(cities),
                state=random.choice(states),
                zip_code=f'{62701 + i}',
                latitude=Decimal(str(base_lat + lat_offset)),
                longitude=Decimal(str(base_lng + lng_offset)),
                care_level=random.choice(care_levels),
                special_instructions=f'Test instructions for client {i+1}',
                is_active=True
            )
            
            self.stdout.write(f'Created client: {client.get_full_name()} ({client.client_id})')
    
    def create_sample_sessions(self, count):
        """Create sample sessions."""
        users = list(User.objects.filter(is_practitioner=True))
        clients = list(Client.objects.filter(is_active=True))
        service_types = ['counseling', 'assessment', 'crisis_intervention', 'case_management']
        statuses = ['completed', 'completed', 'completed', 'active']  # Weighted toward completed
        
        if not users or not clients:
            self.stdout.write(
                self.style.WARNING('No users or clients found. Create them first.')
            )
            return
        
        for i in range(count):
            practitioner = random.choice(users)
            client = random.choice(clients)
            status = random.choice(statuses)
            service_type = random.choice(service_types)
            
            # Generate clock-in time (within last 30 days)
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(8, 18)  # Business hours
            clock_in_time = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
            
            # Generate coordinates near client location
            lat_offset = (random.random() - 0.5) * 0.002  # ~200m
            lng_offset = (random.random() - 0.5) * 0.002
            
            clock_in_lat = float(client.latitude) + lat_offset
            clock_in_lng = float(client.longitude) + lng_offset
            
            session = ClockSession.objects.create(
                practitioner=practitioner,
                client=client,
                status='active',  # Will be updated below if needed
                clock_in_time=clock_in_time,
                clock_in_latitude=Decimal(str(clock_in_lat)),
                clock_in_longitude=Decimal(str(clock_in_lng)),
                clock_in_accuracy=random.uniform(5, 50),
                service_type=service_type,
                session_notes=f'Sample session notes for session {i+1}'
            )
            
            # If session should be completed, add clock-out data
            if status == 'completed':
                session_duration = random.randint(30, 180)  # 30 minutes to 3 hours
                clock_out_time = clock_in_time + timedelta(minutes=session_duration)
                
                # Generate clock-out coordinates (slightly different from clock-in)
                clock_out_lat = clock_in_lat + (random.random() - 0.5) * 0.001
                clock_out_lng = clock_in_lng + (random.random() - 0.5) * 0.001
                
                session.clock_out_time = clock_out_time
                session.clock_out_latitude = Decimal(str(clock_out_lat))
                session.clock_out_longitude = Decimal(str(clock_out_lng))
                session.clock_out_accuracy = random.uniform(5, 50)
                session.status = 'completed'
                session.save()
            
            self.stdout.write(
                f'Created session: {practitioner.get_full_name()} -> {client.get_full_name()} '
                f'({status})'
            )
