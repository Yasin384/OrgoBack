# main/management/commands/reset_and_create_i24_9.py

import os
import random
import string
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import School, SchoolClass
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Delete all classes and create class ИИ-24-9 with specified students using numeric usernames and passwords.'

    def handle(self, *args, **options):
        # Define the class name
        class_name = "ИИ-24-9"

        # Define the list of students
        students = [
            "Абдурахмонов Кутэмир Рафторович",
            "Абжалилов Бекмырза Абдилазимович",
            "Айдарбеков Арген Нурланбекович",
            "Айдаров Айдин Маратович",
            "Алимханов Азизхон Ахмадхонович",
            "Исманалиев Асланбек Муратжанович",
            "Казыбеков Байнур Бекболотович",
            "Курманбеков Арнас Дүйшөнкулович",
            "Мамбетжумаев Залкарбек Русланович",
            "Медербекова Алтынай Максатбековна",
            "Оморбеков Айбек Алмазбекович",
            "Сайдрасулов Саидакбар Камалдинович",
        ]

        # Prepare to write credentials
        credentials_path = os.path.join(os.getcwd(), 'students_credentials.txt')
        with open(credentials_path, 'w', encoding='utf-8') as cred_file:
            cred_file.write('Class\tUsername\tPassword\n')

            # Use transaction for atomicity
            with transaction.atomic():
                # Step 1: Delete all existing classes
                existing_classes = SchoolClass.objects.all()
                count = existing_classes.count()
                existing_classes.delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted {count} existing classes.'))

                # Step 2: Get or create the default school
                school = self.get_or_create_school()

                # Step 3: Create the class ИИ-24-9
                school_class, created = SchoolClass.objects.get_or_create(
                    name=class_name,
                    defaults={
                        'school': school,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created class: {class_name}'))
                else:
                    self.stdout.write(f'Class already exists: {class_name}')

                # Step 4: Create users and assign to class
                starting_username = 1001  # Starting point for numeric usernames
                for idx, student_full_name in enumerate(students, start=starting_username):
                    username = str(idx)  # Numeric username

                    # Ensure username uniqueness
                    while User.objects.filter(username=username).exists():
                        idx += 1
                        username = str(idx)

                    # Generate numeric password (e.g., 6-digit)
                    password = self.generate_numeric_password(length=6)

                    # Split full name into parts
                    first_name, last_name = self.split_full_name(student_full_name)

                    # Create user
                    user, user_created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': f"{username}@example.com",  # Assign a default email
                            'role': User.STUDENT,
                            'school': school,
                        }
                    )

                    if user_created:
                        user.set_password(password)
                        user.save()
                        # Assign to class via students ManyToManyField
                        school_class.students.add(user)
                        self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
                    else:
                        self.stdout.write(f'User already exists: {username}')

                    # Write credentials to file
                    cred_file.write(f'{class_name}\t{username}\t{password}\n')

        self.stdout.write(self.style.SUCCESS(f'Credentials saved to {credentials_path}'))

    def get_or_create_school(self):
        """
        Get the default school or create one if none exists.
        Modify this method if you have multiple schools.
        """
        school_name = "Default School"
        school, created = School.objects.get_or_create(
            name=school_name,
            defaults={
                'address': '123 Default Street',
                'email': 'admin@defaultschool.com',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created school: {school_name}'))
        else:
            self.stdout.write(f'School already exists: {school_name}')
        return school

    def generate_numeric_password(self, length=6):
        """
        Generate a random numeric password of specified length.
        """
        return ''.join(random.choices(string.digits, k=length))

    def split_full_name(self, full_name):
        """
        Split the full name into first name and last name.
        Assumes format: LastName FirstName Patronymic
        """
        parts = full_name.strip().split()
        if len(parts) >= 2:
            last_name = parts[0]
            first_name = parts[1]
        elif len(parts) == 1:
            last_name = parts[0]
            first_name = ''
        else:
            last_name = ''
            first_name = ''
        return first_name, last_name
