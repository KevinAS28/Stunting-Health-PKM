from django.core.management.base import BaseCommand, CommandError
from apiv1 import models as apiv1_models

class Command(BaseCommand):
    help = 'Seeder management'

    def add_arguments(self, parser):
        parser.add_argument('--migrate', action='store_true', help='Execute the database seeder')

    def migrate_seeds(self):
        apiv1_models.GeneralConfig(key='last_question_index', value=0).save()
        self.stdout.write(self.style.SUCCESS('Seeder migration success'))

    def handle(self, *args, **options):
        if options['migrate']:
            self.migrate_seeds()
        else:
            self.stdout.write(self.style.ERROR('No command action provided, please use -h for usages.'))
    