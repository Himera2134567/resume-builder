import uuid
from PIL import Image
from django.db import models

def user_photo_path(instance, filename):
    return f"resumes/{instance.id}/photo/{filename}"

def project_file_path(instance, filename):
    return f"resumes/{instance.resume.id}/projects/{filename}"

def experience_file_path(instance, filename):
    return f"resumes/{instance.resume.id}/experiences/{filename}"

def event_file_path(instance, filename):  # NEW
    return f"resumes/{instance.resume.id}/events/{filename}"

# ───────────────────────────────────────────────────────────────────

class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    edit_token = models.UUIDField(default=uuid.uuid4, editable=False)
    public_share_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    is_published = models.BooleanField("Опубликовано", default=False)

    # Личное
    surname = models.CharField("Фамилия", max_length=100, blank=True)
    name = models.CharField("Имя", max_length=100, blank=True)
    patronymic = models.CharField("Отчество", max_length=100, blank=True)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    location = models.CharField("Место жительства", max_length=120, blank=True)
    citizenship = models.CharField("Гражданство", max_length=80, blank=True)  # NEW
    photo = models.ImageField("Фото", upload_to=user_photo_path, null=True, blank=True)

    # Контакты
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Телефон", max_length=40, blank=True)
    telegram = models.CharField("Telegram", max_length=80, blank=True)
    github = models.URLField("GitHub", blank=True)
    website = models.URLField("Веб-сайт", blank=True)
    leader_id = models.URLField("Leader ID", blank=True)     # NEW
    stepik = models.URLField("Stepik", blank=True)           # NEW
    video_intro = models.URLField("Видео-визитка", blank=True)  # NEW

    # О себе
    desired_role = models.CharField("Желаемая роль", max_length=120, blank=True)
    expected_salary = models.CharField("Желаемая зарплата", max_length=40, blank=True)  # NEW
    EMPLOYMENT_CHOICES = [
        ("full", "Полная"), ("part", "Частичная"), ("internship", "Стажировка"),
        ("project", "Проектная"), ("temporary", "Временная"), ("volunteer", "Волонтёрство"),
    ]
    employment_type = models.CharField("Тип занятости", max_length=20, choices=EMPLOYMENT_CHOICES, blank=True)  # NEW
    WORK_MODE_CHOICES = [("office", "Офис"), ("remote", "Удалённая"), ("hybrid", "Гибрид")]
    work_mode = models.CharField("Формат работы", max_length=10, choices=WORK_MODE_CHOICES, blank=True)  # NEW

    about = models.TextField("Коротко о себе", blank=True)
    languages = models.CharField("Языки", max_length=200, blank=True)

    # Скиллы
    soft_skills = models.TextField("Soft skills", blank=True)
    hard_skills = models.TextField("Hard skills", blank=True)
    computer_skills = models.CharField("Компьютерные навыки (чекбоксы)", max_length=300, blank=True)  # NEW

    # Дополнительно
    military_service = models.BooleanField("Служба в армии", default=False)  # NEW
    drivers_license = models.CharField("Водительские права", max_length=80, blank=True)  # NEW (CSV: A,B,BE,...)
    MARITAL_CHOICES = [
        ("single", "Не женат/не замужем"),
        ("married", "Женат/замужем"),
        ("divorced", "В разводе"),
        ("widowed", "Вдовец/вдова"),
    ]
    marital_status = models.CharField("Семейное положение", max_length=20, choices=MARITAL_CHOICES, blank=True)  # NEW
    relocation_ready = models.BooleanField("Готов к переезду", default=False)  # NEW
    courses = models.TextField("Курсы", blank=True)  # NEW

    created_at = models.DateTimeField(auto_now_add=True)

    def get_public_url(self):
        return f"/r/{self.public_share_id}/"

    def get_pdf_url(self):
        return f"/r/{self.public_share_id}/pdf/"

    def get_edit_url(self):
        return "/builder/"

    @property
    def full_name(self):
        return " ".join([p for p in [self.surname, self.name, self.patronymic] if p])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.photo:
            try:
                path = self.photo.path
                img = Image.open(path).convert("RGB")
                size = min(img.width, img.height)
                left = (img.width - size) / 2
                top = (img.height - size) / 2
                img = img.crop((left, top, left + size, top + size)).resize((360, 360))
                img.save(path, format="JPEG", quality=85)
            except Exception:
                pass

class ProjectEntry(models.Model):
    resume = models.ForeignKey(Resume, related_name="projects", on_delete=models.CASCADE)
    title = models.CharField("Название проекта", max_length=200)
    description = models.TextField("Описание", blank=True)
    external_link = models.URLField("Ссылка", blank=True)
    file = models.FileField("Файл", upload_to=project_file_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class EventEntry(models.Model):
    resume = models.ForeignKey(Resume, related_name="events", on_delete=models.CASCADE)
    CATEGORY_CHOICES = [
        ("achievement", "Достижение"),
        ("event", "Мероприятие"),
        ("award", "Награда"),
        ("grant", "Грант"),
        ("publication", "Научная статья"),  # NEW
        ("volunteer", "Волонтёрство"),
        ("certificate", "Сертификат"),
    ]
    category = models.CharField("Категория", max_length=20, choices=CATEGORY_CHOICES, default="achievement")  # NEW
    name = models.CharField("Мероприятие / достижение / награда / грант", max_length=200)
    role = models.CharField("Роль / статус", max_length=200, blank=True)
    description = models.TextField("Описание", blank=True)
    date = models.CharField("Дата", max_length=100, blank=True)
    links = models.TextField("Ссылки (Drive и др.)", blank=True)
    video_url = models.URLField("Видео (YouTube/VK/Drive)", blank=True)  # NEW
    attachment = models.FileField("Файл", upload_to=event_file_path, null=True, blank=True)  # NEW
    created_at = models.DateTimeField(auto_now_add=True)

class WorkExperience(models.Model):
    resume = models.ForeignKey(Resume, related_name="experiences", on_delete=models.CASCADE)
    company = models.CharField("Компания / организация", max_length=200)
    position = models.CharField("Должность", max_length=200)
    start_date = models.CharField("Начало", max_length=100, blank=True)
    end_date = models.CharField("Окончание / по настоящее время", max_length=100, blank=True)
    description = models.TextField("Обязанности / достижения", blank=True)
    attachment = models.FileField("Вложение", upload_to=experience_file_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class EducationEntry(models.Model):
    resume = models.ForeignKey(Resume, related_name="education", on_delete=models.CASCADE)
    institution = models.CharField("Учебное заведение", max_length=200)
    degree = models.CharField("Степень / программа", max_length=200, blank=True)
    field = models.CharField("Специальность", max_length=200, blank=True)
    start_year = models.CharField("Год начала", max_length=10, blank=True)
    end_year = models.CharField("Год окончания", max_length=10, blank=True)
    description = models.TextField("Курсы, диплом, достижения", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
