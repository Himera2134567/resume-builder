from pathlib import PurePosixPath
from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import Http404
from django.core.exceptions import ValidationError
from django.urls import path, include
from django.views.static import serve
from app.models import Resume

def local_static(request,path):
    file = finders.find(path)
    if not file: raise Http404
    from pathlib import Path
    return serve(request,Path(file).name,document_root=Path(file).parent)

def private_media(request,path):
    parts=PurePosixPath(path).parts
    if len(parts)<4 or parts[0]!='resumes' or '..' in parts or '\\' in path: raise Http404
    try: resume=Resume.objects.get(id=parts[1])
    except (Resume.DoesNotExist,ValueError,ValidationError): raise Http404
    if not resume.is_published and str(resume.id)!=request.session.get('rid'): raise Http404
    response=serve(request,path,document_root=settings.MEDIA_ROOT)
    if parts[2]!='photo': response['Content-Disposition']='attachment'
    response['X-Content-Type-Options']='nosniff'
    return response

urlpatterns=[path('',include('app.urls')),path('static/<path:path>',local_static),path('media/<path:path>',private_media)]
