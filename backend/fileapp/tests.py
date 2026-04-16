import shutil
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
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

    def test_sets_expiry_ten_minutes_after_upload(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('sample.txt', b'hello'))
        self.assertLessEqual(
            abs((upload.expires_at - (upload.uploaded_at + timedelta(minutes=FileUpload.EXPIRY_MINUTES))).total_seconds()),
            2,
        )


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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="once.txt"')
        self.assertFalse(FileUpload.objects.filter(pk=upload.pk).exists())

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

    def test_expired_upload_is_deleted_before_download(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('old.txt', b'old data'))
        upload.expires_at = timezone.now() - timedelta(minutes=1)
        upload.save(update_fields=['expires_at'])

        response = self.client.post('/api/download/', {'key': upload.unique_key}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(FileUpload.objects.filter(pk=upload.pk).exists())

    def test_expired_upload_is_removed_from_files_list(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('status.txt', b'status'))
        upload.expires_at = timezone.now() - timedelta(minutes=1)
        upload.save(update_fields=['expires_at'])

        response = self.client.get('/api/files/', {'keys': upload.unique_key})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_deleted_key_can_be_reused_after_successful_download(self):
        first_upload = FileUpload.objects.create(file=SimpleUploadedFile('first.txt', b'one time'))
        key = first_upload.unique_key
        self.client.post('/api/download/', {'key': key}, format='json')

        with patch.object(FileUpload, 'generate_unique_key', return_value=key):
            second_upload = FileUpload.objects.create(file=SimpleUploadedFile('second.txt', b'next file'))

        self.assertEqual(second_upload.unique_key, key)

    def test_download_schedules_async_file_deletion(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('async.txt', b'async delete'))

        with patch('fileapp.models.delete_file_async') as mocked_delete:
            response = self.client.post('/api/download/', {'key': upload.unique_key}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_delete.assert_called_once()

    def test_expired_cleanup_schedules_async_file_deletion(self):
        upload = FileUpload.objects.create(file=SimpleUploadedFile('expired.txt', b'expired'))
        upload.expires_at = timezone.now() - timedelta(minutes=1)
        upload.save(update_fields=['expires_at'])

        with patch('fileapp.models.delete_file_async') as mocked_delete:
            response = self.client.get('/api/files/', {'keys': upload.unique_key})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_delete.assert_called_once()
