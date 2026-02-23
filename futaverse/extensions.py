from supabase import create_client, Client
from django.conf import settings
import uuid
from rest_framework.response import Response
from rest_framework import status

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_resume(file, student_id):
    """
    Uploads a student's resume to Supabase storage and returns the public URL
    """
    try:
        path = f'resumes/{student_id}/{uuid.uuid4().hex}_{file.name}'
        
        file_bytes = file.read()

        response = supabase.storage.from_("futaverse-media").upload(path, file_bytes,  file_options={"content_type": file.content_type})
        print(response)
            
        public_url = supabase.storage.from_("futaverse-media").get_public_url(path)
        
        if not public_url:
            raise Exception("Failed to get public URL")
        
        return public_url
    except Exception as e:
        raise Exception(f"File upload failed: {str(e)}")