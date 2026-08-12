


def upload_resume(resume, student):
    if not resume:
        raise ValueError({"detail": "Resume not provided", "status": "error"})
    