from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.management import call_command

from ...models import SMSToken
from ...api.tasks import send_activation_code


class Command(BaseCommand):
    help = 'Check system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sms',
            action='store_true',
            help='Send test SMS',
        )
    def handle(self, *args, **options):
        print('Performing system check')
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('You are in DEBUG MODE'))
        if options['sms']:
            # Check SMS
            try:
                token = SMSToken.objects.get(pk=1)
                result = send_activation_code.delay('09121755310', '1234', token.token)
            except Exception as e:
                self.stderr.write(self.style.ERROR('ERROR: %s' % e))

        call_command("check", 'social')

        # call_command("inspectdb")

        self.stdout.write(self.style.SUCCESS('Successfully checked'))
