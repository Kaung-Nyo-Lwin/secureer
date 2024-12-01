from django.db import models
from django.contrib.auth.models import User as AuthUser

class Skill(models.Model):
    skill_name = models.CharField(max_length=200)
    descr = models.CharField(max_length=200, default=None, blank=True, null=True)

    class Meta:
        ordering = ["skill_name"]

    def __str__(self):
        return self.skill_name

class User(models.Model):
    skills = models.ManyToManyField(Skill)

    user_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200, default=None, blank=True, null=True)
    resume_url = models.CharField(max_length=400, default=None, blank=True, null=True)
    created_at = models.DateTimeField("created_at")

    class Meta:
        ordering = ["user_name"]

    def __str__(self):
        return self.user_name

class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    matched_skills =  models.ManyToManyField(Skill)
    recommended_skills =  models.JSONField(default=None, blank=True, null=True)
    recommended_jobs = models.JSONField(default=None, blank=True, null=True)

    # job_poll = models.PositiveIntegerField(default=0, blank=True, null=True)
    # avg_salary = models.DecimalField(max_digits=8, decimal_places=2, default=None, blank=True, null=True)
    # industrial_risk_index = models.DecimalField(max_digits=4, decimal_places=2, default=None, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return str(self.id)

class Post(models.Model):
    created_by = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name='post_created_by', default=None, blank=True, null=True)
    skills = models.ManyToManyField(Skill)

    title = models.CharField(max_length=200)
    descr = models.CharField(max_length=200, default=None, blank=True, null=True)
    url = models.CharField(max_length=400)
    status = models.BooleanField(default=True, blank=True, null=True)
    reach_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

# class Click(models.Model):
#     user = models.ForeignKey(Users, on_delete=models.CASCADE)
#     post = models.ForeignKey(Posts, on_delete=models.CASCADE)
#     created_at = models.DateTimeField("created_at")

# class Generated_reports(models.Model):



