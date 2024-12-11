import csv
import secrets
import string
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import School, Class
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Ручной импорт студентов и создание групп из списка'

    def handle(self, *args, **kwargs):
        # Получение модели пользователя
        User = get_user_model()

        # Получение или создание объекта школы
        school_name = "Название вашей школы"  # Замените на фактическое название вашей школы
        school, created = School.objects.get_or_create(name=school_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Создана новая школа: {school_name}"))
        else:
            self.stdout.write(f"Используется существующая школа: {school_name}")

        # Список групп и студентов
        groups = {
            "Разработка игр RI-24-9": [
                "Ашыров Бектур Ашырович",
                "Балакин Кирилл Сергеевич",
                "Джоошбаев Адис Рустанбекович",
                "Дуйшенова Айсулуу Нурланбековна",
                "Жунусов Жанторо Алтынбекович",
                "Зулпуев Адилет Алмазович",
                "Ибралиев Байыш Нурканович",
                "Исакова Алиса Бакытовна",
                "Касыев Агзам Эрнестович",
                "Кудашов Урмат Бактыбекович",
                "Матраимова Даана Маратовна",
                "Мырзамомунов Бекболсун Кубанычбекович",
                "Назырбекова Назик Керимжановна",
                "Омурбеков Нурислам Баатырбекович",
                "Рыскулбеков Нуржигит Эрнисбекович",
                "Сайфудинов Даниэль Адилетович",
                "Эргашев Иброхим Шовкат Угли"
            ],
            # Добавьте другие группы, если нужно
        }

        # Функция для генерации уникального username
        def generate_username(full_name):
            base_username = slugify(full_name).replace('-', '').lower()
            
            # Если username оказался пустым (например, имя содержит только спецсимволы)
            if not base_username:
                base_username = f"user{secrets.token_hex(4)}"  # Генерация уникального имени
            
            username = base_username
            counter = 1
            
            # Убедимся, что username уникальный
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            return username

        # Функция для генерации случайного пароля
        def generate_password(length=12):
            characters = string.ascii_letters + string.digits + string.punctuation
            # Исключим символы, которые могут вызвать проблемы в некоторых системах
            characters = characters.replace('"', '').replace("'", "").replace('\\', '')
            password = ''.join(secrets.choice(characters) for _ in range(length))
            return password

        # Список для записи учетных данных студентов
        credentials = []

        # Обработка каждой группы
        for group_name, students in groups.items():
            # Создание или получение группы
            class_obj, created = Class.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Создана новая группа: {group_name}"))
            else:
                self.stdout.write(f"Группа уже существует: {group_name}")

            # Удаление старых студентов из группы
            old_students = class_obj.students.filter(role=User.STUDENT)
            if old_students.exists():
                count = old_students.count()
                old_students.delete()
                self.stdout.write(f"Удалено {count} старых студентов из группы: {group_name}")

            # Добавление новых студентов
            for full_name in students:
                # Пропускаем пустые строки
                if not full_name.strip():
                    continue

                # Проверка существования пользователя с таким именем
                if User.objects.filter(name=full_name.strip(), role=User.STUDENT).exists():
                    self.stdout.write(f"Студент уже существует (пропуск): {full_name.strip()}")
                    continue

                # Генерация уникального username
                try:
                    username = generate_username(full_name.strip())
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Ошибка генерации username для {full_name}: {e}"))
                    continue

                # Генерация случайного пароля
                password = generate_password()

                # Создание пользователя
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=f"{username}@school.com",  # Можно изменить формат email
                        password=password,
                        role=User.STUDENT,
                        name=full_name.strip(),
                        school=school
                    )
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Ошибка создания пользователя {full_name.strip()}: {e}"))
                    continue

                # Добавление пользователя в группу
                try:
                    class_obj.students.add(user)
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Ошибка добавления студента {full_name.strip()} в группу {group_name}: {e}"))
                    continue

                # Сохранение учетных данных
                credentials.append({
                    'username': username,
                    'password': password,
                    'full_name': full_name.strip(),
                    'group': group_name
                })

                self.stdout.write(self.style.SUCCESS(f"Добавлен студент: {full_name.strip()} в группу {group_name}"))

        # Запись учетных данных в CSV-файл
        output_csv = "students_credentials.csv"
        try:
            with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['username', 'password', 'full_name', 'group']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for cred in credentials:
                    writer.writerow(cred)
            self.stdout.write(self.style.SUCCESS(f"Учетные данные студентов сохранены в файл: {output_csv}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка при записи CSV-файла: {e}"))

        self.stdout.write(self.style.SUCCESS("Импорт студентов и групп завершён успешно."))