# Generated by Django 5.1.3 on 2024-11-12 17:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Skill",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("skill_name", models.CharField(max_length=200)),
                (
                    "descr",
                    models.CharField(
                        blank=True, default=None, max_length=200, null=True
                    ),
                ),
            ],
            options={
                "ordering": ["skill_name"],
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("user_name", models.CharField(max_length=200)),
                (
                    "position",
                    models.CharField(
                        blank=True, default=None, max_length=200, null=True
                    ),
                ),
                (
                    "resume_url",
                    models.CharField(
                        blank=True, default=None, max_length=400, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(verbose_name="created_at")),
                ("skills", models.ManyToManyField(to="risk_check.skill")),
            ],
            options={
                "ordering": ["user_name"],
            },
        ),
        migrations.CreateModel(
            name="Result",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "risk_index",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=None,
                        max_digits=4,
                        null=True,
                    ),
                ),
                (
                    "job_poll",
                    models.PositiveIntegerField(blank=True, default=0, null=True),
                ),
                (
                    "avg_salary",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=None,
                        max_digits=8,
                        null=True,
                    ),
                ),
                (
                    "industrial_risk_index",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=None,
                        max_digits=4,
                        null=True,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="risk_check.user",
                    ),
                ),
            ],
            options={
                "ordering": ["user_id"],
            },
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                (
                    "descr",
                    models.CharField(
                        blank=True, default=None, max_length=200, null=True
                    ),
                ),
                ("url", models.CharField(max_length=400)),
                ("status", models.BooleanField(blank=True, default=True, null=True)),
                ("reach_count", models.PositiveIntegerField(default=0)),
                ("click_count", models.PositiveIntegerField(default=0)),
                ("users", models.ManyToManyField(to="risk_check.user")),
            ],
            options={
                "ordering": ["title"],
            },
        ),
    ]
