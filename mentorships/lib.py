from django.db import models

class FocusArea(models.TextChoices):
        # Career & Professional Development
        CAREER_GUIDANCE       = 'career_guidance',       'Career Guidance'
        CV_AND_PORTFOLIO      = 'cv_and_portfolio',      'CV & Portfolio Building'
        INTERVIEW_PREP        = 'interview_prep',         'Interview Preparation'
        LINKEDIN_BRANDING     = 'linkedin_branding',     'LinkedIn & Personal Branding'
        SALARY_NEGOTIATION    = 'salary_negotiation',    'Salary Negotiation'

        # Tech & Engineering (FUTA is a tech university)
        SOFTWARE_ENGINEERING  = 'software_engineering',  'Software Engineering'
        DATA_SCIENCE          = 'data_science',           'Data Science & Analytics'
        PRODUCT_MANAGEMENT    = 'product_management',    'Product Management'
        PRODUCT_DESIGN        = 'product_design',         'Product Design & UX'
        CYBERSECURITY         = 'cybersecurity',          'Cybersecurity'
        CLOUD_DEVOPS          = 'cloud_devops',           'Cloud & DevOps'
        EMBEDDED_SYSTEMS      = 'embedded_systems',      'Embedded Systems & IoT'
        RESEARCH_ACADEMIA     = 'research_academia',     'Research & Academia'

        # Business & Entrepreneurship (Nigerian startup ecosystem)
        ENTREPRENEURSHIP      = 'entrepreneurship',       'Entrepreneurship'
        FREELANCING           = 'freelancing',            'Freelancing & Remote Work'
        FINTECH               = 'fintech',                'Fintech'
        AGRITECH              = 'agritech',               'Agritech'
        STARTUP_BUILDING      = 'startup_building',      'Startup Building'
        BUSINESS_DEVELOPMENT  = 'business_development',  'Business Development'

        # Navigating the Nigerian market specifically
        TECH_IN_NIGERIA       = 'tech_in_nigeria',       'Breaking into Tech in Nigeria'
        DIASPORA_PATHWAYS     = 'diaspora_pathways',     'Diaspora & International Opportunities'
        POSTGRAD_ABROAD       = 'postgrad_abroad',       'Postgraduate Studies Abroad'
        NYSC_GUIDANCE         = 'nysc_guidance',         'NYSC & Early Career'

        # Soft Skills
        COMMUNICATION         = 'communication',          'Communication & Presentation'
        LEADERSHIP            = 'leadership',             'Leadership & Teamwork'
        OPEN_SOURCE           = 'open_source',            'Open Source Contribution'
        