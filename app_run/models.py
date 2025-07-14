from django.db import models
from django.contrib.auth.models import User


class Run(models.Model):
    INIT = 'init'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'

    STATUS = [
        (INIT, 'init'),
        (IN_PROGRESS, 'in_progress'),
        (FINISHED, 'finished')
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, related_name='runs')
    status = models.CharField(choices=STATUS, default=INIT)

    def __str__(self):
        return f'{self.athlete}'


class AthleteInfo(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='athlete_info')
    goals = models.TextField(default=None)
    weight = models.IntegerField(default=None)
