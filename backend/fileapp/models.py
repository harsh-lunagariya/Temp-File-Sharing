import random
from datetime import timedelta

from django.db import models
from django.utils import timezone

from .cleanup import delete_file_async


def upload_to(instance, filename):
    return f'uploads/{instance.unique_key}/{filename}'


def default_expires_at():
    return timezone.now() + timedelta(minutes=FileUpload.EXPIRY_MINUTES)


class FileUpload(models.Model):
    EXPIRY_MINUTES = 10

    file = models.FileField(upload_to=upload_to)
    unique_key = models.CharField(max_length=6, unique=True, editable=False, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expires_at, editable=False)
    is_downloaded = models.BooleanField(default=False)
    downloaded_at = models.DateTimeField(null=True, blank=True)

    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        DOWNLOADED = 'Downloaded', 'Downloaded'

    def save(self, *args, **kwargs):
        if not self.unique_key:
            self.unique_key = self.generate_unique_key()
        super().save(*args, **kwargs)

    @classmethod
    def generate_unique_key(cls):
        for _ in range(100):
            key = f'{random.randint(0, 999999):06d}'
            if not cls.objects.filter(unique_key=key).exists():
                return key
        raise RuntimeError('Unable to generate a unique 6-digit key.')

    @property
    def status(self):
        return self.Status.DOWNLOADED if self.is_downloaded else self.Status.PENDING

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def original_filename(self):
        return self.file.name.split('/')[-1]

    def __str__(self):
        return f'{self.unique_key} - {self.original_filename}'

    def get_file_path(self):
        if not self.file:
            return None

        self.file.close()
        if getattr(self.file, 'file', None):
            self.file.file.close()

        return getattr(self.file, 'path', None)

    def schedule_file_deletion(self):
        delete_file_async(self.get_file_path())

    @classmethod
    def cleanup_expired(cls):
        expired_uploads = cls.objects.filter(expires_at__lte=timezone.now())
        for upload in expired_uploads:
            upload.schedule_file_deletion()
            upload.delete()
