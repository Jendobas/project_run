from django.db import models
from django.contrib.auth.models import User


class Run(models.Model):
    INIT = 'init'
    IN_PROGRESS = 'in_progres'
    FINISHED = 'finished'

    STATUS = [
        (INIT, 'init'),
        (IN_PROGRESS, 'in_progres'),
        (FINISHED, 'finished')
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()
    athlete = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS, default=INIT)

    def __str__(self):
        return f'{self.athlete}'
