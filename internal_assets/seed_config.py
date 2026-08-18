"""
Seed data configuration — Nigerian FUTA-themed data pools.

Used by the seed_data management command to generate realistic platform data.
"""

import random
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Nigerian names
# ---------------------------------------------------------------------------

FIRST_NAMES_MALE = [
    "Adewale", "Chinedu", "Emeka", "Tunde", "Oluwaseun", "Chukwuemeka",
    "Adebayo", "Ifeanyi", "Olumide", "Chidi", "Kehinde", "Babatunde",
    "Omololu", "Femi", "Yemi", "Segun", "Damilare", "Ayo", "Tobi",
    "Samuel", "David", "Michael", "Daniel", "Joshua", "Elijah",
    "Isaac", "Joseph", "Caleb", "Timothy", "Isaiah", "Emmanuel",
    "Chisom", "Chinedu", "Ikenna", "Nnamdi", "Obinna", "Uche",
    "Moses", "Peter", "Paul", "John", "James", "Andrew",
    "Ibrahim", "Abdulrahman", "Musa", "Suleiman", "Yusuf", "Aliyu",
    "Ola", "Kayode", "Deji", "Lanre", "Gbolahan", "Tunde",
]

FIRST_NAMES_FEMALE = [
    "Chidinma", "Oluwadamilola", "Adaeze", "Ngozi", "Amara", "Folake",
    "Aderonke", "Blessing", "Chiamaka", "Ebunoluwa", "Funke", "Grace",
    "Halima", "Ifeoma", "Jumoke", "Kemi", "Linda", "Maryam",
    "Nneka", "Oluchi", "Priscilla", "Rashidat", "Sade", "Tolu",
    "Ure", "Victoria", "Wunmi", "Yetunde", "Zainab", "Ada",
    "Chisom", "Ebube", "Favour", "Gloria", "Hannah", "Ife",
    "Janet", "Kalu", "Lilian", "Mercy", "Nancy", "Obianuju",
    "Patience", "Rita", "Stella", "Uloma", "Vivian", "Winifred",
    "Yewande", "Zara", "Adanna", "Chinyere", "Ezinne", "Ifeanyichukwu",
]

LAST_NAMES = [
    "Okafor", "Adeyemi", "Ibrahim", "Chukwu", "Abubakar", "Olawale",
    "Nnamdi", "Balogun", "Okonkwo", "Adekunle", "Obi", "Oladipo",
    "Eze", "Adegoke", "Aliyu", "Afolabi", "Uche", "Ogundimu",
    "Lawal", "Akinwale", "Chinedu", "Mohammed", "Oyewole", "Igwe",
    "Adeleke", "Oluwole", "Bakare", "Ogundele", "Oladimeji", "Adebiyi",
    "Ikhena", "Obasohan", "Ogundoyin", "Aderibigbe", "Oyekanmi", "Adebajo",
    "Akinola", "Osagie", "Idowu", "Adeyinka", "Omotayo", "Fayemi",
    "Onwueme", "Okechukwu", "Ezekwe", "Anichebe", "Ugwu", "Ogbonna",
    "Amaechi", "Obiora", "Chike", "Uzoma", "Emenike", "Nwosu",
    "Ogundairo", "Adesanya", "Atere", "Oyelaran", "Fadare", "Awolowo",
]

# ---------------------------------------------------------------------------
# FUTA departments and faculties
# ---------------------------------------------------------------------------

FUTA_DEPARTMENTS = [
    ("Computer Science", "Engineering and Technology"),
    ("Electrical and Electronics Engineering", "Engineering and Technology"),
    ("Mechanical Engineering", "Engineering and Technology"),
    ("Civil Engineering", "Engineering and Technology"),
    ("Chemical Engineering", "Engineering and Technology"),
    ("Information Technology", "Engineering and Technology"),
    ("Mathematics", "Science"),
    ("Physics", "Science"),
    ("Architecture", "Engineering and Technology"),
    ("Statistics", "Science"),
    ("Industrial Engineering", "Engineering and Technology"),
    ("Metallurgical and Materials Engineering", "Engineering and Technology"),
    ("Mining Engineering", "Engineering and Technology"),
    ("Agricultural Engineering", "Engineering and Technology"),
    ("Electrical Engineering", "Engineering and Technology"),
]

# ---------------------------------------------------------------------------
# Nigerian states and cities
# ---------------------------------------------------------------------------

NIGERIAN_STATES = [
    "Lagos", "Ogun", "Oyo", "Osun", "Ondo", "Ekiti", "Kwara",
    "Abuja", "Kano", "Kaduna", "Rivers", "Delta", "Edo", "Anambra",
    "Enugu", "Abia", "Imo", "Cross River", "Akwa Ibom", "Bayelsa",
    "Borno", "Adamawa", "Gombe", "Taraba", "Plateau", "Nassarawa",
    "Benue", "Kogi", "Niger", "Kebbi", "Sokoto", "Zamfara",
    "Jigawa", "Katsina", "Bauchi", "Yobe", "Ebonyi", "Benue",
]

# ---------------------------------------------------------------------------
# Industries and companies
# ---------------------------------------------------------------------------

INDUSTRIES = [
    "Technology", "Finance", "Banking", "Consulting", "Healthcare",
    "Energy", "Oil and Gas", "Telecommunications", "Manufacturing",
    "Education", "Real Estate", "Agriculture", "Media", "Entertainment",
    "Legal", "Aviation", "Retail", "E-commerce", "Logistics",
    "Construction", "Hospitality", "Insurance", "Mining", "Government",
]

COMPANIES = {
    "Technology": [
        "Andela", "Flutterwave", "Paystack", "Interswitch", "Kuda Bank",
        "Carbon", "Piggyvest", "Farmcrowdy", "Tremendous", "54gene",
        "TeamApt", "Moove", "Reliance HMO", "Stears", "Lidra",
        "BuyAm", "Zumi", "Risevest", "FairMoney", "Cowrywise",
    ],
    "Finance": [
        "Zenith Bank", "GTBank", "Access Bank", "First Bank", "UBA",
        "Fidelity Bank", "Stanbic IBTC", "StanChart", "Citi Nigeria",
        "Ecobank", "Wema Bank", "Polaris Bank", "Unity Bank", "Keystone Bank",
    ],
    "Consulting": [
        "McKinsey Lagos", "BCG Nigeria", "Deloitte Nigeria", "PwC Nigeria",
        "KPMG Nigeria", "EY Nigeria", "ARM Securities", "Quantum Zenith",
    ],
    "Healthcare": [
        "54gene", "LifeBank", "mPharma", "Wellvis", "MDaaS",
        "Reliance HMO", "Hygeia HMO", "NHIS", "Synlab Nigeria",
    ],
    "Energy": [
        "Seplat Energy", "Oando", "Dangote Refinery", "NNPC", "Shell Nigeria",
        "Total Energies Nigeria", "Chevron Nigeria", "Agip Nigeria",
    ],
    "Telecommunications": [
        "MTN Nigeria", "Airtel Nigeria", "Glo Mobile", "9Mobile",
        "MainOne", "rack Centre", "Internet Solutions",
    ],
    "Manufacturing": [
        "Dangote Group", "Nigerian Breweries", "Nestle Nigeria", "Unilever Nigeria",
        "PZ Cussons", "Cadbury Nigeria", "Lafarge Africa", "BUA Group",
    ],
    "E-commerce": [
        "Jumia Nigeria", "Konga", "PayPorte", "CartNG", "MarketDoctor",
    ],
    "Media": [
        "Pulse Nigeria", "TechCabal", "Nairametrics", "Techpoint Africa",
        "Benjamin Dada", "OkayAfrica", "Channels TV", "Punch Newspapers",
    ],
    "Logistics": [
        "Kobo360", "Max NG", "GIG Logistics", "DHL Nigeria", "FedEx Nigeria",
    ],
}

# Fallback for industries not in COMPANIES
DEFAULT_COMPANIES = [
    "Schlumberger", "Baker Hughes", "Julius Berger", "Boustead",
    "TGI Group", "Olam Nigeria", "Honeywell Group", "Coscharis Group",
    "Innoson Vehicle Manufacturing", "Ibukun Ajike",
]

# ---------------------------------------------------------------------------
# Skills pools
# ---------------------------------------------------------------------------

TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Django", "Node.js",
    "Java", "C++", "SQL", "HTML/CSS", "Swift", "Kotlin", "Go", "Rust",
    "AWS", "Docker", "Kubernetes", "Git", "Linux", "PostgreSQL",
    "MongoDB", "Redis", "GraphQL", "REST APIs", "Machine Learning",
    "TensorFlow", "PyTorch", "Data Analysis", "Power BI", "Tableau",
    "Figma", "Adobe XD", "UI/UX Design", "Product Management",
    "Agile/Scrum", "DevOps", "CI/CD", "Terraform", "Azure", "GCP",
    "Flutter", "React Native", "Vue.js", "Angular", "Spring Boot",
    "Microservices", "Blockchain", "Solidity", "Cybersecurity",
    "Penetration Testing", "Network Security",
]

NON_TECH_SKILLS = [
    "Project Management", "Leadership", "Communication", "Teamwork",
    "Problem Solving", "Critical Thinking", "Public Speaking",
    "Business Development", "Sales", "Marketing", "Content Writing",
    "Copywriting", "SEO", "Social Media Management", "Brand Strategy",
    "Financial Analysis", "Accounting", "HR Management", "Recruitment",
    "Negotiation", "Time Management", "Event Planning", "Grant Writing",
    "Research", "Data Entry", "Customer Service", "Relations Management",
]

ALL_SKILLS = TECH_SKILLS + NON_TECH_SKILLS

# ---------------------------------------------------------------------------
# Mentorship focus areas and categories (from model choices)
# ---------------------------------------------------------------------------

MENTORSHIP_FOCUS_AREAS = [
    "career_guidance", "cv_and_portfolio", "interview_prep",
    "linkedin_branding", "salary_negotiation", "software_engineering",
    "data_science", "product_management", "product_design",
    "cybersecurity", "cloud_devops", "embedded_systems",
    "research_academia", "entrepreneurship", "freelancing",
    "fintech", "agritech", "startup_building", "business_development",
    "tech_in_nigeria", "diaspora_pathways", "postgrad_abroad",
    "nysc_guidance", "communication", "leadership", "open_source",
]

MENTORSHIP_CATEGORIES = [
    "career_development", "technical", "academic",
    "entrepreneurship", "industry_specific", "other",
]

# ---------------------------------------------------------------------------
# Internship data pools
# ---------------------------------------------------------------------------

WORK_MODES = ["Remote", "Hybrid", "Onsite"]
ENGAGEMENT_TYPES = ["Full-time", "Part-time", "Contract"]

INTERNSHIP_TITLES = [
    "Software Engineer Intern", "Frontend Developer Intern",
    "Backend Developer Intern", "Data Analyst Intern",
    "Machine Learning Engineer Intern", "DevOps Engineer Intern",
    "Product Manager Intern", "UI/UX Design Intern",
    "Marketing Intern", "Business Development Intern",
    "Cybersecurity Intern", "Cloud Engineering Intern",
    "Mobile App Developer Intern", "QA Engineer Intern",
    "Technical Writer Intern", "Research Intern",
    "Blockchain Developer Intern", "AI Engineer Intern",
    "Network Engineering Intern", "Database Administrator Intern",
    "IT Support Intern", "Project Management Intern",
    "Financial Analyst Intern", "HR Intern",
    "Content Strategy Intern", "Growth Hacker Intern",
    "Full Stack Developer Intern", "Embedded Systems Intern",
]

MENTORSHIP_TITLES = [
    "Career Guidance in Tech", "CV & Portfolio Review",
    "Interview Preparation Masterclass", "LinkedIn Branding Workshop",
    "Salary Negotiation Strategies", "Software Engineering Mentorship",
    "Data Science Career Path", "Product Management 101",
    "UI/UX Design Mentorship", "Cybersecurity Career Guide",
    "Cloud & DevOps Mentorship", "Entrepreneurship in Tech",
    "Freelancing in Nigeria", "Fintech Career Guidance",
    "Startup Building from Zero", "Business Development Skills",
    "Tech Career in Nigeria", "Diaspora Pathways for Techies",
    "Postgraduate Studies Abroad", "NYSC Career Planning",
    "Open Source Contributions", "Leadership in Tech",
    "Communication Skills for Engineers", "Research & Academia Path",
    "AgriTech Opportunities", "Embedded Systems Deep Dive",
]

# ---------------------------------------------------------------------------
# Event data pools
# ---------------------------------------------------------------------------

EVENT_CATEGORIES = [
    "workshop", "talk", "career", "networking",
    "training", "symposium", "donation", "other",
]

EVENT_MODES = ["virtual", "physical", "hybrid"]

EVENT_TITLES = [
    "FUTA Tech Summit 2026", "Career Fair & Networking Night",
    "Hackathon: Build for Nigeria", "AI & Machine Learning Workshop",
    "Cybersecurity Awareness Seminar", "Product Design Sprint",
    "Startup Pitch Day", "Data Science Bootcamp",
    "Cloud Computing Workshop", "Blockchain in Africa Panel",
    "Women in Tech Conference", "FUTA Alumni Homecoming",
    "DevOps Best Practices Talk", "Mobile App Development Workshop",
    "Digital Marketing Masterclass", "Financial Literacy Seminar",
    "Public Speaking Workshop", "Leadership Development Program",
    "Resume & Interview Prep Day", "Open Source Contribution Sprint",
    "AgriTech Innovation Forum", "HealthTech in Nigeria Talk",
    "Fintech Revolution Panel", "Creative Writing Workshop",
    "Photography & Content Creation", "NYSC Orientation Talk",
    "Postgraduate Study Abroad Info Session", "Venture Capital 101",
    "Building Your Personal Brand", "Mental Health in Tech",
    "Sustainable Engineering Seminar", "Robotics & IoT Workshop",
    "Game Development Workshop", "3D Modeling & Animation",
    "Music Production Workshop", "Film & Media Production",
    "Social Enterprise Forum", "NGO & Impact Investing Talk",
    "Real Estate Investment Workshop", "Legal Tech Innovations",
]

# ---------------------------------------------------------------------------
# Post content templates
# ---------------------------------------------------------------------------

POST_STARTER_TEMPLATES = [
    "Excited to share that I've just started a new internship at {company} as a {title}! Looking forward to learning and growing.",
    "Thrilled to announce my journey as a {title} at {company}. Ready to make an impact!",
    "Starting my internship journey at {company} today! Can't wait to dive into {skill} projects.",
    "New chapter begins! Just landed an internship at {company}. Grateful for this opportunity.",
    "Day 1 at {company} as a {title}! The team has been incredibly welcoming.",
]

POST_COMPLETION_TEMPLATES = [
    "Just wrapped up my internship at {company}! It's been an amazing {weeks} weeks learning {skill}. Thank you to everyone who made this possible.",
    "Successfully completed my {title} internship at {company}! Gained invaluable experience in {skill}.",
    "What a journey! My {weeks}-week internship at {company} has come to an end. Grateful for every lesson.",
    "Final day at {company}! Reflecting on an incredible internship experience. {skill} skills level: up!",
    "Internship complete at {company}! The growth I've experienced as a {title} is immeasurable.",
]

POST_MILESTONE_TEMPLATES = [
    "Hit a milestone today at {company}! Shipped my first {skill} feature. Small wins matter.",
    "One month into my internship at {company} and I've already learned so much about {skill}.",
    "Proud moment: presented my project at {company} today. Public speaking gets easier with practice!",
    "3 months at {company} — from intern to contributing team member. The growth is real.",
    "Just got positive feedback from my supervisor at {company}! Hard work pays off.",
]

# ---------------------------------------------------------------------------
# Notification templates
# ---------------------------------------------------------------------------

NOTIFICATION_TITLES = [
    "New Application Received", "Application Status Update",
    "New Internship Opportunity", "New Mentorship Available",
    "Event Reminder", "New Review", "Engagement Update",
    "New Post from Connection", "Weekly Digest",
    "Profile View", "New Message", "Achievement Unlocked",
]

NOTIFICATION_CONTENT_TEMPLATES = [
    "A new student has applied to your {type} '{title}'.",
    "Your application for '{title}' has been {status}.",
    "A new {type} '{title}' has been posted in your area of interest.",
    "Don't miss the upcoming event: '{title}'.",
    "You have a new review from a {role}.",
    "Your engagement status has been updated to {status}.",
    "Check out the latest posts from your connections.",
    "Here's your weekly summary of platform activity.",
    "Someone viewed your profile today.",
    "You have a new message from {name}.",
    "Congratulations! You've earned the '{badge}' badge.",
]

# ---------------------------------------------------------------------------
# Review text templates
# ---------------------------------------------------------------------------

REVIEW_TEXTS_POSITIVE = [
    "Excellent experience! Very professional and supportive throughout the process.",
    "Highly recommend. The mentorship/guidance was invaluable for my career growth.",
    "Great communicator, always available when needed. Learned a lot.",
    "One of the best experiences I've had on this platform. Truly invested in student success.",
    "Knowledgeable and patient. Helped me understand complex concepts with ease.",
    "Outstanding mentorship. The structured approach to learning was exactly what I needed.",
    "Would definitely work with again. The experience exceeded my expectations.",
    "Very supportive and encouraging. Helped me build confidence in my skills.",
]

REVIEW_TEXTS_NEUTRAL = [
    "Good experience overall. Some areas could be improved but generally satisfied.",
    "Decent mentorship. The content was useful but the pace could have been faster.",
    "Met expectations. The guidance was helpful for my career planning.",
    "Solid experience. Would recommend for beginners looking for direction.",
    "Good learning opportunity. The structured sessions were beneficial.",
]

REVIEW_TEXTS_NEGATIVE = [
    "Average experience. Expected more hands-on guidance than what was provided.",
    "Communication could have been better. Sometimes took too long to respond.",
    "The content was basic. Would have appreciated more advanced topics.",
]

# ---------------------------------------------------------------------------
# Internship description templates
# ---------------------------------------------------------------------------

INTERNSHIP_DESCRIPTION_TEMPLATES = [
    (
        "Join our team at {company} as a {title}. You'll work on real projects "
        "using {skills} and gain hands-on experience in a fast-paced environment. "
        "This is a great opportunity for {level} level students passionate about {industry}."
    ),
    (
        "{company} is looking for a motivated {title} to join our {department} team. "
        "You'll be involved in {tasks} and collaborate with experienced professionals. "
        "Duration: {weeks} weeks. Ideal for students studying {field}."
    ),
    (
        "We're offering a {title} position at {company}. The role involves {tasks} "
        "using modern tools and methodologies. You'll receive mentorship from senior "
        "engineers and exposure to production-level {industry} projects."
    ),
    (
        "Exciting opportunity at {company}! As a {title}, you'll contribute to "
        "{tasks} while learning about {industry} best practices. "
        "This {work_mode} position is perfect for students looking to build their portfolio."
    ),
]

MENTORSHIP_DESCRIPTION_TEMPLATES = [
    (
        "This mentorship program focuses on {focus_area}. Over {weeks} weeks, "
        "we'll cover {topics} through weekly 1-hour sessions. "
        "Perfect for students interested in {industry} careers."
    ),
    (
        "Join this {category} mentorship to develop your {focus_area} skills. "
        "Sessions include {topics} and personalized career advice. "
        "Open to {level} level students with a passion for growth."
    ),
    (
        "A structured {weeks}-week mentorship in {focus_area}. "
        "Topics covered: {topics}. You'll receive hands-on guidance, "
        "portfolio reviews, and career planning support."
    ),
]

# ---------------------------------------------------------------------------
# Internship task descriptions (for filling templates)
# ---------------------------------------------------------------------------

INTERNSHIP_TASKS = [
    "building REST APIs", "developing frontend interfaces",
    "analyzing datasets", "training ML models",
    "managing cloud infrastructure", "conducting security audits",
    "designing user interfaces", "writing technical documentation",
    "developing mobile features", "testing and debugging software",
    "building data pipelines", "creating marketing campaigns",
    "developing automation scripts", "supporting IT operations",
    "conducting market research", "assisting with financial modeling",
    "contributing to open source projects", "building IoT prototypes",
    "developing embedded firmware", "creating content strategies",
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def random_date_in_past(max_months_ago=6, min_days_ago=7):
    """Return a random date within the past N months."""
    today = date.today()
    earliest = today - timedelta(days=max_months_ago * 30)
    latest = today - timedelta(days=min_days_ago)
    delta = (latest - earliest).days
    if delta <= 0:
        return earliest
    return earliest + timedelta(days=random.randint(0, delta))


def random_future_date(max_months_ahead=3):
    """Return a random date in the near future."""
    today = date.today()
    latest = today + timedelta(days=max_months_ahead * 30)
    delta = (latest - today).days
    if delta <= 0:
        return today
    return today + timedelta(days=random.randint(1, delta))


def random_phone_number():
    """Generate a realistic Nigerian phone number."""
    prefixes = ["080", "081", "070", "090", "085", "070", "090", "081"]
    prefix = random.choice(prefixes)
    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


def random_matric_number(grad_year, dept_code):
    """Generate a FUTA-style matric number like FUTA/CS/20/00123."""
    num = random.randint(1, 999)
    return f"FUTA/{dept_code}/{str(grad_year)[-2:]}/{num:05d}"


def weighted_choice(choices, weights):
    """Pick from choices using weights."""
    return random.choices(choices, weights=weights, k=1)[0]


# Department code mapping for matric numbers
DEPT_CODES = {
    "Computer Science": "CS",
    "Electrical and Electronics Engineering": "EEE",
    "Mechanical Engineering": "ME",
    "Civil Engineering": "CE",
    "Chemical Engineering": "CHE",
    "Information Technology": "IT",
    "Mathematics": "MTH",
    "Physics": "PHY",
    "Architecture": "ARCH",
    "Statistics": "STA",
    "Industrial Engineering": "IE",
    "Metallurgical and Materials Engineering": "MME",
    "Mining Engineering": "MIN",
    "Agricultural Engineering": "AE",
    "Electrical Engineering": "EE",
}
