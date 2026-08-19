"""
Management command: seed_data

Populates the database with realistic Nigerian FUTA-themed data.
Run: python manage.py seed_data [--clear] [--batch N]

Options:
  --clear    Wipe all existing data before seeding
  --batch N  Run only batch N (1-8), useful for incremental seeding
"""

import os
import random
import sys
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

# Add project root to path for .internal_assets import
_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from internal_assets.seed_config import (
    ALL_SKILLS,
    COMPANIES,
    DEFAULT_COMPANIES,
    DEPT_CODES,
    ENGAGEMENT_TYPES,
    EVENT_CATEGORIES,
    EVENT_MODES,
    EVENT_TITLES,
    FIRST_NAMES_FEMALE,
    FIRST_NAMES_MALE,
    FUTA_DEPARTMENTS,
    INDUSTRIES,
    INTERNSHIP_DESCRIPTION_TEMPLATES,
    INTERNSHIP_TASKS,
    INTERNSHIP_TITLES,
    LAST_NAMES,
    MENTORSHIP_CATEGORIES,
    MENTORSHIP_DESCRIPTION_TEMPLATES,
    MENTORSHIP_FOCUS_AREAS,
    MENTORSHIP_TITLES,
    NIGERIAN_STATES,
    NOTIFICATION_CONTENT_TEMPLATES,
    NOTIFICATION_TITLES,
    POST_COMPLETION_TEMPLATES,
    POST_MILESTONE_TEMPLATES,
    POST_STARTER_TEMPLATES,
    REVIEW_TEXTS_NEGATIVE,
    REVIEW_TEXTS_NEUTRAL,
    REVIEW_TEXTS_POSITIVE,
    TECH_SKILLS,
    WORK_MODES,
    random_date_in_past,
    random_future_date,
    random_matric_number,
    random_phone_number,
    weighted_choice,
)


class Command(BaseCommand):
    help = "Seed the database with realistic Nigerian FUTA-themed data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )
        parser.add_argument(
            "--batch",
            type=int,
            default=0,
            help="Run only a specific batch (1-8), 0 = all",
        )

    def handle(self, *args, **options):
        self.faker = Faker("en_US")
        self.style.SUCCESS("Seeding database with Nigerian FUTA data...")

        if options["clear"]:
            self.clear_data()

        batch = options["batch"]
        batches = {
            1: ("Users + Profiles", self.batch_users),
            2: ("Listings", self.batch_listings),
            3: ("Applications", self.batch_applications),
            4: ("Offers", self.batch_offers),
            5: ("Engagements", self.batch_engagements),
            6: ("Events", self.batch_events),
            7: ("Social (Posts + Notifications)", self.batch_social),
            8: ("Reviews + Feed", self.batch_reviews_feed),
        }

        if batch:
            if batch not in batches:
                self.stdout.write(self.style.ERROR(f"Invalid batch: {batch}. Use 1-8."))
                return
            name, func = batches[batch]
            self.stdout.write(f"\n--- Batch {batch}: {name} ---")
            with transaction.atomic():
                func()
        else:
            for num, (name, func) in batches.items():
                self.stdout.write(f"\n--- Batch {num}: {name} ---")
                with transaction.atomic():
                    func()

        self.stdout.write(self.style.SUCCESS("\nSeeding complete!"))

    # ------------------------------------------------------------------
    # CLEAR
    # ------------------------------------------------------------------

    def clear_data(self):
        self.stdout.write("Clearing existing data...")
        from core.models import (
            OTP,
            AlumniProfile,
            StudentProfile,
            StudentResume,
            User,
            UserProfileImage,
        )
        from engagements.models import Engagement
        from events.models import Event, Ticket, TicketPurchase, VirtualMeeting
        from feed.models import FeedEvent, FeedImpression, FeedTarget
        from internships.models import (
            Internship,
            InternshipApplication,
            InternshipEngagement,
            InternshipOffer,
        )
        from mentorships.models import (
            Mentorship,
            MentorshipApplication,
            MentorshipEngagement,
            MentorshipOffer,
        )
        from notifications.models import Notification
        from payments.models import Subaccount
        from posts.models import Post
        from reviews.models import Review

        with transaction.atomic():
            FeedImpression.objects.all().delete()
            FeedTarget.objects.all().delete()
            FeedEvent.objects.all().delete()
            Notification.objects.all().delete()
            Review.objects.all().delete()
            Post.objects.all().delete()
            Engagement.objects.all().delete()
            InternshipEngagement.objects.all().delete()
            InternshipOffer.objects.all().delete()
            InternshipApplication.objects.all().delete()
            Internship.objects.all().delete()
            MentorshipEngagement.objects.all().delete()
            MentorshipOffer.objects.all().delete()
            MentorshipApplication.objects.all().delete()
            Mentorship.objects.all().delete()
            VirtualMeeting.objects.all().delete()
            TicketPurchase.objects.all().delete()
            Ticket.objects.all().delete()
            Event.objects.all().delete()
            Subaccount.objects.all().delete()
            StudentResume.objects.all().delete()
            StudentProfile.objects.all().delete()
            AlumniProfile.objects.all().delete()
            OTP.objects.all().delete()
            UserProfileImage.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.WARNING("Existing data cleared."))

    # ==================================================================
    # BATCH 1: Users + Profiles
    # ==================================================================

    def batch_users(self):
        from core.models import AlumniProfile, StudentProfile, User

        used_emails = set()
        self.alumni_users = []
        self.student_users = []

        def make_email(first, last):
            base = f"{first.lower()}.{last.lower()}@futa.edu.ng"
            if base not in used_emails:
                used_emails.add(base)
                return base
            for i in range(1, 100):
                candidate = f"{first.lower()}.{last.lower()}{i}@futa.edu.ng"
                if candidate not in used_emails:
                    used_emails.add(candidate)
                    return candidate
            return base

        # --- Fixed accounts (always created first) ---
        fixed_accounts = [
            {
                "email": "covenantcrackslord01@gmail.com",
                "password": "watermelon",
                "role": User.Role.ALUMNI,
                "firstname": "Covenant",
                "lastname": "Crackslord",
                "gender": "male",
                "dept": "Computer Science",
                "faculty": "Engineering and Technology",
                "state": "Lagos",
                "grad_year": "2019",
                "industry": "Technology",
                "job_title": "Full Stack Developer",
                "company": "Andela",
                "years_exp": 7,
            },
            {
                "email": "covenantcrackslord02@gmail.com",
                "password": "watermelon",
                "role": User.Role.STUDENT,
                "firstname": "Covenant",
                "lastname": "Crackslord",
                "gender": "male",
                "dept": "Computer Science",
                "faculty": "Engineering and Technology",
                "state": "Lagos",
                "level": 400,
                "cgpa": 4.50,
                "skills": ["Python", "Django", "React", "JavaScript", "PostgreSQL"],
            },
            {
                "email": "davidpraise100@gmail.com",
                "password": "Rato123$",
                "role": User.Role.ALUMNI,
                "firstname": "David",
                "lastname": "Praise",
                "gender": "male",
                "dept": "Information Technology",
                "faculty": "Engineering and Technology",
                "state": "Ogun",
                "grad_year": "2020",
                "industry": "Finance",
                "job_title": "Backend Engineer",
                "company": "Flutterwave",
                "years_exp": 6,
            },
            {
                "email": "oliverpraise1@gmail.com",
                "password": "Rato123$",
                "role": User.Role.STUDENT,
                "firstname": "Oliver",
                "lastname": "Praise",
                "gender": "male",
                "dept": "Electrical and Electronics Engineering",
                "faculty": "Engineering and Technology",
                "state": "Abuja",
                "level": 300,
                "cgpa": 4.10,
                "skills": ["Java", "C++", "SQL", "Machine Learning", "Linux"],
            },
        ]

        for acct in fixed_accounts:
            used_emails.add(acct["email"])

        # Create fixed alumni users + profiles
        fixed_alumni_users = []
        for acct in fixed_accounts:
            if acct["role"] != User.Role.ALUMNI:
                continue
            user = User(
                email=acct["email"],
                role=User.Role.ALUMNI,
                is_active=True,
                is_staff=False,
            )
            user.set_password(acct["password"])
            user.save()
            AlumniProfile.objects.create(
                user=user,
                phone_num=random_phone_number(),
                gender=acct["gender"],
                firstname=acct["firstname"],
                lastname=acct["lastname"],
                middlename="",
                address="12 Allen Avenue, Ikeja, Lagos",
                state=acct["state"],
                country="Nigeria",
                description="Passionate tech professional with a love for building impactful products.",
                matric_no=random_matric_number(int(acct["grad_year"]), DEPT_CODES.get(acct["dept"], "CS")),
                department=acct["dept"],
                faculty=acct["faculty"],
                grad_year=acct["grad_year"],
                current_job_title=acct["job_title"],
                current_company=acct["company"],
                industry=acct["industry"],
                years_of_exp=acct["years_exp"],
                previous_comps=[],
                linkedin_url=f"https://www.linkedin.com/in/{acct['firstname'].lower()}-{acct['lastname'].lower()}",
            )
            fixed_alumni_users.append(user)
            self.stdout.write(f"    Created fixed alumni: {acct['email']}")

        # Create fixed student users + profiles
        fixed_student_users = []
        for acct in fixed_accounts:
            if acct["role"] != User.Role.STUDENT:
                continue
            user = User(
                email=acct["email"],
                role=User.Role.STUDENT,
                is_active=True,
                is_staff=False,
            )
            user.set_password(acct["password"])
            user.save()
            StudentProfile.objects.create(
                user=user,
                phone_num=random_phone_number(),
                gender=acct["gender"],
                firstname=acct["firstname"],
                lastname=acct["lastname"],
                middlename="",
                address="45 Adetokunbo Ademola Cr, Wuse, Abuja",
                state=acct["state"],
                country="Nigeria",
                description="Motivated student eager to learn and grow in tech.",
                matric_no=random_matric_number(2022, DEPT_CODES.get(acct["dept"], "CS")),
                department=acct["dept"],
                faculty=acct["faculty"],
                level=acct["level"],
                cgpa=Decimal(str(acct["cgpa"])),
                skills=acct["skills"],
                expected_grad_year=str(2026 + (700 - acct["level"]) // 100),
                willingness_to_be_mentored=True,
                linkedin_url=f"https://www.linkedin.com/in/{acct['firstname'].lower()}-{acct['lastname'].lower()}",
            )
            fixed_student_users.append(user)
            self.stdout.write(f"    Created fixed student: {acct['email']}")

        # --- Alumni ---
        self.stdout.write("  Creating 50 alumni...")
        alumni_batch = []
        for i in range(50):
            gender = random.choice(["male", "female"])
            first = random.choice(
                FIRST_NAMES_MALE if gender == "male" else FIRST_NAMES_FEMALE
            )
            last = random.choice(LAST_NAMES)
            email = make_email(first, last)
            dept, faculty = random.choice(FUTA_DEPARTMENTS)
            state = random.choice(NIGERIAN_STATES)
            grad_year = str(random.randint(2015, 2023))
            industry = random.choice(INDUSTRIES)

            user = User(
                email=email,
                role=User.Role.ALUMNI,
                is_active=True,
                is_staff=False,
            )
            user.set_password("seedpass123")
            alumni_batch.append(
                (user, first, last, gender, dept, faculty, state, grad_year, industry)
            )

        created_alumni = User.objects.bulk_create([u for u, *_ in alumni_batch])
        self.stdout.write(f"    Created {len(created_alumni)} alumni users")

        alumni_profile_batch = []
        for i, (
            user,
            first,
            last,
            gender,
            dept,
            faculty,
            state,
            grad_year,
            industry,
        ) in enumerate(alumni_batch):
            company_list = COMPANIES.get(industry, DEFAULT_COMPANIES)
            job_titles = {
                "Technology": [
                    "Software Engineer",
                    "DevOps Engineer",
                    "Data Scientist",
                    "Product Manager",
                    "Backend Developer",
                    "Frontend Developer",
                    "ML Engineer",
                ],
                "Finance": [
                    "Financial Analyst",
                    "Investment Banker",
                    "Risk Analyst",
                    "Portfolio Manager",
                    "Accountant",
                ],
                "Consulting": [
                    "Management Consultant",
                    "Strategy Analyst",
                    "Business Analyst",
                    "Senior Consultant",
                ],
                "Healthcare": [
                    "Health Informatics Specialist",
                    "Clinical Data Analyst",
                    "Public Health Officer",
                ],
                "Energy": [
                    "Petroleum Engineer",
                    "Energy Analyst",
                    "Project Engineer",
                    "Operations Manager",
                ],
                "Telecommunications": [
                    "Network Engineer",
                    "Systems Engineer",
                    "Solutions Architect",
                    "Telecom Analyst",
                ],
                "Manufacturing": [
                    "Production Engineer",
                    "Quality Assurance Engineer",
                    "Process Engineer",
                    "Plant Manager",
                ],
                "Education": [
                    "Lecturer",
                    "Research Fellow",
                    "Academic Advisor",
                    "Education Consultant",
                ],
                "E-commerce": [
                    "Growth Manager",
                    "Product Designer",
                    "Logistics Coordinator",
                    "UX Researcher",
                ],
                "Media": [
                    "Content Producer",
                    "Digital Marketing Specialist",
                    "Editor",
                    "Journalist",
                ],
                "Logistics": [
                    "Supply Chain Analyst",
                    "Operations Manager",
                    "Logistics Coordinator",
                    "Fleet Manager",
                ],
            }
            titles = job_titles.get(
                industry, ["Professional", "Analyst", "Manager", "Specialist"]
            )
            job_title = random.choice(titles)
            years_exp = random.randint(2, 12)
            company = random.choice(company_list)
            company_url = (
                f"https://www.linkedin.com/company/{company.lower().replace(' ', '-')}"
            )
            company_web = f"https://www.{company.lower().replace(' ', '')}.com"

            profile = AlumniProfile(
                user=user,
                phone_num=random_phone_number(),
                gender=gender,
                firstname=first,
                lastname=last,
                middlename=random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
                if random.random() > 0.5
                else "",
                address=f"{random.randint(1, 200)} {random.choice(['Street', 'Road', 'Avenue', 'Close', 'Drive'])}, "
                f"{self.faker.city()}, {state}",
                state=state,
                country="Nigeria",
                description=self.faker.paragraph(nb_sentences=2)
                if random.random() > 0.3
                else "",
                matric_no=random_matric_number(
                    int(grad_year), DEPT_CODES.get(dept, "XX")
                ),
                department=dept,
                faculty=faculty,
                grad_year=grad_year,
                current_job_title=job_title,
                current_company=company,
                industry=industry,
                years_of_exp=years_exp,
                previous_comps=random.sample(
                    company_list, min(random.randint(0, 2), len(company_list))
                ),
                linkedin_url=f"https://www.linkedin.com/in/{first.lower()}-{last.lower()}",
                company_linkedin_url=company_url if random.random() > 0.3 else None,
                github_url=f"https://github.com/{first.lower()}{last.lower()}"
                if random.random() > 0.5
                else None,
                website_url=company_web if random.random() > 0.6 else None,
                company_website_url=company_web if random.random() > 0.4 else None,
                x_url=f"https://x.com/{first.lower()}{last.lower()}"
                if random.random() > 0.4
                else None,
                instagram_url=f"https://instagram.com/{first.lower()}.{last.lower()}"
                if random.random() > 0.7
                else None,
                facebook_url=None,
            )
            alumni_profile_batch.append(profile)

        created_profiles = AlumniProfile.objects.bulk_create(alumni_profile_batch)
        self.stdout.write(f"    Created {len(created_profiles)} alumni profiles")

        # Refresh to get IDs
        self.alumni_users = list(
            User.objects.filter(role=User.Role.ALUMNI, is_active=True)
        )
        self.alumni_profiles = list(AlumniProfile.objects.select_related("user").all())

        # --- Students ---
        self.stdout.write("  Creating 80 students...")
        student_batch = []
        for i in range(80):
            gender = random.choice(["male", "female"])
            first = random.choice(
                FIRST_NAMES_MALE if gender == "male" else FIRST_NAMES_FEMALE
            )
            last = random.choice(LAST_NAMES)
            email = make_email(first, last)
            dept, faculty = random.choice(FUTA_DEPARTMENTS)
            state = random.choice(NIGERIAN_STATES)
            level = weighted_choice(
                [100, 200, 300, 400, 500],
                [10, 25, 35, 20, 10],
            )
            cgpa = round(random.uniform(2.5, 5.0), 2)

            user = User(
                email=email,
                role=User.Role.STUDENT,
                is_active=True,
                is_staff=False,
            )
            user.set_password("seedpass123")
            student_batch.append(
                (user, first, last, gender, dept, faculty, state, level, cgpa)
            )

        created_students = User.objects.bulk_create([u for u, *_ in student_batch])
        self.stdout.write(f"    Created {len(created_students)} student users")

        student_profile_batch = []
        for i, (
            user,
            first,
            last,
            gender,
            dept,
            faculty,
            state,
            level,
            cgpa,
        ) in enumerate(student_batch):
            grad_year = str(2026 + (700 - level) // 100)
            num_skills = random.randint(3, 8)
            skills = random.sample(ALL_SKILLS, min(num_skills, len(ALL_SKILLS)))

            profile = StudentProfile(
                user=user,
                phone_num=random_phone_number(),
                gender=gender,
                firstname=first,
                lastname=last,
                middlename=random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
                if random.random() > 0.5
                else "",
                address=f"{random.randint(1, 200)} {random.choice(['Street', 'Road', 'Avenue', 'Close', 'Drive'])}, "
                f"{self.faker.city()}, {state}",
                state=state,
                country="Nigeria",
                description=self.faker.paragraph(nb_sentences=2)
                if random.random() > 0.4
                else "",
                matric_no=random_matric_number(
                    int(grad_year) - 4, DEPT_CODES.get(dept, "XX")
                ),
                department=dept,
                faculty=faculty,
                level=level,
                cgpa=Decimal(str(cgpa)),
                skills=skills,
                expected_grad_year=grad_year,
                preferred_industry=random.choice(INDUSTRIES)
                if random.random() > 0.3
                else None,
                preferred_company_type=random.choice(
                    ["Tech", "Finance", "Startup", "Enterprise", "NGO"]
                )
                if random.random() > 0.4
                else None,
                willingness_to_be_mentored=random.random() > 0.2,
                linkedin_url=f"https://www.linkedin.com/in/{first.lower()}-{last.lower()}"
                if random.random() > 0.4
                else None,
                github_url=f"https://github.com/{first.lower()}{last.lower()}"
                if random.random() > 0.5
                else None,
                x_url=f"https://x.com/{first.lower()}{last.lower()}"
                if random.random() > 0.5
                else None,
            )
            student_profile_batch.append(profile)

        created_s_profiles = StudentProfile.objects.bulk_create(student_profile_batch)
        self.stdout.write(f"    Created {len(created_s_profiles)} student profiles")

        self.student_users = list(
            User.objects.filter(role=User.Role.STUDENT, is_active=True)
        )
        self.student_profiles = list(
            StudentProfile.objects.select_related("user").all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"  Batch 1 complete: {len(self.alumni_users)} alumni + {len(self.student_users)} students"
            )
        )

    # ==================================================================
    # BATCH 2: Listings (Internships + Mentorships)
    # ==================================================================

    def batch_listings(self):
        from internships.models import Internship
        from mentorships.models import Mentorship

        # --- Internships ---
        self.stdout.write("  Creating 120 internships...")
        internship_batch = []
        alumni_profiles = self.alumni_profiles

        for i in range(120):
            alumnus = random.choice(alumni_profiles)
            title = random.choice(INTERNSHIP_TITLES)
            industry = alumnus.industry
            company_list = COMPANIES.get(industry, DEFAULT_COMPANIES)
            company = random.choice(company_list)
            work_mode = random.choice(WORK_MODES)
            engagement_type = random.choice(ENGAGEMENT_TYPES)

            start = random_date_in_past(max_months_ago=6, min_days_ago=30)
            duration = random.choice([4, 6, 8, 10, 12, 16, 24])
            end = start + timedelta(weeks=duration)

            is_paid = random.random() > 0.35
            stipend = (
                Decimal(
                    str(
                        random.choice(
                            [
                                50000,
                                75000,
                                100000,
                                120000,
                                150000,
                                200000,
                                250000,
                                300000,
                            ]
                        )
                    )
                )
                if is_paid
                else None
            )

            dept, faculty = random.choice(FUTA_DEPARTMENTS)
            skills = random.sample(TECH_SKILLS, random.randint(2, 6))
            levels = random.sample([100, 200, 300, 400, 500], random.randint(1, 3))

            desc_template = random.choice(INTERNSHIP_DESCRIPTION_TEMPLATES)
            description = desc_template.format(
                company=company,
                title=title,
                skills=", ".join(skills[:3]),
                level=levels[0],
                industry=industry.lower(),
                department=dept.lower(),
                tasks=random.choice(INTERNSHIP_TASKS),
                weeks=duration,
                field=dept,
                work_mode=work_mode.lower(),
            )

            slots = random.choice([1, 2, 3, 5, 8, 10, 15])
            taken = random.randint(0, max(0, slots - 1))

            internship_batch.append(
                Internship(
                    alumnus=alumnus,
                    title=title,
                    description=description,
                    work_mode=work_mode,
                    engagement_type=engagement_type,
                    location=self.faker.city() if work_mode != "Remote" else "Remote",
                    skills_required=skills,
                    duration_weeks=duration,
                    start_date=start,
                    end_date=end,
                    is_paid=is_paid,
                    stipend=stipend,
                    levels=levels,
                    company=company,
                    company_type=random.choice(
                        ["Startup", "Enterprise", "Agency", "NGO"]
                    ),
                    industry=industry,
                    company_linkedin_url=f"https://www.linkedin.com/company/{company.lower().replace(' ', '-')}"
                    if random.random() > 0.3
                    else None,
                    company_website_url=f"https://www.{company.lower().replace(' ', '')}.com"
                    if random.random() > 0.3
                    else None,
                    available_slots=slots,
                    remaining_slots=max(0, slots - taken),
                    is_active=random.random() > 0.15,
                    require_resume=random.random() > 0.2,
                    require_cover_letter=random.random() > 0.5,
                )
            )

        created_internships = Internship.objects.bulk_create(internship_batch)
        self.stdout.write(f"    Created {len(created_internships)} internships")
        self.internships = list(
            Internship.objects.select_related("alumnus__user").all()
        )

        # --- Mentorships ---
        self.stdout.write("  Creating 80 mentorships...")
        mentorship_batch = []

        for i in range(80):
            alumnus = random.choice(alumni_profiles)
            title = random.choice(MENTORSHIP_TITLES)
            category = random.choice(MENTORSHIP_CATEGORIES)
            focus_areas = random.sample(MENTORSHIP_FOCUS_AREAS, random.randint(1, 4))
            work_mode = random.choice(["Remote", "Hybrid", "Onsite"])

            start = random_date_in_past(max_months_ago=5, min_days_ago=20)
            duration = random.choice([4, 6, 8, 10, 12])
            end = start + timedelta(weeks=duration)

            desc_template = random.choice(MENTORSHIP_DESCRIPTION_TEMPLATES)
            description = desc_template.format(
                focus_area=focus_areas[0].replace("_", " "),
                weeks=duration,
                topics=", ".join([f.replace("_", " ") for f in focus_areas]),
                industry=alumnus.industry.lower(),
                category=category.replace("_", " "),
                level=weighted_choice([100, 200, 300], [20, 40, 40]),
            )

            slots = random.choice([1, 2, 3, 5, 8])
            taken = random.randint(0, max(0, slots - 1))

            mentorship_batch.append(
                Mentorship(
                    alumnus=alumnus,
                    title=title,
                    description=description,
                    category=category,
                    focus_areas=focus_areas,
                    work_mode=work_mode,
                    duration_weeks=duration,
                    start_date=start,
                    end_date=end,
                    available_slots=slots,
                    remaining_slots=max(0, slots - taken),
                    is_active=random.random() > 0.15,
                )
            )

        created_mentorships = Mentorship.objects.bulk_create(mentorship_batch)
        self.stdout.write(f"    Created {len(created_mentorships)} mentorships")
        self.mentorships = list(
            Mentorship.objects.select_related("alumnus__user").all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"  Batch 2 complete: {len(self.internships)} internships + {len(self.mentorships)} mentorships"
            )
        )

    # ==================================================================
    # BATCH 3: Applications
    # ==================================================================

    def batch_applications(self):
        from engagements.models import EngagementLifecycleStatus
        from internships.models import InternshipApplication
        from mentorships.models import MentorshipApplication

        statuses = [
            EngagementLifecycleStatus.PENDING,
            EngagementLifecycleStatus.ACCEPTED,
            EngagementLifecycleStatus.REJECTED,
            EngagementLifecycleStatus.WITHDRAWN,
        ]
        status_weights = [0.25, 0.30, 0.25, 0.20]

        # --- Internship Applications ---
        self.stdout.write("  Creating 200 internship applications...")
        app_batch = []
        used_pairs = set()

        for i in range(200):
            student = random.choice(self.student_profiles)
            internship = random.choice(self.internships)
            pair = (student.id, internship.id)
            if pair in used_pairs:
                continue
            used_pairs.add(pair)

            status = weighted_choice(statuses, status_weights)
            responded_at = (
                random_date_in_past(max_months_ago=5, min_days_ago=5)
                if status != EngagementLifecycleStatus.PENDING
                else None
            )

            app_batch.append(
                InternshipApplication(
                    internship=internship,
                    student=student,
                    status=status,
                    responded_at=responded_at,
                    cover_letter=self.faker.paragraph(nb_sentences=3)
                    if random.random() > 0.3
                    else "",
                )
            )

        created_apps = InternshipApplication.objects.bulk_create(app_batch)
        self.stdout.write(f"    Created {len(created_apps)} internship applications")
        self.internship_apps = list(
            InternshipApplication.objects.select_related(
                "internship", "student__user"
            ).all()
        )

        # --- Mentorship Applications ---
        self.stdout.write("  Creating 120 mentorship applications...")
        mapp_batch = []
        used_mpairs = set()

        for i in range(120):
            student = random.choice(self.student_profiles)
            mentorship = random.choice(self.mentorships)
            pair = (student.id, mentorship.id)
            if pair in used_mpairs:
                continue
            used_mpairs.add(pair)

            status = weighted_choice(statuses, status_weights)
            responded_at = (
                random_date_in_past(max_months_ago=4, min_days_ago=5)
                if status != EngagementLifecycleStatus.PENDING
                else None
            )

            mapp_batch.append(
                MentorshipApplication(
                    mentorship=mentorship,
                    student=student,
                    status=status,
                    responded_at=responded_at,
                    cover_letter=self.faker.paragraph(nb_sentences=3),
                )
            )

        created_mapps = MentorshipApplication.objects.bulk_create(mapp_batch)
        self.stdout.write(f"    Created {len(created_mapps)} mentorship applications")
        self.mentorship_apps = list(
            MentorshipApplication.objects.select_related(
                "mentorship", "student__user"
            ).all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"  Batch 3 complete: {len(self.internship_apps)} + {len(self.mentorship_apps)} applications"
            )
        )

    # ==================================================================
    # BATCH 4: Offers
    # ==================================================================

    def batch_offers(self):
        from engagements.models import EngagementLifecycleStatus
        from internships.models import InternshipOffer
        from mentorships.models import MentorshipOffer

        statuses = [
            EngagementLifecycleStatus.PENDING,
            EngagementLifecycleStatus.ACCEPTED,
            EngagementLifecycleStatus.REJECTED,
        ]
        status_weights = [0.30, 0.50, 0.20]

        # --- Internship Offers ---
        self.stdout.write("  Creating 60 internship offers...")
        offer_batch = []
        used_pairs = set()

        # Create offers from accepted internship applications
        accepted_apps = [
            a
            for a in self.internship_apps
            if a.status == EngagementLifecycleStatus.ACCEPTED
        ]
        for app in accepted_apps[:40]:
            pair = (app.student_id, app.internship_id)
            if pair in used_pairs:
                continue
            used_pairs.add(pair)
            offer_batch.append(
                InternshipOffer(
                    internship=app.internship,
                    student=app.student,
                    status=EngagementLifecycleStatus.ACCEPTED,
                    responded_at=random_date_in_past(max_months_ago=4, min_days_ago=5),
                )
            )

        # Fill remaining with new offers
        for i in range(max(0, 60 - len(offer_batch))):
            student = random.choice(self.student_profiles)
            internship = random.choice(self.internships)
            pair = (student.id, internship.id)
            if pair in used_pairs:
                continue
            used_pairs.add(pair)

            status = weighted_choice(statuses, status_weights)
            responded_at = (
                random_date_in_past(max_months_ago=4, min_days_ago=5)
                if status != EngagementLifecycleStatus.PENDING
                else None
            )

            offer_batch.append(
                InternshipOffer(
                    internship=internship,
                    student=student,
                    status=status,
                    responded_at=responded_at,
                )
            )

        created_offers = InternshipOffer.objects.bulk_create(offer_batch)
        self.stdout.write(f"    Created {len(created_offers)} internship offers")
        self.internship_offers = list(
            InternshipOffer.objects.select_related("internship", "student__user").all()
        )

        # --- Mentorship Offers ---
        self.stdout.write("  Creating 40 mentorship offers...")
        moffer_batch = []
        used_mpairs = set()

        accepted_mapps = [
            a
            for a in self.mentorship_apps
            if a.status == EngagementLifecycleStatus.ACCEPTED
        ]
        for app in accepted_mapps[:25]:
            pair = (app.student_id, app.mentorship_id)
            if pair in used_mpairs:
                continue
            used_mpairs.add(pair)
            moffer_batch.append(
                MentorshipOffer(
                    mentorship=app.mentorship,
                    student=app.student,
                    status=EngagementLifecycleStatus.ACCEPTED,
                    responded_at=random_date_in_past(max_months_ago=3, min_days_ago=5),
                )
            )

        for i in range(max(0, 40 - len(moffer_batch))):
            student = random.choice(self.student_profiles)
            mentorship = random.choice(self.mentorships)
            pair = (student.id, mentorship.id)
            if pair in used_mpairs:
                continue
            used_mpairs.add(pair)

            status = weighted_choice(statuses, status_weights)
            responded_at = (
                random_date_in_past(max_months_ago=3, min_days_ago=5)
                if status != EngagementLifecycleStatus.PENDING
                else None
            )

            moffer_batch.append(
                MentorshipOffer(
                    mentorship=mentorship,
                    student=student,
                    status=status,
                    responded_at=responded_at,
                )
            )

        created_moffers = MentorshipOffer.objects.bulk_create(moffer_batch)
        self.stdout.write(f"    Created {len(created_moffers)} mentorship offers")
        self.mentorship_offers = list(
            MentorshipOffer.objects.select_related("mentorship", "student__user").all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"  Batch 4 complete: {len(self.internship_offers)} + {len(self.mentorship_offers)} offers"
            )
        )

    # ==================================================================
    # BATCH 5: Engagements
    # ==================================================================

    def batch_engagements(self):
        from engagements.models import Engagement, EngagementLifecycleStatus
        from engagements.services import create_engagement

        engagement_statuses = [
            Engagement.EngagementStatus.ACTIVE,
            Engagement.EngagementStatus.COMPLETED,
            Engagement.EngagementStatus.ACKNOWLEDGED,
            Engagement.EngagementStatus.TERMINATED,
        ]
        status_weights = [0.35, 0.40, 0.15, 0.10]

        self.stdout.write("  Creating 100 engagements...")
        engagement_count = 0
        used_engagement_pairs = set()

        # From accepted internship offers
        accepted_io = [
            o
            for o in self.internship_offers
            if o.status == EngagementLifecycleStatus.ACCEPTED
        ]
        for offer in accepted_io[:50]:
            pair = (offer.student_id, offer.internship_id)
            if pair in used_engagement_pairs:
                continue
            used_engagement_pairs.add(pair)

            status = weighted_choice(engagement_statuses, status_weights)
            try:
                engagement = create_engagement(
                    engagement_type=Engagement.EngagementType.INTERNSHIP,
                    student=offer.student,
                    alumnus=offer.internship.alumnus,
                    offer=offer,
                )
                engagement.status = status
                engagement.save(update_fields=["status"])
                engagement_count += 1
            except Exception:
                continue

        # From accepted mentorship offers
        accepted_mo = [
            o
            for o in self.mentorship_offers
            if o.status == EngagementLifecycleStatus.ACCEPTED
        ]
        for offer in accepted_mo[:30]:
            pair = (offer.student_id, offer.mentorship_id)
            if pair in used_engagement_pairs:
                continue
            used_engagement_pairs.add(pair)

            status = weighted_choice(engagement_statuses, status_weights)
            try:
                engagement = create_engagement(
                    engagement_type=Engagement.EngagementType.MENTORSHIP,
                    student=offer.student,
                    alumnus=offer.mentorship.alumnus,
                    offer=offer,
                )
                engagement.status = status
                engagement.save(update_fields=["status"])
                engagement_count += 1
            except Exception:
                continue

        # From accepted internship applications (not already covered by offers)
        accepted_ia = [
            a
            for a in self.internship_apps
            if a.status == EngagementLifecycleStatus.ACCEPTED
        ]
        for app in accepted_ia:
            if engagement_count >= 100:
                break
            pair = (app.student_id, app.internship_id)
            if pair in used_engagement_pairs:
                continue
            used_engagement_pairs.add(pair)

            status = weighted_choice(engagement_statuses, status_weights)
            try:
                engagement = create_engagement(
                    engagement_type=Engagement.EngagementType.INTERNSHIP,
                    student=app.student,
                    alumnus=app.internship.alumnus,
                    application=app,
                )
                engagement.status = status
                engagement.save(update_fields=["status"])
                engagement_count += 1
            except Exception:
                continue

        # From accepted mentorship applications
        accepted_ma = [
            a
            for a in self.mentorship_apps
            if a.status == EngagementLifecycleStatus.ACCEPTED
        ]
        for app in accepted_ma:
            if engagement_count >= 100:
                break
            pair = (app.student_id, app.mentorship_id)
            if pair in used_engagement_pairs:
                continue
            used_engagement_pairs.add(pair)

            status = weighted_choice(engagement_statuses, status_weights)
            try:
                engagement = create_engagement(
                    engagement_type=Engagement.EngagementType.MENTORSHIP,
                    student=app.student,
                    alumnus=app.mentorship.alumnus,
                    application=app,
                )
                engagement.status = status
                engagement.save(update_fields=["status"])
                engagement_count += 1
            except Exception:
                continue

        self.engagements = list(
            Engagement.objects.select_related("student__user", "alumnus__user").all()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"  Batch 5 complete: {engagement_count} engagements created"
            )
        )

    # ==================================================================
    # BATCH 6: Events + Tickets + Virtual Meetings
    # ==================================================================

    def batch_events(self):
        from events.models import Event, Ticket, VirtualMeeting

        self.stdout.write("  Creating 40 events...")
        all_users = self.alumni_users + self.student_users
        event_batch = []

        for i in range(40):
            creator = random.choice(all_users)
            title = random.choice(EVENT_TITLES)
            category = random.choice(EVENT_CATEGORIES)
            mode = random.choice(EVENT_MODES)

            event_date = (
                random_date_in_past(max_months_ago=4, min_days_ago=3)
                if random.random() > 0.3
                else random_future_date(max_months_ahead=2)
            )
            start_time = time(
                hour=random.choice([9, 10, 11, 13, 14, 15, 16]),
                minute=random.choice([0, 30]),
            )
            duration = random.choice([60, 90, 120, 180, 240, 360])

            venue = None
            if mode in ("physical", "hybrid"):
                venue_options = [
                    "FUTA Auditorium",
                    "FUTA Engineering Hall",
                    "FUTA Senate Building",
                    "FUTA Library Complex",
                    "FUTA Sports Center",
                    "FUTA ICT Center",
                    "FUTA New Hall",
                    "FUTA Staff Club",
                    "FUTA Vice-Chancellor's Lodge",
                ]
                venue = random.choice(venue_options)

            description = self.faker.paragraph(nb_sentences=4)
            max_cap = random.choice([50, 100, 150, 200, 300, 500, None])

            event_batch.append(
                Event(
                    creator=creator,
                    title=title,
                    description=description,
                    category=category,
                    mode=mode,
                    venue=venue,
                    date=event_date,
                    start_time=start_time,
                    duration_mins=duration,
                    max_capacity=max_cap,
                    allow_sponsorship=random.random() > 0.7,
                    allow_donations=random.random() > 0.8,
                    is_cancelled=False,
                    is_published=random.random() > 0.1,
                )
            )

        created_events = Event.objects.bulk_create(event_batch)
        self.stdout.write(f"    Created {len(created_events)} events")
        self.events = list(Event.objects.select_related("creator").all())

        # --- Tickets ---
        self.stdout.write("  Creating tickets...")
        ticket_batch = []
        for event in self.events:
            num_tickets = random.choice([1, 1, 2])
            for t in range(num_tickets):
                is_free = random.random() > 0.6
                price = (
                    Decimal(0)
                    if is_free
                    else Decimal(
                        str(
                            random.choice([1000, 2000, 3000, 5000, 10000, 15000, 20000])
                        )
                    )
                )
                qty = random.choice([None, 50, 100, 200, 300])
                discount = Decimal(str(random.choice([0, 0, 0, 5, 10, 15, 20])))

                ticket_batch.append(
                    Ticket(
                        event=event,
                        name=f"{'Free' if is_free else 'Standard'} Ticket"
                        if t == 0
                        else f"{'VIP Free' if is_free else 'VIP'} Ticket",
                        description=f"{'Free' if is_free else 'Standard'} entry"
                        if t == 0
                        else "VIP access with priority seating",
                        price=price,
                        discount_perc=discount,
                        quantity=qty,
                        quantity_sold=random.randint(0, min(30, qty or 30)),
                        type="default" if t == 0 and is_free else "custom",
                        sales_start=timezone.make_aware(
                            datetime.combine(event.date - timedelta(days=30), time(0, 0))
                        ),
                        sales_end=timezone.make_aware(
                            datetime.combine(event.date - timedelta(days=1), time(23, 59))
                        )
                        if random.random() > 0.3
                        else None,
                        is_active=True,
                    )
                )

        created_tickets = Ticket.objects.bulk_create(ticket_batch)
        self.stdout.write(f"    Created {len(created_tickets)} tickets")

        # --- Virtual Meetings ---
        self.stdout.write("  Creating virtual meetings...")
        vm_batch = []
        for event in self.events:
            if event.mode in ("virtual", "hybrid"):
                platform = random.choice(["meet", "jitsi"])
                if platform == "meet":
                    slug = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=3)) + "-" + \
                           "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=4)) + "-" + \
                           "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=3))
                    join_url = f"https://meet.google.com/{slug}"
                else:
                    slug = event.title.title().replace(" ", "-")[:40]
                    join_url = f"https://meet.jit.si/{slug}"
                vm_batch.append(
                    VirtualMeeting(
                        event=event,
                        platform=platform,
                        join_url=join_url,
                        room_name=slug,
                    )
                )

        VirtualMeeting.objects.bulk_create(vm_batch)
        self.stdout.write(f"    Created {len(vm_batch)} virtual meetings")

        self.stdout.write(
            self.style.SUCCESS(
                f"  Batch 6 complete: {len(self.events)} events, {len(created_tickets)} tickets, {len(vm_batch)} VMs"
            )
        )

    # ==================================================================
    # BATCH 7: Posts + Notifications
    # ==================================================================

    def batch_social(self):
        from notifications.models import Notification
        from posts.models import Post

        all_users = self.alumni_users + self.student_users

        # --- Posts ---
        self.stdout.write("  Creating 150 posts...")
        post_batch = []

        # Posts from engagements
        for engagement in self.engagements[:80]:
            user = engagement.student.user
            post_type = weighted_choice(
                ["engagement_started", "engagement_completed", "milestone"],
                [0.3, 0.3, 0.4],
            )

            templates = {
                "engagement_started": POST_STARTER_TEMPLATES,
                "engagement_completed": POST_COMPLETION_TEMPLATES,
                "milestone": POST_MILESTONE_TEMPLATES,
            }
            template = random.choice(templates[post_type])

            detail = engagement.detail
            context = {}
            if hasattr(detail, "internship"):
                context = {
                    "company": detail.internship.company,
                    "title": detail.internship.title,
                    "skill": random.choice(
                        detail.internship.skills_required or ["tech"]
                    ),
                    "weeks": detail.internship.duration_weeks,
                }
            elif hasattr(detail, "mentorship"):
                context = {
                    "company": "mentoring",
                    "title": detail.mentorship.title,
                    "skill": random.choice(detail.mentorship.focus_areas or ["career"]),
                    "weeks": detail.mentorship.duration_weeks or 8,
                }

            try:
                content = template.format(**context)
            except KeyError:
                content = self.faker.paragraph(nb_sentences=2)

            post_batch.append(
                Post(
                    author=user,
                    post_type=post_type,
                    content=content,
                    is_public=True,
                )
            )

        # General milestone posts
        milestone_templates = [
            "Just hit CGPA {cgpa}! Hard work pays off.",
            "Completed my NYSC at {company}. What an experience!",
            "Passed my certification exam! {skill} level: certified.",
            "Won first place at the {event} hackathon!",
            "Got accepted into the {program} fellowship program!",
            "Published my first research paper on {topic}!",
            "Reached 1000 followers on GitHub. Open source is life.",
            "Started learning {skill} 3 months ago. Today I built my first project.",
            "My team just shipped v2.0 of our product. {weeks} months of hard work!",
            "Awarded Best Intern at {company} for Q{quarter}. Grateful!",
        ]

        for i in range(70):
            user = random.choice(all_users)
            template = random.choice(milestone_templates)
            content = template.format(
                cgpa=f"{random.uniform(3.5, 5.0):.2f}",
                company=random.choice(COMPANIES.get("Technology", DEFAULT_COMPANIES)),
                skill=random.choice(TECH_SKILLS),
                event=random.choice(["FUTA", "Tech", "Innovation"]),
                program=random.choice(["Andela", "MLH", "Google", "Microsoft"]),
                topic=random.choice(
                    ["AI", "blockchain", "renewable energy", "fintech"]
                ),
                weeks=random.randint(2, 8),
                quarter=random.randint(1, 4),
            )
            post_batch.append(
                Post(
                    author=user,
                    post_type="milestone",
                    content=content,
                    is_public=random.random() > 0.1,
                )
            )

        created_posts = Post.objects.bulk_create(post_batch)
        self.stdout.write(f"    Created {len(created_posts)} posts")

        # --- Notifications ---
        self.stdout.write("  Creating 200 notifications...")
        notif_batch = []

        for i in range(200):
            user = random.choice(all_users)
            title = random.choice(NOTIFICATION_TITLES)
            template = random.choice(NOTIFICATION_CONTENT_TEMPLATES)
            content = template.format(
                type=random.choice(["internship", "mentorship"]),
                title=random.choice(INTERNSHIP_TITLES + MENTORSHIP_TITLES),
                status=random.choice(["accepted", "rejected", "under review"]),
                role=random.choice(["student", "alumnus"]),
                name=self.faker.name(),
                badge=random.choice(
                    ["Rising Star", "Top Mentor", "Active Learner", "Community Builder"]
                ),
            )
            is_read = random.random() > 0.4
            read_at = (
                timezone.now() - timedelta(hours=random.randint(1, 168))
                if is_read
                else None
            )

            notif_batch.append(
                Notification(
                    user=user,
                    title=title,
                    content=content,
                    is_read=is_read,
                    read_at=read_at,
                )
            )

        created_notifs = Notification.objects.bulk_create(notif_batch)
        self.stdout.write(f"    Created {len(created_notifs)} notifications")

        self.stdout.write(
            self.style.SUCCESS(
                f"  Batch 7 complete: {len(created_posts)} posts + {len(created_notifs)} notifications"
            )
        )

    # ==================================================================
    # BATCH 8: Reviews + Feed
    # ==================================================================

    def batch_reviews_feed(self):
        from engagements.models import Engagement
        from engagements.services import default_share_text, get_engagement_post_context
        from events.models import VirtualMeeting
        from feed.models import FeedEvent, FeedImpression, FeedTarget
        from feed.tasks import create_feed_event_task
        from posts.models import Post
        from reviews.models import Review

        all_users = self.alumni_users + self.student_users

        # --- Reviews ---
        self.stdout.write("  Creating 100 reviews...")
        completed = [
            e
            for e in self.engagements
            if e.status == Engagement.EngagementStatus.COMPLETED
        ]
        review_batch = []
        used_review_pairs = set()

        engagement_ct = ContentType.objects.get_for_model(Engagement)

        for engagement in completed[:100]:
            # Student reviews alumnus
            if random.random() > 0.25:
                pair = (
                    engagement.student.user_id,
                    engagement.alumnus.user_id,
                    engagement.id,
                )
                if pair not in used_review_pairs:
                    used_review_pairs.add(pair)
                    rating = round(random.uniform(2.5, 5.0), 2)
                    if rating >= 4.0:
                        text = random.choice(REVIEW_TEXTS_POSITIVE)
                    elif rating >= 3.0:
                        text = random.choice(REVIEW_TEXTS_NEUTRAL)
                    else:
                        text = random.choice(REVIEW_TEXTS_NEGATIVE)

                    review_batch.append(
                        Review(
                            reviewer=engagement.student.user,
                            reviewee=engagement.alumnus.user,
                            source_content_type=engagement_ct,
                            source_object_id=engagement.id,
                            overall_rating=Decimal(str(rating)),
                            review_text=text,
                            metrics={
                                "communication": round(random.uniform(2.0, 5.0), 1),
                                "knowledge": round(random.uniform(2.0, 5.0), 1),
                                "availability": round(random.uniform(2.0, 5.0), 1),
                                "helpfulness": round(random.uniform(2.0, 5.0), 1),
                            },
                            editable_until=timezone.now() + timedelta(days=30),
                        )
                    )

            # Alumnus reviews student
            if random.random() > 0.4:
                pair = (
                    engagement.alumnus.user_id,
                    engagement.student.user_id,
                    engagement.id,
                )
                if pair not in used_review_pairs:
                    used_review_pairs.add(pair)
                    rating = round(random.uniform(3.0, 5.0), 2)
                    text = random.choice(
                        REVIEW_TEXTS_POSITIVE if rating >= 4.0 else REVIEW_TEXTS_NEUTRAL
                    )

                    review_batch.append(
                        Review(
                            reviewer=engagement.alumnus.user,
                            reviewee=engagement.student.user,
                            source_content_type=engagement_ct,
                            source_object_id=engagement.id,
                            overall_rating=Decimal(str(rating)),
                            review_text=text,
                            metrics={
                                "communication": round(random.uniform(2.5, 5.0), 1),
                                "initiative": round(random.uniform(2.5, 5.0), 1),
                                "punctuality": round(random.uniform(2.5, 5.0), 1),
                                "skill_level": round(random.uniform(2.5, 5.0), 1),
                            },
                            editable_until=timezone.now() + timedelta(days=30),
                        )
                    )

            if len(review_batch) >= 100:
                break

        created_reviews = Review.objects.bulk_create(review_batch)
        self.stdout.write(f"    Created {len(created_reviews)} reviews")

        # --- Feed Events ---
        # Use create_feed_event_task exactly like organic creation so FeedTargets
        # are created from each entity's real .feed_targets property.
        self.stdout.write("  Creating feed events...")

        # Pre-fetch virtual meetings for event data
        virtual_meetings = {
            vm.event_id: vm.platform
            for vm in VirtualMeeting.objects.filter(
                event_id__in=[e.id for e in self.events[:40]]
            )
        }

        feed_event_count = 0

        for internship in self.internships[:80]:
            create_feed_event_task(
                event_type=FeedEvent.EventType.INTERNSHIP_CREATED,
                related_object_id=internship.id,
                related_model="internship",
                audience=FeedEvent.Audience.STUDENT,
                data={
                    "title": internship.title,
                    "alumni": internship.alumnus.full_name,
                    "work_mode": internship.work_mode,
                    "engagement_type": internship.engagement_type,
                    "stipend": str(internship.stipend),
                    "is_paid": internship.is_paid,
                    "available_slots": internship.available_slots,
                    "remaining_slots": internship.remaining_slots,
                    "created_at": internship.created_at.isoformat(),
                },
                score=random.randint(0, 10),
            )
            feed_event_count += 1

        for mentorship in self.mentorships[:60]:
            create_feed_event_task(
                event_type=FeedEvent.EventType.MENTORSHIP_CREATED,
                related_object_id=mentorship.id,
                related_model="mentorship",
                audience=FeedEvent.Audience.PUBLIC,
                data={
                    "title": mentorship.title,
                    "alumni": mentorship.alumnus.full_name,
                    "category": mentorship.category,
                    "available_slots": mentorship.available_slots,
                    "remaining_slots": mentorship.remaining_slots,
                    "created_at": mentorship.created_at.isoformat(),
                },
                score=random.randint(0, 10),
            )
            feed_event_count += 1

        for event in self.events[:40]:
            event_data = {
                "title": event.title,
                "alumni": event.creator.full_name,
                "mode": event.mode,
                "category": event.category,
                "date": event.date.isoformat(),
                "created_at": event.created_at.isoformat(),
            }
            vm_platform = virtual_meetings.get(event.id)
            if vm_platform:
                event_data["virtual_meeting"] = vm_platform

            create_feed_event_task(
                event_type=FeedEvent.EventType.EVENT_CREATED,
                related_object_id=event.id,
                related_model="event",
                audience=FeedEvent.Audience.STUDENT,
                data=event_data,
                score=random.randint(0, 10),
            )
            feed_event_count += 1

        for engagement in self.engagements[:60]:
            detail = engagement.detail
            post_context = getattr(detail, "post_context", {}) if detail else {}

            if random.random() < 0.7:
                context = get_engagement_post_context(engagement)
                default_text = default_share_text(engagement)
                post = Post.objects.create(
                    author=engagement.student.user,
                    post_type=Post.PostType.ENGAGEMENT_STARTED,
                    content=default_text,
                    related_object=engagement,
                )
                create_feed_event_task(
                    event_type=FeedEvent.EventType.INTERNSHIP_STARTED
                    if engagement.engagement_type == Engagement.EngagementType.INTERNSHIP
                    else FeedEvent.EventType.MENTORSHIP_STARTED,
                    related_object_id=post.id,
                    related_model="post",
                    audience=FeedEvent.Audience.PUBLIC,
                    data={"content": post.content, "engagement": context},
                    score=random.randint(0, 10),
                )
            else:
                create_feed_event_task(
                    event_type=FeedEvent.EventType.INTERNSHIP_STARTED
                    if engagement.engagement_type == Engagement.EngagementType.INTERNSHIP
                    else FeedEvent.EventType.MENTORSHIP_STARTED,
                    related_object_id=engagement.id,
                    related_model=engagement.engagement_type,
                    audience=FeedEvent.Audience.PUBLIC,
                    data={**post_context},
                    score=random.randint(0, 10),
                )
            feed_event_count += 1

        self.stdout.write(f"    Created {feed_event_count} feed events")

        # --- Feed Impressions ---
        self.stdout.write("  Creating feed impressions...")
        impression_batch = []

        all_feed_events = list(FeedEvent.objects.all())
        for i in range(500):
            user = random.choice(all_users)
            event = random.choice(all_feed_events)
            days_ago = random.randint(0, 90)
            impression_batch.append(
                FeedImpression(
                    user=user,
                    event=event,
                    seen_at=timezone.now()
                    - timedelta(days=days_ago, hours=random.randint(0, 23)),
                )
            )

        # Deduplicate
        seen_impressions = set()
        unique_impressions = []
        for imp in impression_batch:
            key = (imp.user_id, imp.event_id)
            if key not in seen_impressions:
                seen_impressions.add(key)
                unique_impressions.append(imp)

        FeedImpression.objects.bulk_create(unique_impressions)
        self.stdout.write(f"    Created {len(unique_impressions)} feed impressions")

        self.stdout.write(
            self.style.SUCCESS(
                f"  Batch 8 complete: {len(created_reviews)} reviews, "
                f"{feed_event_count} feed events, "
                f"{len(unique_impressions)} impressions"
            )
        )
