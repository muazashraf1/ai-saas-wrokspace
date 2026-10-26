from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from usage.models import PlanLimit
from workspaces.models import Workspace, WorkspaceMember

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds initial plan limits (Free, Pro) and creates a demo user & workspace."

    def handle(self, *args, **options):
        self.stdout.write("Seeding plan limits...")

        with transaction.atomic():
            # 1. Seed Plan Limits
            PlanLimit.objects.update_or_create(
                plan='free',
                defaults={
                    'daily_questions': 20,
                    'monthly_tokens': 100000,
                    'max_documents': 10,
                    'max_file_mb': 10,
                }
            )
            PlanLimit.objects.update_or_create(
                plan='pro',
                defaults={
                    'daily_questions': 200,
                    'monthly_tokens': 2000000,
                    'max_documents': 100,
                    'max_file_mb': 50,
                }
            )

            # 2. Seed Demo User
            demo_email = "demo@example.com"
            demo_password = "Password123!"
            user, created = User.objects.get_or_create(
                email=demo_email,
                defaults={'full_name': 'Demo User', 'is_staff': True}
            )
            if created or not user.has_usable_password():
                user.set_password(demo_password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created demo user: {demo_email}"))
            else:
                self.stdout.write(f"Demo user already exists: {demo_email}")

            # 3. Seed Demo Workspace
            workspace, ws_created = Workspace.objects.get_or_create(
                name="Acme HR",
                owner=user,
                defaults={'plan': 'free'}
            )
            WorkspaceMember.objects.get_or_create(
                workspace=workspace,
                user=user,
                defaults={'role': 'owner'}
            )

        self.stdout.write(self.style.SUCCESS("Plan limits and demo account successfully seeded!"))
        self.stdout.write(f"Credentials -> Email: {demo_email} | Password: {demo_password}")
        self.stdout.write(f"Demo Workspace -> ID: {workspace.id} | Name: {workspace.name}")
