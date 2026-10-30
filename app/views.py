# views.py
import os
import requests
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_GET
from django.utils.http import url_has_allowed_host_and_scheme

from .models import (
    Resume, ProjectEntry, EventEntry, WorkExperience, EducationEntry
)
from .forms import (
    ResumeForm, ProjectEntryForm, EventEntryForm,
    WorkExperienceForm, EducationEntryForm
)

# ───────────────────────────────────────────────────────────────────────────────
# AI (OpenRouter / DeepSeek)
# ───────────────────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1")
BLACKLIST = {"бухаю", "алкоголь", "наркотики", "курю"}


def home(request):
    return redirect("builder")


def _sanitize(raw: str) -> str:
    parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    parts = [p for p in parts if p.lower() not in BLACKLIST]
    return ", ".join(parts)


def _ai_describe(skills: str) -> str:
    if not OPENROUTER_API_KEY or os.getenv("OPENROUTER_ENABLED", "0") != "1":
        return ""
    prompt = (
        "Сформулируй 1–2 аккуратных предложения для резюме на русском. "
        "Пиши по делу, без преувеличений. Если упомянуты шахматы/шашки — добавь про стратегическое и критическое мышление.\n"
        f"Навыки: {skills}\nОтвет:"
    )
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": OPENROUTER_MODEL, "messages": [{"role": "user", "content": prompt}]},
            timeout=20,
        )
        if r.status_code != 200:
            return ""
        data = r.json()
        return (data["choices"][0]["message"]["content"] or "").strip()[:4000]
    except Exception:
        return ""


def _get_or_create_resume_in_session(request):
    rid = request.session.get("rid")
    if rid:
        try:
            return Resume.objects.get(id=rid)
        except Resume.DoesNotExist:
            pass
    r = Resume.objects.create()
    request.session["rid"] = str(r.id)
    request.session["rtok"] = str(r.edit_token)
    return r


def _redirect_next(request, default_name="builder"):
    nxt = request.POST.get("next") or request.GET.get("next")
    # минимальная защита, чтобы оставаться в пределах сайта
    if nxt and isinstance(nxt, str) and nxt.startswith("/") and len(nxt) < 2048 and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    return redirect(default_name)


# ───────────────────────────────────────────────────────────────────────────────
# Единая страница-конструктор
# ───────────────────────────────────────────────────────────────────────────────
@require_http_methods(["GET", "POST"])
def builder(request):
    """
    Несколько независимых форм на одной странице.
    Каждая отправляет: form_kind + next (якорь секции), чтобы после POST
    оставаться в той же секции без «прыжка» страницы.
    """
    resume = _get_or_create_resume_in_session(request)

    if request.method == "POST":
        kind = request.POST.get("form_kind", "").strip()

        # Публикация (после этого внизу появляются ссылки)
        if kind in {"publish", "unpublish"}:
            resume.is_published = kind == "publish"
            resume.save(update_fields=["is_published"])
            return _redirect_next(request)

        # Шапка/контакты/скиллы
        if kind == "resume":
            form = ResumeForm(request.POST, request.FILES, instance=resume)
            if form.is_valid():
                form.save()
            return _redirect_next(request)

        # Проекты
        if kind == "project_add":
            f = ProjectEntryForm(request.POST, request.FILES)
            if f.is_valid():
                obj = f.save(commit=False)
                obj.resume = resume
                obj.save()
            return _redirect_next(request)

        if kind == "project_edit":
            pid = request.POST.get("project_id")
            obj = get_object_or_404(ProjectEntry, id=pid, resume=resume)
            f = ProjectEntryForm(request.POST, request.FILES, instance=obj, prefix=f"pr{obj.id}")
            if f.is_valid():
                f.save()
            return _redirect_next(request)

        if kind == "project_delete":
            pid = request.POST.get("project_id")
            get_object_or_404(ProjectEntry, id=pid, resume=resume).delete()
            return _redirect_next(request)

        # Достижения/мероприятия/гранты
       # Достижения/мероприятия/гранты
        if kind == "event_add":
            f = EventEntryForm(request.POST, request.FILES)  # ← добавили FILES
            if f.is_valid():
                obj = f.save(commit=False)
                obj.resume = resume
                obj.save()
            return _redirect_next(request)

        if kind == "event_edit":
            eid = request.POST.get("event_id")
            obj = get_object_or_404(EventEntry, id=eid, resume=resume)
            f = EventEntryForm(request.POST, request.FILES, instance=obj, prefix=f"ev{obj.id}")  # ← FILES
            if f.is_valid():
                f.save()
            return _redirect_next(request)


        if kind == "event_delete":
            eid = request.POST.get("event_id")
            get_object_or_404(EventEntry, id=eid, resume=resume).delete()
            return _redirect_next(request)

        # Опыт работы
        if kind == "experience_add":
            f = WorkExperienceForm(request.POST, request.FILES)
            if f.is_valid():
                obj = f.save(commit=False)
                obj.resume = resume
                obj.save()
            return _redirect_next(request)

        if kind == "experience_edit":
            xid = request.POST.get("experience_id")
            obj = get_object_or_404(WorkExperience, id=xid, resume=resume)
            f = WorkExperienceForm(request.POST, request.FILES, instance=obj, prefix=f"ex{obj.id}")
            if f.is_valid():
                f.save()
            return _redirect_next(request)

        if kind == "experience_delete":
            xid = request.POST.get("experience_id")
            get_object_or_404(WorkExperience, id=xid, resume=resume).delete()
            return _redirect_next(request)

        # Образование
        if kind == "education_add":
            f = EducationEntryForm(request.POST)
            if f.is_valid():
                obj = f.save(commit=False)
                obj.resume = resume
                obj.save()
            return _redirect_next(request)

        if kind == "education_edit":
            eid = request.POST.get("education_id")
            obj = get_object_or_404(EducationEntry, id=eid, resume=resume)
            f = EducationEntryForm(request.POST, instance=obj, prefix=f"ed{obj.id}")
            if f.is_valid():
                f.save()
            return _redirect_next(request)

        if kind == "education_delete":
            eid = request.POST.get("education_id")
            get_object_or_404(EducationEntry, id=eid, resume=resume).delete()
            return _redirect_next(request)

        return HttpResponseBadRequest("unknown form_kind")

    # GET
    ctx = dict(
        resume=resume,
        form=ResumeForm(instance=resume),

        project_form=ProjectEntryForm(),
        pr_edit_forms=[(p, ProjectEntryForm(instance=p, prefix=f"pr{p.id}"))
                       for p in resume.projects.all()],

        event_form=EventEntryForm(),
        ev_edit_forms=[(ev, EventEntryForm(instance=ev, prefix=f"ev{ev.id}"))
                       for ev in resume.events.all()],

        experience_form=WorkExperienceForm(),
        exp_edit_forms=[(x, WorkExperienceForm(instance=x, prefix=f"ex{x.id}"))
                        for x in resume.experiences.all()],

        education_form=EducationEntryForm(),
        edu_edit_forms=[(ed, EducationEntryForm(instance=ed, prefix=f"ed{ed.id}"))
                        for ed in resume.education.all()],

        public_url_full=request.build_absolute_uri(resume.get_public_url()),
        pdf_url_full=request.build_absolute_uri(resume.get_pdf_url()),
        edit_url_full=request.build_absolute_uri(resume.get_edit_url()),
    )
    return render(request, "builder.html", ctx)


import re
from datetime import datetime

def _date_sortkey(s: str):
    """Пытаемся извлечь dd.mm.yyyy или yyyy для сортировки (по убыванию)."""
    s = (s or "").strip()
    m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', s)
    if m:
        d, mth, y = map(int, m.groups())
        return (y, mth, d)
    m = re.search(r'(\d{4})', s)
    if m:
        y = int(m.group(1))
        return (y, 0, 0)
    return (0, 0, 0)

def public_resume(request, share_id):
    resume = get_object_or_404(Resume, public_share_id=share_id, is_published=True)

    # собираем «ленточку времени»
    timeline = []
    for e in resume.events.all():
        timeline.append({
            "date": e.date or "",
            "key": _date_sortkey(e.date),
            "title": f"{e.name} — {dict(e.CATEGORY_CHOICES).get(e.category, e.category)}",
        })
    for x in resume.experiences.all():
        if x.start_date:
            timeline.append({"date": x.start_date, "key": _date_sortkey(x.start_date), "title": f"Начало работы — {x.company}"})
        if x.end_date:
            timeline.append({"date": x.end_date, "key": _date_sortkey(x.end_date), "title": f"Окончание работы — {x.company}"})
    for p in resume.projects.all():
        timeline.append({"date": p.created_at.strftime("%d.%m.%Y"), "key": _date_sortkey(p.created_at.strftime("%d.%m.%Y")), "title": f"Проект — {p.title}"})
    for ed in resume.education.all():
        if ed.start_year:
            timeline.append({"date": ed.start_year, "key": _date_sortkey(ed.start_year), "title": f"Начало обучения — {ed.institution}"})
        if ed.end_year:
            timeline.append({"date": ed.end_year, "key": _date_sortkey(ed.end_year), "title": f"Окончание обучения — {ed.institution}"})

    timeline.sort(key=lambda it: it["key"], reverse=True)

    return render(request, "public_resume.html", {"resume": resume, "timeline": timeline})


@require_GET
def ai_describe(request):
    skills = _sanitize(request.GET.get("skills", "")[:2000])
    if not skills:
        return JsonResponse({"summary": ""})
    text = _ai_describe(skills)
    if not text:
        parts = [s.strip() for s in skills.split(",") if s.strip()]
        if parts:
            extra = (
                " Это подчёркивает стратегическое и критическое мышление."
                if any(w in skills.lower() for w in ("шахматы", "шашки")) else ""
            )
            text = f"Ключевые навыки: {', '.join(parts[:4])}.{extra}"
        else:
            text = ""
    text = " ".join(text.replace("\n", " ").split())
    if text and not text.endswith("."):
        text += "."
    return JsonResponse({"summary": text})


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                           PDF BLOCK (ReportLab)                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
# ===========================
# PDF (ReportLab) блок — FIX
# ===========================
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph, Table, TableStyle, Spacer, Image as RLImage,
    SimpleDocTemplate, KeepTogether
)

def _esc(s: str) -> str:
    return _xml_escape((s or "").strip())

def _mk_styles():
    # Кириллица: пытаемся подключить DejaVuSans
    font_path = finders.find("fonts/DejaVuSans.ttf")
    if font_path and "DejaVuSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    font_name = "DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica"

    base = getSampleStyleSheet()
    base["Normal"].fontName = font_name
    base["Normal"].fontSize = 10
    base["Normal"].leading = 13

    styles = {
        "Normal": base["Normal"],
        "H1": ParagraphStyle(
            "H1", parent=base["Normal"], fontSize=18, leading=22,
            spaceAfter=6, textColor=colors.HexColor("#0f172a")
        ),
        "H2": ParagraphStyle(
            "H2", parent=base["Normal"], fontSize=13, leading=16,
            spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#0f172a")
        ),
        "Sub": ParagraphStyle(
            "Sub", parent=base["Normal"], fontSize=11, leading=14,
            textColor=colors.HexColor("#334155")
        ),
        "Small": ParagraphStyle(
            "Small", parent=base["Normal"], fontSize=9, leading=11,
            textColor=colors.HexColor("#6b7280")
        ),
        "Muted": ParagraphStyle(
            "Muted", parent=base["Normal"], textColor=colors.HexColor("#6b7280")
        ),
        "Bold": ParagraphStyle(
            "Bold", parent=base["Normal"], fontName=font_name, leading=13
        ),
    }
    return styles

def _kv(label: str, value: str, ss) -> Paragraph:
    """Пара «Метка: значение», если пусто — «—»."""
    val = _esc(value) if (value and str(value).strip()) else "—"
    return Paragraph(f"<b>{_esc(label)}:</b> {val}", ss["Normal"])

def _make_header_block(resume, ss):
    # Левая колонка
    fullname = resume.full_name if resume.full_name else "Без имени"
    left_items = [
        Paragraph(_esc(fullname), ss["H1"]),
    ]
    if resume.desired_role or resume.location:
        meta = " • ".join([p for p in [_esc(resume.desired_role), _esc(resume.location)] if p])
        left_items.append(Paragraph(meta, ss["Sub"]))

    left_items += [
        Spacer(1, 2*mm),
        _kv("Дата рождения", resume.birth_date.strftime("%d.%m.%Y") if resume.birth_date else "", ss),
        _kv("Гражданство", resume.citizenship, ss),                                       # NEW
        _kv("Email", resume.email, ss),
        _kv("Телефон", resume.phone, ss),
        _kv("Telegram", resume.telegram, ss),
        _kv("GitHub", resume.github, ss),
        _kv("Веб-сайт", resume.website, ss),
        _kv("Leader ID", resume.leader_id, ss),                                           # NEW
        _kv("Stepik", resume.stepik, ss),                                                 # NEW
        _kv("Видео-визитка", resume.video_intro, ss),                                     # NEW
        _kv("Языки", resume.languages, ss),
        Spacer(1, 2*mm),
        _kv("Желаемая роль", resume.desired_role, ss),
        _kv("Тип занятости", dict(resume.EMPLOYMENT_CHOICES).get(resume.employment_type, ""), ss),   # NEW
        _kv("Формат работы", dict(resume.WORK_MODE_CHOICES).get(resume.work_mode, ""), ss),          # NEW
        _kv("Желаемая ЗП", resume.expected_salary, ss),                                              # NEW
        _kv("О себе", resume.about, ss),
        _kv("Soft skills", resume.soft_skills, ss),
        _kv("Hard skills", resume.hard_skills, ss),
        _kv("Компьютерные навыки", resume.computer_skills.replace(",", ", "), ss),        # NEW
        _kv("Служба в армии", "Да" if resume.military_service else "", ss),              # NEW
        _kv("Права", resume.drivers_license.replace(",", ", "), ss),                      # NEW
        _kv("Семейное положение", dict(resume.MARITAL_CHOICES).get(resume.marital_status, ""), ss),  # NEW
        _kv("Готов к переезду", "Да" if resume.relocation_ready else "Нет", ss),         # NEW
        _kv("Курсы", resume.courses, ss),                                                 # NEW
    ]


    # Рендерим левую колонку как таблицу-одноколоночник (без KeepInFrame!)
    left_tbl = Table([[itm] for itm in left_items], colWidths=[125*mm])
    left_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))

    # Правая колонка — фото строго ограничено
    if resume.photo and getattr(resume.photo, "path", None):
        try:
            ph = RLImage(resume.photo.path)
            ph._restrictSize(38*mm, 38*mm)  # вписать в квадрат 38×38 мм, без переполнений
            photo_cell = ph
        except Exception:
            photo_cell = Paragraph("Фото: —", ss["Small"])
    else:
        photo_cell = Paragraph("Фото: —", ss["Small"])

    photo_tbl = Table([[photo_cell]], colWidths=[45*mm], rowHeights=[40*mm])
    photo_tbl.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.25, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))

    header = Table([[left_tbl, photo_tbl]], colWidths=[125*mm, 45*mm])
    header.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    return KeepTogether([header, Spacer(1, 4*mm)])

def _section(title: str, table_or_flowable, ss):
    return [
        Spacer(1, 3*mm),
        Paragraph(_esc(title), ss["H2"]),
        Spacer(1, 1*mm),
        table_or_flowable,
    ]

def _mk_exp_table(resume, ss):
    exps = list(resume.experiences.all())
    if not exps:
        return Paragraph("—", ss["Muted"])

    rows = []
    for ex in exps:
        # внутренний «вертикальный стек» — тоже таблицей, без KeepInFrame
        inner_rows = [
            [Paragraph(_esc(ex.position or "—"), ss["Bold"])],
            [Paragraph(_esc(ex.company or "—"), ss["Normal"])],
            [Paragraph(_esc(f"{ex.start_date or '—'} — {ex.end_date or '—'}"), ss["Small"])],
            [Spacer(1, 1*mm)],
            [Paragraph(_esc(ex.description or "—"), ss["Normal"])],
        ]
        inner = Table(inner_rows, colWidths=[170*mm])
        inner.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        rows.append([inner])

    t = Table(rows, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("LINEBELOW", (0,0), (-1,-2), 0.25, colors.HexColor("#e5e7eb")),
    ]))
    return t

def _mk_proj_table(resume, ss):
    prs = list(resume.projects.all())
    if not prs:
        return Paragraph("—", ss["Muted"])

    rows = []
    for p in prs:
        inner_rows = [
            [Paragraph(_esc(p.title or "—"), ss["Bold"])],
            [Paragraph(_esc(p.external_link or "—"), ss["Small"])],
            [Spacer(1, 1*mm)],
            [Paragraph(_esc(p.description or "—"), ss["Normal"])],
        ]
        inner = Table(inner_rows, colWidths=[170*mm])
        inner.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        rows.append([inner])

    t = Table(rows, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("LINEBELOW", (0,0), (-1,-2), 0.25, colors.HexColor("#e5e7eb")),
    ]))
    return t

def _mk_event_table(resume, ss):
    evs = list(resume.events.all())
    if not evs:
        return Paragraph("—", ss["Muted"])

    rows = []
    for e in evs:
        cat = dict(e.CATEGORY_CHOICES).get(e.category, e.category)
        head_text = f"{e.name or '—'}{f' ({e.role})' if getattr(e, 'role', None) else ''} — {cat}"
        extra_lines = []
        if e.video_url:
            extra_lines.append(f"Видео: {e.video_url}")
        if e.links:
            extra_lines.append(f"Ссылки: {e.links}")
        if e.attachment:
            extra_lines.append(f"Файл: {e.attachment.name.split('/')[-1]}")

        inner_rows = [
            [Paragraph(_esc(head_text), ss["Bold"])],
            [Paragraph(_esc(getattr(e, 'date', '') or '—'), ss["Small"])],
            [Spacer(1, 1*mm)],
            [Paragraph(_esc(e.description or "—"), ss["Normal"])],
        ]
        for line in extra_lines:
            inner_rows.append([Paragraph(_esc(line), ss["Small"])])
        inner = Table(inner_rows, colWidths=[170*mm])
        inner.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        rows.append([inner])

    t = Table(rows, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("LINEBELOW", (0,0), (-1,-2), 0.25, colors.HexColor("#e5e7eb")),
    ]))
    return t


def _mk_edu_table(resume, ss):
    eds = list(resume.education.all())
    if not eds:
        return Paragraph("—", ss["Muted"])

    rows = []
    for ed in eds:
        title = " / ".join([p for p in [_esc(ed.institution or "—"), _esc(ed.degree or ""), _esc(ed.field or "")] if p])
        inner_rows = [
            [Paragraph(title, ss["Bold"])],
            [Paragraph(_esc(f"{ed.start_year or '—'} — {ed.end_year or '—'}"), ss["Small"])],
            [Spacer(1, 1*mm)],
            [Paragraph(_esc(ed.description or "—"), ss["Normal"])],
        ]
        inner = Table(inner_rows, colWidths=[170*mm])
        inner.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        rows.append([inner])

    t = Table(rows, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("LINEBELOW", (0,0), (-1,-2), 0.25, colors.HexColor("#e5e7eb")),
    ]))
    return t

def resume_pdf(request, share_id):
    resume = get_object_or_404(Resume, public_share_id=share_id)
    if not resume.is_published and str(resume.id) != request.session.get("rid"):
        from django.http import Http404
        raise Http404

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="resume-{resume.id}.pdf"'
    doc = SimpleDocTemplate(
        resp,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=16*mm, bottomMargin=16*mm,
        title=f"Резюме — {resume.full_name or 'Без имени'}"
    )

    ss = _mk_styles()
    story = []
    story.append(_make_header_block(resume, ss))
    story.extend(_section("Опыт работы", _mk_exp_table(resume, ss), ss))
    story.extend(_section("Проекты", _mk_proj_table(resume, ss), ss))
    story.extend(_section("Достижения / мероприятия / награды / гранты / научные статьи",
                      _mk_event_table(resume, ss), ss))

    story.extend(_section("Образование", _mk_edu_table(resume, ss), ss))

    doc.build(story)
    return resp

