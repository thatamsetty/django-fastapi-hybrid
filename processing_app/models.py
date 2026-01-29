from django.db import models

class ProjectStatus(models.Model):
    project_id = models.CharField(max_length=100, unique=True)

    active = models.BooleanField(default=False)
    running = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_id
