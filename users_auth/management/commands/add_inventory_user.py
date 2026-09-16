from django.core.management.base import BaseCommand
from users_auth.models import User, Role, UserRole, Department


class Command(BaseCommand):
    help = 'Add inventory manager user (inventory/inv123) if missing'

    def handle(self, *args, **options):
        dept_pharm = Department.objects.filter(code='PHARM').first()
        dept_opd = Department.objects.filter(code='OPD').first()

        user, created = User.objects.get_or_create(
            username='inventory',
            defaults={
                'first_name': 'Joseph',
                'last_name': 'Mensah',
                'email': 'inventory@jfdhospital.gov.lr',
                'job_title': 'Inventory Manager',
                'department': dept_pharm or dept_opd,
            }
        )
        user.set_password('inv123')
        user.save()

        role = Role.objects.filter(code='INV_MGR').first()
        if role:
            UserRole.objects.get_or_create(user=user, role=role)
            self.stdout.write(self.style.SUCCESS(f'Inventory user ready (role: INV_MGR)'))
        else:
            self.stdout.write(self.style.WARNING('INV_MGR role not found — user created without role'))

        if created:
            self.stdout.write(self.style.SUCCESS('Created inventory user: inventory / inv123'))
        else:
            self.stdout.write(self.style.SUCCESS('Inventory user already exists: inventory / inv123'))
