"""
Management command to generate monthly DHIS2 report as a JSON file.

Usage:
    python manage.py generate_hmis_report --year 2026 --month 8
    python manage.py generate_hmis_report --output /path/to/output/
"""
import json
import os
from datetime import date

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Generate monthly DHIS2 HMIS report as a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year', type=int, default=date.today().year,
            help='Report year (default: current year)',
        )
        parser.add_argument(
            '--month', type=int, default=date.today().month,
            help='Report month 1-12 (default: current month)',
        )
        parser.add_argument(
            '--output', type=str, default='reports',
            help='Output directory (default: reports/)',
        )

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        output_dir = options['output']

        if month < 1 or month > 12:
            raise CommandError('Month must be between 1 and 12')

        from reports.services import build_dhis2_payload, get_hmis_summary

        self.stdout.write(f'Generating DHIS2 report for {year}-{month:02d}...')

        payload = build_dhis2_payload(year, month)
        summary = get_hmis_summary(year, month)

        os.makedirs(output_dir, exist_ok=True)
        filename = f'JFD_HMIS_DHIS2_{year}_{month:02d}.json'
        filepath = os.path.join(output_dir, filename)

        report = {
            'metadata': {
                'report_type': 'DHIS2 DataValueSets',
                'generated_at': date.today().isoformat(),
                'hospital': 'Jackson F. Doe Memorial Regional Referral Hospital',
                'period': f'{year}-{month:02d}',
            },
            'dhis2_payload': payload,
            'summary': summary,
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated: {filepath}\n'
            f'  Indicators: {len(payload["dataValues"])} data values\n'
            f'  Top diagnoses: {len(summary.get("top_diagnoses", []))}'
        ))
