from io import BytesIO
from unittest.mock import patch
from django.test import TestCase,Client
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from .models import Resume,ProjectEntry

class ResumeTests(TestCase):
    def owner(self):
        self.client.get('/');return Resume.objects.get(id=self.client.session['rid'])
    def test_builder_renders(self):
        r=self.client.get('/');self.assertEqual(r.status_code,200)
        self.assertContains(r,'csrfmiddlewaretoken')
    def test_sessions_are_separate(self):
        one=self.owner();other=Client();other.get('/')
        self.assertNotEqual(other.session['rid'],str(one.id))
    def test_create_publish_and_unpublish(self):
        resume=self.owner();self.client.post('/',{'form_kind':'resume','name':'Тест','surname':'Пример','desired_role':'Python developer'})
        self.assertEqual(Client().get(resume.get_public_url()).status_code,404)
        self.client.post('/',{'form_kind':'publish'})
        self.assertContains(Client().get(resume.get_public_url()),'Тест')
        self.client.post('/',{'form_kind':'unpublish'})
        self.assertEqual(Client().get(resume.get_public_url()).status_code,404)
    def test_draft_pdf_is_private(self):
        resume=self.owner();self.assertEqual(Client().get(resume.get_pdf_url()).status_code,404)
        pdf=self.client.get(resume.get_pdf_url());self.assertEqual(pdf.status_code,200)
        self.assertTrue(pdf.content.startswith(b'%PDF-'))
    def test_published_pdf_with_cyrillic(self):
        resume=self.owner();resume.name='Иван';resume.about='Разрабатываю приложения';resume.is_published=True;resume.save()
        pdf=Client().get(resume.get_pdf_url());self.assertEqual(pdf.status_code,200)
        self.assertGreater(len(pdf.content),10000)
    def test_project_ownership(self):
        self.owner();other=Resume.objects.create();item=ProjectEntry.objects.create(resume=other,title='Private')
        self.assertEqual(self.client.post('/',{'form_kind':'project_delete','project_id':item.id}).status_code,404)
        self.assertTrue(ProjectEntry.objects.filter(id=item.id).exists())
    def test_external_redirect_rejected(self):
        response=self.client.post('/',{'form_kind':'publish','next':'//example.com/'})
        self.assertEqual(response.status_code,302);self.assertFalse(response['Location'].startswith('//'))
    def test_media_private_and_ai_offline(self):
        resume=self.owner();raw=BytesIO();Image.new('RGB',(20,20),(10,40,90)).save(raw,format='JPEG')
        resume.photo=SimpleUploadedFile('synthetic.jpg',raw.getvalue(),content_type='image/jpeg');resume.save()
        url=resume.photo.url
        self.assertEqual(Client().get(url).status_code,404)
        self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.get('/media/resumes/not-a-uuid/photo/x.jpg').status_code,404)
        self.assertEqual(self.client.get(f'/media/resumes/{resume.id}/../../elsewhere/photo/x.jpg').status_code,404)
        with patch('app.views.requests.post') as network:
            self.assertEqual(self.client.get('/ai-describe/',{'skills':'Python, SQL'}).status_code,200)
            network.assert_not_called()
