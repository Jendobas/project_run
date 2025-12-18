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
    distance = models.FloatField(default=0.0, blank=True, null=True)
    run_time_seconds = models.IntegerField(default=None)

    def __str__(self):
        return f'{self.athlete}'


class AthleteInfo(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='athlete_info')
    goals = models.TextField(default=None)
    weight = models.IntegerField(default=None)


class Challenge(models.Model):
    full_name = models.CharField()
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge')


class Position(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    latitude = models.FloatField(default=None)
    longitude = models.FloatField(default=None)
    date_time = models.DateTimeField(null=True, blank=True)


class CollectibleItem(models.Model):
    name = models.CharField()
    uid = models.CharField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    picture = models.CharField()
    value = models.IntegerField()
    users = models.ManyToManyField(User, related_name='collectible_items')
