"""
Seed demo data for Surgery, OBGYN, Pediatric, and Lab modules.
Run after pilot_reset: python manage.py seed_demo_modules
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed demo data for all clinical modules'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('Seeding demo module data...'))

        from patients.models import Patient
        from clinical.models import (
            Visit, SurgicalCase, AntenatalVisit, LaborRecord,
            DeliveryRecord, BirthRecord, PostnatalVisit,
            PediatricAssessment, Specimen, Order, DiagnosticResult,
        )
        from users_auth.models import User, Department

        # Get existing users
        try:
            surgeon = User.objects.filter(is_superuser=False).first()
            doctor = User.objects.filter(is_superuser=False).first()
            nurse = User.objects.filter(is_superuser=False).first()
        except:
            surgeon = None
            doctor = None
            nurse = None

        # Get existing patients
        patients = list(Patient.objects.filter(is_temporary=False)[:12])
        if len(patients) < 3:
            self.stdout.write(self.style.WARNING('Not enough patients. Run seed_data first.'))
            return

        # Get existing visits
        visits = list(Visit.objects.filter(is_deleted=False)[:12])

        self.seed_surgery(patients, visits, surgeon)
        self.seed_obgyn(patients, visits, doctor, nurse)
        self.seed_pediatric(patients, visits, doctor)
        self.seed_lab(patients, visits)

        self.stdout.write(self.style.SUCCESS('Demo module data seeded successfully!'))

    def seed_surgery(self, patients, visits, surgeon):
        from clinical.models import SurgicalCase
        from django.utils import timezone

        if SurgicalCase.objects.exists():
            self.stdout.write('  Surgery: already seeded, skipping')
            return

        self.stdout.write('  Seeding surgical cases...')
        now = timezone.now()

        SurgicalCase.objects.get_or_create(
            patient=patients[0],
            procedure_name='Open Reduction Internal Fixation - Left Distal Radius',
            defaults={
                'surgical_site': 'Left Wrist',
                'laterality': 'left',
                'priority': 'urgent',
                'scheduled_date': now + timedelta(hours=2),
                'surgeon': surgeon,
                'anesthesia_type': 'general',
                'status': 'scheduled',
                'pre_op_diagnosis': 'Displaced distal radius fracture',
            }
        )
        SurgicalCase.objects.get_or_create(
            patient=patients[1],
            procedure_name='Appendectomy - Laparoscopic',
            defaults={
                'surgical_site': 'Right Lower Quadrant',
                'laterality': 'right',
                'priority': 'urgent',
                'scheduled_date': now - timedelta(hours=1),
                'surgeon': surgeon,
                'anesthesia_type': 'general',
                'status': 'in_progress',
                'pre_op_diagnosis': 'Acute appendicitis',
            }
        )
        SurgicalCase.objects.get_or_create(
            patient=patients[2],
            procedure_name='Inguinal Hernia Repair',
            defaults={
                'surgical_site': 'Right Inguinal Region',
                'laterality': 'right',
                'priority': 'elective',
                'scheduled_date': now - timedelta(days=1),
                'surgeon': surgeon,
                'anesthesia_type': 'spinal',
                'status': 'completed',
                'pre_op_diagnosis': 'Right indirect inguinal hernia',
                'post_op_diagnosis': 'Right indirect inguinal hernia confirmed',
                'duration_minutes': 45,
            }
        )
        self.stdout.write(f'    Created 3 surgical cases')

    def seed_obgyn(self, patients, visits, doctor, nurse):
        from clinical.models import AntenatalVisit, LaborRecord, DeliveryRecord, BirthRecord, PostnatalVisit
        from django.utils import timezone

        if AntenatalVisit.objects.exists():
            self.stdout.write('  OBGYN: already seeded, skipping')
            return

        self.stdout.write('  Seeding OBGYN records...')

        # Use female patients for OBGYN
        female_patients = [p for p in patients if p.gender == 'F'][:3]
        if len(female_patients) < 2:
            female_patients = patients[:3]

        # ANC Visit 1
        anc1 = AntenatalVisit.objects.create(
            patient=female_patients[0],
            lmp_date=date(2026, 1, 15),
            edd_date=date(2026, 10, 22),
            ga_weeks=32,
            gravida=2,
            parity=1,
            blood_group='O+',
            hemoglobin=Decimal('11.5'),
            blood_pressure_systolic=118,
            blood_pressure_diastolic=72,
            weight=Decimal('68.5'),
            fundal_height=30,
            fetal_heart_rate=142,
            presentation='cephalic',
            urine_protein='negative',
            urine_glucose='negative',
            next_visit_date=date(2026, 9, 15),
        )

        # ANC Visit 2
        anc2 = AntenatalVisit.objects.create(
            patient=female_patients[1],
            lmp_date=date(2026, 3, 1),
            edd_date=date(2026, 12, 6),
            ga_weeks=24,
            gravida=1,
            parity=0,
            blood_group='A+',
            hemoglobin=Decimal('10.8'),
            blood_pressure_systolic=110,
            blood_pressure_diastolic=68,
            weight=Decimal('62.0'),
            fundal_height=22,
            fetal_heart_rate=150,
            presentation='unknown',
            urine_protein='negative',
            urine_glucose='trace',
            next_visit_date=date(2026, 10, 1),
        )

        # Labor Record
        labor1 = LaborRecord.objects.create(
            patient=female_patients[0],
            admission_time=timezone.now() - timedelta(hours=6),
            cervical_dilation=Decimal('8.0'),
            fetal_heart_rate=138,
            presentation='cephalic',
            status='in_progress',
            labor_progress_notes='Active labor, cervix dilating well',
        )

        # Delivery Record
        delivery1 = DeliveryRecord.objects.create(
            labor_record=labor1,
            patient=female_patients[0],
            delivery_time=timezone.now() - timedelta(hours=2),
            delivery_method='vaginal',
            blood_loss_ml=350,
            perineal_tear='first_degree',
            episiotomy=True,
            oxytocin_given=True,
            notes='Normal vaginal delivery, first-degree tear repaired',
        )

        # Birth Record
        birth1 = BirthRecord.objects.create(
            delivery_record=delivery1,
            patient=female_patients[0],
            baby_name='Baby Boy Sackor',
            sex='M',
            birth_weight_grams=3200,
            birth_length_cm=Decimal('50.0'),
            apgar_score_1min=8,
            apgar_score_5min=9,
            apgar_score_10min=10,
            cry_at_birth=True,
            feeding_method='breast',
            vitamin_k_given=True,
            eye_prophylaxis_given=True,
            hepatitis_b_vaccine_given=True,
            status='alive',
        )

        # Postnatal Visit
        PostnatalVisit.objects.create(
            patient=female_patients[0],
            delivery_record=delivery1,
            visit_day_postpartum=1,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=78,
            temperature=Decimal('37.2'),
            fundal_height='firm, midline',
            lochia_assessment='rubra, moderate',
            perineal_assessment='repaired, clean',
            breast_assessment='engorged, lactating',
            baby_weight=Decimal('3.1'),
            baby_condition='good',
            feeding_method='breastfeeding',
            family_planning_counseling=True,
            notes='Mother and baby doing well. Continue breastfeeding.',
        )

        self.stdout.write(f'    Created 2 ANC, 1 labor, 1 delivery, 1 birth, 1 postnatal')

    def seed_pediatric(self, patients, visits, doctor):
        from patients.models import Patient
        from clinical.models import PediatricAssessment, Visit
        from django.utils import timezone

        if PediatricAssessment.objects.exists():
            self.stdout.write('  Pediatric: already seeded, skipping')
            return

        self.stdout.write('  Seeding pediatric patients and assessments...')

        # Create child patients
        child1, _ = Patient.objects.get_or_create(
            first_name='Emmanuel',
            last_name='Tolbert',
            defaults={
                'gender': 'M',
                'date_of_birth': date(2020, 6, 15),
                'phone': '0770123456',
                'payer_category': 'Insurance',
            }
        )
        child2, _ = Patient.objects.get_or_create(
            first_name='Sarah',
            last_name='Cooper',
            defaults={
                'gender': 'F',
                'date_of_birth': date(2018, 3, 22),
                'phone': '0770654321',
                'payer_category': 'Insurance',
            }
        )

        # Create visits for children
        visit_child1 = Visit.objects.create(
            patient=child1,
            visit_type='pediatric',
            status='in_progress',
            chief_complaint='Fever and cough for 2 days',
            triage_priority='urgent',
            check_in_time=timezone.now() - timedelta(hours=3),
        )
        visit_child2 = Visit.objects.create(
            patient=child2,
            visit_type='pediatric',
            status='checked_in',
            chief_complaint='Diarrhea and vomiting for 1 day',
            triage_priority='urgent',
            check_in_time=timezone.now() - timedelta(hours=1),
        )

        # Pediatric Assessment 1
        PediatricAssessment.objects.create(
            visit=visit_child1,
            patient=child1,
            visit_type='first',
            child_problem='Fever and productive cough for 2 days, worse at night',
            pulse=110,
            respiratory_rate=32,
            temperature=Decimal('38.8'),
            bp='',
            sao2=Decimal('95'),
            weight=Decimal('14.5'),
            height=Decimal('98'),
            head_circumference=None,
            cough_breath_difficulty=True,
            fever_present=True,
            lethargy_unconscious=False,
            convulsing_now=False,
            has_diarrhea=False,
            severe_pallor=False,
            sleeping_under_net=True,
            muac=Decimal('14.5'),
            provisional_diagnosis='Pneumonia, community-acquired',
            treatment='Amoxicillin 250mg TID x 7 days, Paracetamol 150mg QID PRN fever',
            follow_up_notes='Return in 1 week or sooner if worsening',
            completed_by=doctor,
        )

        # Pediatric Assessment 2
        PediatricAssessment.objects.create(
            visit=visit_child2,
            patient=child2,
            visit_type='repeat',
            child_problem='Watery diarrhea and vomiting for 1 day, 5 episodes',
            pulse=120,
            respiratory_rate=24,
            temperature=Decimal('37.8'),
            bp='',
            sao2=Decimal('98'),
            weight=Decimal('18.0'),
            height=Decimal('110'),
            head_circumference=None,
            has_diarrhea=True,
            blood_in_stool=False,
            dehydration_signs=True,
            sunken_eyes=True,
            delayed_capillary_refill=False,
            poor_skin_turgor=True,
            vomits_everything=True,
            severe_pallor=False,
            fever_present=True,
            sleeping_under_net=True,
            muac=Decimal('15.2'),
            provisional_diagnosis='Acute gastroenteritis with moderate dehydration',
            treatment='ORS after each stool, Zinc 20mg x 10 days, continue breastfeeding',
            follow_up_notes='Reassess in 24 hours',
            completed_by=doctor,
        )

        self.stdout.write(f'    Created 2 child patients, 2 visits, 2 assessments')

    def seed_lab(self, patients, visits):
        from clinical.models import Order, Specimen, DiagnosticResult

        if Specimen.objects.exists():
            self.stdout.write('  Lab: already seeded, skipping')
            return

        self.stdout.write('  Seeding lab specimens and results...')

        # Find existing lab orders
        lab_orders = list(Order.objects.filter(order_type='lab')[:3])
        if not lab_orders:
            self.stdout.write('    No lab orders found, creating sample orders...')
            for i, patient in enumerate(patients[:3]):
                order = Order.objects.create(
                    patient=patient,
                    visit=visits[i] if i < len(visits) else None,
                    order_type='lab',
                    order_description=f'{"CBC" if i == 0 else "Malaria RDT" if i == 1 else "Urinalysis"}',
                    priority='routine',
                    status='pending',
                )
                lab_orders.append(order)

        # Create specimens for existing orders
        from django.utils import timezone
        from users_auth.models import User
        now = timezone.now()
        nurse_user = User.objects.filter(is_superuser=False).first()

        for i, order in enumerate(lab_orders[:3]):
            spec = Specimen.objects.create(
                order=order,
                patient=order.patient,
                specimen_type='Blood' if i != 2 else 'Urine',
                status='completed' if i < 2 else 'received',
                collection_datetime=now - timedelta(hours=4 - i),
                collected_by=nurse_user,
            )

            if i < 2:
                DiagnosticResult.objects.create(
                    order=order,
                    patient=order.patient,
                    visit=order.visit,
                    result_text='WBC: 8.5 x10^3/uL (Normal)\nRBC: 4.8 x10^6/uL (Normal)\nHgb: 13.2 g/dL (Normal)\nHct: 39.6% (Normal)\nPlatelets: 250 x10^3/uL (Normal)' if i == 0 else 'Plasmodium falciparum: Positive (+++)\nParasite count: 150,000/uL',
                    status='verified',
                    is_abnormal=True if i == 1 else False,
                    critical_flag=False,
                    verified_by=nurse_user,
                )

        self.stdout.write(f'    Created 3 specimens, 2 diagnostic results')
