"""Validate profiles before any inference or database writes."""

import json
import re

from django import forms


class AssessmentForm(forms.Form):
    user_name = forms.CharField(
        label="First name",
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "What should we call you?",
                "autocomplete": "given-name",
            }
        ),
    )
    position = forms.CharField(
        label="Current or recent role",
        min_length=2,
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Marketing Manager",
                "autocomplete": "organization-title",
            }
        ),
    )
    skills = forms.CharField(
        label="Your skills",
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "placeholder": "e.g. Marketing, Communication, Project Management",
                "rows": 3,
                "aria-describedby": "skills-help",
            }
        ),
    )

    def clean_skills(self):
        raw = self.cleaned_data["skills"]
        # Accept the original Tagify format as well as ordinary text.
        if raw.startswith("["):
            try:
                items = json.loads(raw)
                if not isinstance(items, list):
                    raise TypeError
                values = [item["value"] for item in items]
                if not all(isinstance(value, str) for value in values):
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                raise forms.ValidationError("Enter skills separated by commas.")
        else:
            values = re.split(r"[,;\n]", raw)
        skills = {}
        for value in values:
            value = " ".join(value.split())
            if not value:
                continue
            if len(value) > 80:
                raise forms.ValidationError(
                    "Keep each skill to 80 characters or fewer."
                )
            skills.setdefault(value.casefold(), value)
        if not skills:
            raise forms.ValidationError("Add at least one skill to get started.")
        if len(skills) > 20:
            raise forms.ValidationError("Choose up to 20 skills for this assessment.")
        return list(skills.values())
