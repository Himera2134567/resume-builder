from django import forms
from .models import Resume, ProjectEntry, EventEntry, WorkExperience, EducationEntry

DRIVER_CHOICES = [("A","A"),("B","B"),("BE","BE"),("C","C"),("CE","CE"),("D","D"),("DE","DE"),("M","M"),("TB","ТБ"),("TM","ТМ")]
COMP_CHOICES = [
    ("print", "Печать/сканирование/копирование"),
    ("internet", "Интернет"),
    ("email", "Электронная почта"),
    ("word", "Microsoft Word"),
    ("excel", "Microsoft Excel"),
    ("ppt", "Microsoft PowerPoint"),
]

class ResumeForm(forms.ModelForm):
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    drivers_license = forms.MultipleChoiceField(
        label="Водительские права (категории)", required=False,
        choices=DRIVER_CHOICES, widget=forms.CheckboxSelectMultiple
    )
    computer_skills = forms.MultipleChoiceField(
        label="Владение компьютером", required=False,
        choices=COMP_CHOICES, widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Resume
        fields = [
            # личное
            "surname","name","patronymic","birth_date","location","citizenship","photo",
            # контакты
            "email","phone","telegram","github","website","leader_id","stepik","video_intro",
            # о себе
            "desired_role","employment_type","work_mode","expected_salary","about","languages",
            # скиллы
            "soft_skills","hard_skills","computer_skills",
            # дополнительно
            "military_service","drivers_license","marital_status","relocation_ready","courses",
        ]
        widgets = {
            "about": forms.Textarea(attrs={"rows":3, "placeholder":"2–3 предложения: сильные стороны, цели."}),
            "soft_skills": forms.Textarea(attrs={"rows":4, "placeholder":"Коммуникация, наставничество…"}),
            "hard_skills": forms.Textarea(attrs={"rows":4, "placeholder":"Python, C++, Docker, SQL…"}),
            "languages": forms.Textarea(attrs={"rows":2, "placeholder":"Русский — родной, English — B2…"}),
            "courses": forms.Textarea(attrs={"rows":3, "placeholder":"Курсы/сертификаты…"}),
        }

    # инициализация чекбоксов из CSV
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance
        if inst and inst.drivers_license:
            self.initial["drivers_license"] = [p.strip() for p in inst.drivers_license.split(",") if p.strip()]
        if inst and inst.computer_skills:
            self.initial["computer_skills"] = [p.strip() for p in inst.computer_skills.split(",") if p.strip()]

    # склейка обратно в CSV
    def clean_drivers_license(self):
        items = self.cleaned_data.get("drivers_license") or []
        return ",".join(items)

    def clean_computer_skills(self):
        items = self.cleaned_data.get("computer_skills") or []
        return ",".join(items)

class ProjectEntryForm(forms.ModelForm):
    class Meta:
        model = ProjectEntry
        fields = ["title", "description", "external_link", "file"]
        widgets = {"description": forms.Textarea(attrs={"rows":3})}

class EventEntryForm(forms.ModelForm):
    class Meta:
        model = EventEntry
        fields = ["category","name","role","description","date","links","video_url","attachment"]
        widgets = {
            "description": forms.Textarea(attrs={"rows":3}),
            "links": forms.Textarea(attrs={"rows":2, "placeholder":"https://drive.google.com/...  https://disk.yandex.ru/..."}),
        }

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ["company", "position", "start_date", "end_date", "description", "attachment"]
        widgets = {"description": forms.Textarea(attrs={"rows":4})}

class EducationEntryForm(forms.ModelForm):
    class Meta:
        model = EducationEntry
        fields = ["institution","degree","field","start_year","end_year","description"]
        widgets = {"description": forms.Textarea(attrs={"rows":3})}
