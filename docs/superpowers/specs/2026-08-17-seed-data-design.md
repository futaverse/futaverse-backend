# Seed Data Script Design

## Overview

A Django management command (`python manage.py seed_data`) that populates the database with realistic Nigerian FUTA-themed data to make the product look actively used by 100s of people over several months.

## Requirements

- 50 alumni, 80 students with unique Nigerian profiles
- 100s of internships, mentorships, events, posts, applications, offers, reviews
- Realistic timelines spanning 6+ months of history
- Batched execution to avoid choking the single bg worker
- No API/email/Cloudinary calls — direct ORM operations only

## Data Volumes

| Entity | Count | Distribution |
|--------|-------|-------------|
| Alumni users + profiles | 50 | ~15 industries, 6+ FUTA departments |
| Student users + profiles | 80 | Levels 100-500, various departments |
| Internships | 120 | 2-3 per alumni, mix of paid/unpaid/remote |
| Mentorships | 80 | 1-2 per alumni, various categories |
| Internship applications | 200 | 2-3 per student, various statuses |
| Mentorship applications | 120 | 1-2 per student, various statuses |
| Internship offers | 60 | ~30% conversion from applications |
| Mentorship offers | 40 | ~30% conversion from applications |
| Engagements | 100 | Active/completed/acknowledged mix |
| Events | 40 | Workshops, talks, networking, hybrid/virtual |
| Tickets | 80+ | 1-2 per event, mix of free/paid |
| Virtual meetings | 20+ | For virtual/hybrid events |
| Posts | 150 | engagement_started/completed/milestone |
| Notifications | 200 | Random for all users |
| Reviews | 100 | On completed engagements, ratings 2.5-5.0 |
| Feed events | 300+ | Auto-created per internship/mentorship/event |
| Feed targets | 600+ | 2-3 per feed event |
| Feed impressions | 500+ | Random user-event pairs |

## Batch Strategy

8 sequential batches, each in its own transaction with progress output:

1. **Users + Profiles** (130 users) — bulk_create users, then profiles
2. **Listings** (200 total) — internships + mentorships with spread dates
3. **Applications** (320 total) — internship + mentorship applications
4. **Offers** (100 total) — from accepted applications
5. **Engagements** (100 total) — via create_engagement() service
6. **Events** (40 total) — with tickets + virtual meetings
7. **Social** (350 total) — posts + notifications
8. **Reviews + Feed** (900+ total) — reviews, feed events, impressions

## File Structure

```
.core_assets/
  seed_data.py          # Management command
  seed_config.py        # Constants, name pools, industry data
```

## Key Design Decisions

- **No email/OTP** — users created with `is_active=True`, password `seedpass123`
- **Bulk operations** — `bulk_create` for performance, avoid signal overhead
- **Realistic timelines** — dates spread across past 6 months (Feb-Aug 2026)
- **Nigerian profiles** — FUTA departments, Nigerian states, realistic phone numbers
- **--clear flag** — option to wipe existing data before seeding
- **No external calls** — no Cloudinary, S3, or email service calls
- **Profile images** — skipped (would require Cloudinary)

## Data Distribution

### Alumni Industries
Technology, Finance, Consulting, Healthcare, Energy, Telecommunications, Manufacturing, Education, Real Estate, Agriculture, Media, Legal, Aviation, Retail, Government

### FUTA Departments
Computer Science, Electrical Engineering, Mechanical Engineering, Civil Engineering, Chemical Engineering, Information Technology, Mathematics, Physics, Architecture, Statistics

### Student Levels
Heavily weighted toward 200-400 (realistic for an active platform)

### Engagement Status Distribution
- Completed: 40% (for reviews)
- Active: 35%
- Acknowledged: 15%
- Terminated: 10%

### Application Status Distribution
- Accepted: 30%
- Pending: 25%
- Rejected: 25%
- Withdrawn: 20%
