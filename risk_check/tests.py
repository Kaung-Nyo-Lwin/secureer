"""Regression coverage for the public assessment flow and its trust boundaries."""

import json
import os
import subprocess
import sys
from copy import deepcopy
from decimal import Decimal
from typing import ClassVar
from unittest.mock import patch

from django.conf import settings
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .forms import AssessmentForm
from .models import Result, Skill, User
from .services import (
    AssessmentUnavailable,
    DemoEngine,
    assess,
    risk_summary,
    split_skills,
)


class AssessmentFormTests(SimpleTestCase):
    def form(self, **changes):
        return AssessmentForm(
            {"position": "Marketing Manager", "skills": "Marketing", **changes}
        )

    def test_name_is_optional(self):
        form = self.form()
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user_name"], "")

    def test_skills_are_trimmed_and_deduplicated(self):
        form = self.form(skills=" Python, python; Leadership\n  Market   Research ")
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["skills"], ["Python", "Leadership", "Market Research"]
        )

    def test_legacy_tagify_input_is_supported(self):
        form = self.form(skills=json.dumps([{"value": "Python"}, {"value": "SQL"}]))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["skills"], ["Python", "SQL"])

    def test_malformed_or_empty_skills_are_rejected(self):
        for value in ["", ", , ;", "[broken", "[1]", '[{"value": 42}]', "[]", "[{}]"]:
            with self.subTest(value=value):
                self.assertFalse(self.form(skills=value).is_valid())

    def test_skill_limits(self):
        for value in ["x" * 81, ",".join(f"skill {i}" for i in range(21)), "x" * 2001]:
            with self.subTest(value=value):
                self.assertFalse(self.form(skills=value).is_valid())

    def test_position_is_required_and_bounded(self):
        for position in ["", "  ", "x", "x" * 121]:
            with self.subTest(position=position):
                self.assertFalse(self.form(position=position).is_valid())


class DemoEngineTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = DemoEngine()

    def test_documented_dataset_counts(self):
        self.assertEqual(len(self.engine.jobs), 872)
        self.assertEqual(len(self.engine.occupations), 702)

    def test_known_title_uses_its_reference_score(self):
        risk = self.engine.risk("Marketing Manager", ["Marketing"])
        self.assertEqual(risk["reference"], "Marketing Managers")
        self.assertEqual(risk["score"], 1.4)

    def test_unknown_title_has_no_invented_score(self):
        for title in ["Quantum Zookeeper", "Xyzzy Manager", "", "and or"]:
            with self.subTest(title=title):
                self.assertIsNone(self.engine.risk(title, ["Python"])["score"])

    def test_demo_skills_do_not_change_title_reference(self):
        self.assertEqual(
            self.engine.risk("Accountant", ["Python"]),
            self.engine.risk("Accountant", ["Accounting"]),
        )

    def test_unmatched_skills_do_not_produce_arbitrary_recommendations(self):
        self.assertEqual(self.engine.recommend(["xyzzynotaskill"]), [])

    def test_recommendations_are_deterministic_and_from_the_catalog(self):
        skills = ["Digital marketing", "Content writing skills", "Market Research"]
        jobs = self.engine.recommend(skills)
        self.assertEqual(len(jobs), 5)
        self.assertEqual(jobs, self.engine.recommend(skills))
        self.assertTrue(all(job in self.engine.jobs for job in jobs))
        self.assertTrue(any("Marketing" in job["Title"] for job in jobs))

    def test_skill_matching_compares_individual_skills(self):
        report = assess(
            "Marketing Manager",
            [
                "Digital marketing",
                "Market Research",
                "Content writing skills",
                "Communication Skills",
            ],
            "demo",
        )
        self.assertIn("Digital marketing", report["matched_skills"])
        self.assertNotIn("Digital marketing", report["suggested_skills"])
        self.assertGreater(len(report["suggested_skills"]), 0)

    def test_source_skill_lists_are_split_and_deduplicated(self):
        self.assertEqual(
            split_skills("Python and  SQL and Python and  and Communication"),
            ["Python", "SQL", "Communication"],
        )

    def test_risk_bands_and_bounds(self):
        for score, band in [
            (0, "low"),
            (40, "low"),
            (40.1, "moderate"),
            (70, "moderate"),
            (70.1, "high"),
            (100, "high"),
            (None, "unknown"),
        ]:
            with self.subTest(score=score):
                self.assertEqual(risk_summary(score)["band"], band)
        self.assertEqual(risk_summary(120)["score"], 100)
        self.assertEqual(risk_summary(-10)["score"], 0)

    def test_application_import_does_not_load_ml_packages(self):
        code = """
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'admin.settings'
import django
django.setup()
from risk_check import views
assert not {'torch', 'sentence_transformers', 'sklearn', 'pandas', 'joblib'} & sys.modules.keys()
"""
        completed = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=settings.BASE_DIR,
            env=os.environ.copy(),
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


@override_settings(
    SECUREER_ENGINE="demo",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    },
)
class AssessmentFlowTests(TestCase):
    profile: ClassVar[dict[str, str]] = {
        "user_name": "Alex",
        "position": "Marketing Manager",
        "skills": "Digital marketing, Market Research, Content writing skills, Communication Skills",
    }

    def submit(self, client=None, **changes):
        return (client or self.client).post(
            reverse("check"), {**self.profile, **changes}
        )

    def test_public_pages_and_example_need_no_profiles(self):
        for name in ["index", "about", "example", "health"]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Result.objects.count(), 0)

    def test_get_does_not_create_an_assessment(self):
        self.assertEqual(self.client.get(reverse("check")).status_code, 405)
        self.assertEqual(Result.objects.count(), 0)

    def test_successful_submission_persists_snapshot_and_skills(self):
        response = self.submit()
        result = Result.objects.get()
        self.assertRedirects(response, reverse("result", args=[result.pk]))
        self.assertEqual(result.user.skills.count(), 4)
        self.assertIn(
            "Digital marketing",
            result.matched_skills.values_list("skill_name", flat=True),
        )
        self.assertEqual(result.risk_index, Decimal("1.40"))
        self.assertEqual(result.analysis["engine"], "demo")

    def test_refresh_uses_the_saved_report_without_running_inference(self):
        response = self.submit()
        with patch(
            "risk_check.views.assess",
            side_effect=AssertionError("Inference on refresh"),
        ):
            self.assertEqual(self.client.get(response.url).status_code, 200)

    def test_invalid_profile_is_retained_without_writes_or_inference(self):
        with patch("risk_check.views.assess") as inference:
            response = self.submit(position="", skills="[broken")
            inference.assert_not_called()
        self.assertContains(response, "Alex", status_code=400)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Result.objects.count(), 0)

    def test_unavailable_engine_is_a_recoverable_error_without_writes(self):
        with (
            patch("risk_check.views.assess", side_effect=AssessmentUnavailable),
            self.assertLogs("risk_check.views", level="ERROR"),
        ):
            response = self.submit()
        self.assertContains(response, "temporarily unavailable", status_code=503)
        self.assertEqual(User.objects.count(), 0)

    def test_other_sessions_cannot_read_or_delete_a_report(self):
        result_url = self.submit().url
        result = Result.objects.get()
        stranger = Client()
        self.assertEqual(stranger.get(result_url).status_code, 404)
        self.assertEqual(
            stranger.post(reverse("delete_result", args=[result.pk])).status_code, 404
        )
        self.assertTrue(Result.objects.filter(pk=result.pk).exists())

    def test_reports_disable_caching_and_indexing(self):
        response = self.client.get(self.submit().url)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_delete_removes_profile_report_and_unshared_skills(self):
        self.submit()
        result = Result.objects.get()
        url = reverse("delete_result", args=[result.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("index"))
        self.assertEqual(Result.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Skill.objects.count(), 0)
        self.assertEqual(self.client.session["result_ids"], [])

    def test_deletion_preserves_skills_used_by_another_profile(self):
        self.submit()
        first = Result.objects.get()
        self.submit(user_name="Other")
        self.client.post(reverse("delete_result", args=[first.pk]))
        self.assertEqual(Result.objects.count(), 1)
        self.assertEqual(Result.objects.get().user.skills.count(), 4)

    def test_csrf_protection_is_enforced(self):
        self.assertEqual(
            self.submit(client=Client(enforce_csrf_checks=True)).status_code, 403
        )

    def test_user_content_is_escaped(self):
        response = self.client.get(
            self.submit(user_name='<script>alert("x")</script>').url
        )
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("x")</script>')

    def test_full_scale_score_fits_database_field(self):
        report = deepcopy(assess("Marketing Manager", ["Marketing"], "demo"))
        report["risk"] = risk_summary(100)
        with patch("risk_check.views.assess", return_value=report):
            self.submit()
        result = Result.objects.get()
        result.full_clean()
        self.assertEqual(result.risk_index, Decimal("100.00"))

    def test_unknown_title_and_skills_render_empty_states(self):
        response = self.client.get(
            self.submit(position="Quantum Zookeeper", skills="xyzzynotaskill").url
        )
        self.assertContains(response, "No close reference")
        self.assertContains(response, "No close skill matches yet.")
        self.assertIsNone(Result.objects.get().risk_index)
