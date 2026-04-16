import random

from django.db import models


def upload_to(instance, filename):
    return f'uploads/{instance.unique_key}/{filename}'


class FileUpload(models.Model):
    file = models.FileField(upload_to=upload_to)
    unique_key = models.CharField(max_length=6, unique=True, editable=False, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
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
    def original_filename(self):
        return self.file.name.split('/')[-1]

    def __str__(self):
        return f'{self.unique_key} - {self.original_filename}'
