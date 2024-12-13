from celery import shared_task
from django.utils.timezone import localtime, now
from .models import User, Attendance
from geopy.distance import geodesic
import datetime

@shared_task
def check_attendance():
    """
    Periodically check attendance for students near the school.
    """
    students = User.objects.filter(role=User.STUDENT)
    current_time = localtime(now()).time()

    # Only check during a specific time window
    if current_time >= datetime.time(10, 0) and current_time <= datetime.time(17, 0):
        for student in students:
            school = getattr(student, 'school', None)  # Get the student's associated school
            if not school:
                continue

            # Mock or retrieve student's current coordinates
            student_coords = (42.8746, 74.6122)  # Mocked coordinates
            school_coords = (float(school.latitude), float(school.longitude))

            # Calculate distance
            distance = geodesic(student_coords, school_coords).kilometers
            status = 'present' if distance <= 0.1 else 'absent'

            # Update or create attendance record
            Attendance.objects.update_or_create(
                student=student,
                date=now().date(),
                defaults={
                    'status': status,
                    'latitude': student_coords[0],
                    'longitude': student_coords[1],
                }
            )