from typing import ClassVar

from django.contrib.auth.models import User as AuthUser
from django.db import models


class Skill(models.Model):
    skill_name = models.CharField(max_length=200)
    descr = models.CharField(max_length=200, default=None, blank=True, null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["skill_name"]

    def __str__(self):
        return self.skill_name


class User(models.Model):
    """An assessment profile, independent of Django's authenticated admin users."""

    skills = models.ManyToManyField(Skill)
    user_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200, default=None, blank=True, null=True)
    resume_url = models.CharField(max_length=400, default=None, blank=True, null=True)
    created_at = models.DateTimeField("created_at")

    class Meta:
        ordering: ClassVar[list[str]] = ["user_name"]

    def __str__(self):
        return self.user_name


class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    matched_skills = models.ManyToManyField(
        Skill, related_name="matched_skills", blank=True
    )
    risk_index = models.DecimalField(
        max_digits=5, decimal_places=2, default=None, blank=True, null=True
    )
    recommended_skills = models.JSONField(default=None, blank=True, null=True)
    recommended_jobs = models.JSONField(default=None, blank=True, null=True)
    analysis = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["id"]

    def __str__(self):
        return f"Assessment {self.pk}"


class Post(models.Model):
    created_by = models.ForeignKey(
        AuthUser,
        on_delete=models.CASCADE,
        related_name="post_created_by",
        default=None,
        blank=True,
        null=True,
    )
    skills = models.ManyToManyField(Skill, related_name="post_skills", blank=True)
    title = models.CharField(max_length=200)
    descr = models.CharField(max_length=200, default=None, blank=True, null=True)
    url = models.CharField(max_length=400)
    status = models.BooleanField(default=True, blank=True, null=True)
    reach_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering: ClassVar[list[str]] = ["title"]

    def __str__(self):
        return self.title
