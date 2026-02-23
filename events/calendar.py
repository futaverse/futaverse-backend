



def create_calender_event_data(title, description, date, start_time, end_time, attendees):
    """
    Create a dictionary representing the event data.
    """
    event = {
        "summary": title,
        "description": description,
        "start": {
            'dateTime': f"{date}T{start_time}",
            "timeZone": "Africa/Lagos",
        },
        "end": {
            'dateTime': f"{date}T{end_time}",
            "timeZone": "Africa/Lagos",
        },
        "attendees": [{"email": attendee} for attendee in attendees],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 12 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    
    return event