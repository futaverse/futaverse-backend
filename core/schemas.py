from drf_spectacular.utils import OpenApiExample, PolymorphicProxySerializer

from .serializers import AlumniMeResponseSerializer, StudentMeResponseSerializer

ME_RESPONSES = {
    200: PolymorphicProxySerializer(
        component_name="MeResponse",
        serializers=[StudentMeResponseSerializer, AlumniMeResponseSerializer],
        resource_type_field_name="role",
    )
}

ME_EXAMPLES = [
    OpenApiExample(
        name="Student response",
        response_only=True,
        value={
            "data": {
                "sqid": "user-sqid",
                "email": "student@test.com",
                "role": "student",
                "created_at": "2026-01-01T00:00:00Z",
                "profile": {
                    "sqid": "profile-sqid",
                    "phone_num": "08012345678",
                    "gender": "male",
                    "firstname": "Test",
                    "lastname": "Student",
                    "middlename": "",
                    "address": "123 Test St",
                    "state": "Lagos",
                    "country": "Nigeria",
                    "description": None,
                    "matric_no": "FUTA/20/0001",
                    "department": "Computer Science",
                    "faculty": "Engineering",
                    "level": 300,
                    "cgpa": "4.50",
                    "skills": ["python", "django"],
                    "expected_grad_year": "2027",
                    "preferred_industry": None,
                    "preferred_company_type": None,
                    "willingness_to_be_mentored": True,
                    "linkedin_url": None,
                    "github_url": None,
                    "website_url": None,
                    "x_url": None,
                    "instagram_url": None,
                    "facebook_url": None,
                    "avg_rating": None,
                    "total_reviews": 0,
                    "created_at": "2026-01-01T00:00:00Z",
                    "profile_img_url": "https://res.cloudinary.com/example/student.jpg",
                    "resumes": [
                        {
                            "sqid": "resume-sqid",
                            "resume": "https://example.com/resume.pdf",
                            "filename": "cv.pdf",
                            "uploaded_at": "2026-01-02T00:00:00Z",
                        }
                    ],
                },
            },
            "status": "success",
        },
    ),
    OpenApiExample(
        name="Alumni response",
        response_only=True,
        value={
            "data": {
                "sqid": "user-sqid",
                "email": "alumnus@test.com",
                "role": "alumni",
                "created_at": "2026-01-01T00:00:00Z",
                "profile": {
                    "sqid": "profile-sqid",
                    "phone_num": "08098765432",
                    "gender": "male",
                    "firstname": "Test",
                    "lastname": "Alumnus",
                    "middlename": "",
                    "address": "456 Test Ave",
                    "state": "Ogun",
                    "country": "Nigeria",
                    "description": None,
                    "matric_no": "FUTA/14/0002",
                    "department": "Computer Science",
                    "faculty": "Engineering",
                    "grad_year": "2020",
                    "current_job_title": "Software Engineer",
                    "current_company": "Tech Corp",
                    "industry": "Technology",
                    "years_of_exp": 5,
                    "previous_comps": ["Startup Inc"],
                    "linkedin_url": None,
                    "company_linkedin_url": None,
                    "github_url": None,
                    "website_url": None,
                    "company_website_url": None,
                    "x_url": None,
                    "instagram_url": None,
                    "facebook_url": None,
                    "avg_rating": None,
                    "total_reviews": 0,
                    "created_at": "2026-01-01T00:00:00Z",
                    "profile_img_url": "https://res.cloudinary.com/example/alumnus.jpg",
                },
            },
            "status": "success",
        },
    ),
]
