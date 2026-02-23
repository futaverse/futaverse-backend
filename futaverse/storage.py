from supabase import create_client
from django.conf import settings
import uuid

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_resume(file, student_id):
    """
    Uploads a student's resume to Supabase storage and returns the public URL
    """
    # Generate a unique filename
    filename = f"{student_id}_{uuid.uuid4().hex}.pdf"

    # Upload to "resumes" bucket
    supabase.storage.from_("resumes").upload(filename, file)

    # Get public URL
    public_url = supabase.storage.from_("resumes").get_public_url(filename)
    return public_url

