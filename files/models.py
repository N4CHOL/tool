from django.db import models

class File(models.Model):
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FilePathField(path="/uploads")

    def __str__(self):
        return self.name
