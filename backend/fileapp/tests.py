import shutil
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from .models import FileUpload


TEMP_MEDIA_ROOT = Path(__file__).resolve().parent.parent / 'test_media'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FileUploadModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        TEMP_MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_generates_unique_six_digit_key(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('sample.txt', b'hello'))
        self.assertEqual(len(upload.unique_key), 6)
        self.assertTrue(upload.unique_key.isdigit())

    def test_default_status_is_pending(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('sample.txt', b'hello'))
        self.assertFalse(upload.is_downloaded)
        self.assertEqual(upload.status, FileUpload.Status.PENDING)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FileUploadApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        TEMP_MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()

    def test_upload_returns_key_and_saves_file(self):
        response = self.client.post(
            '/api/upload/',
            {'file': SimpleUploadedFile('hello.txt', b'hello world')},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('key', response.data)
        self.assertEqual(FileUpload.objects.count(), 1)

    def test_download_returns_file_once(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('once.txt', b'one time'))
        response = self.client.post('/api/download/', {'key': upload.unique_key}, format='json')

        upload.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="once.txt"')
        self.assertTrue(upload.is_downloaded)
        self.assertIsNotNone(upload.downloaded_at)

        second_response = self.client.post('/api/download/', {'key': upload.unique_key}, format='json')
        self.assertEqual(second_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_key_returns_error(self):
        response = self.client.post('/api/download/', {'key': '999999'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Invalid or expired key.')

    def test_files_endpoint_returns_metadata(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('status.txt', b'status'))
        response = self.client.get('/api/files/', {'keys': upload.unique_key})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], upload.unique_key)
