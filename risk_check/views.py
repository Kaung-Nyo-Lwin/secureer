import logging

from django.conf import settings
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_POST

from .forms import AssessmentForm
from .models import Result, Skill, User
from .services import AssessmentUnavailable, assess

logger = logging.getLogger(__name__)


def home_context(form=None):
    return {
        "form": form if form is not None else AssessmentForm(),
        "engine": settings.SECUREER_ENGINE,
        "active_page": "assessment",
    }


@require_GET
def index(request):
    return render(request, "risk_check/index.html", home_context())


@require_GET
def about(request):
    return render(request, "risk_check/about.html", {"active_page": "research"})


@require_GET
def example(request):
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
    return render(
        request,
        "risk_check/result.html",
        {
            "report": report,
            "display_name": "Alex",
            "is_example": True,
            "active_page": "example",
        },
    )


@require_POST
@sensitive_post_parameters("user_name", "position", "skills")
def check(request):
    form = AssessmentForm(request.POST)
    if not form.is_valid():
        return render(request, "risk_check/index.html", home_context(form), status=400)
    profile = form.cleaned_data
    try:
        report = assess(profile["position"], profile["skills"])
    except AssessmentUnavailable:
        logger.exception("Assessment engine unavailable")
        form.add_error(
            None,
            "The analysis engine is temporarily unavailable. Please try again later, or explore the example report.",
        )
        return render(request, "risk_check/index.html", home_context(form), status=503)
    with transaction.atomic():
        user = User.objects.create(
            user_name=profile["user_name"] or "Explorer",
            position=profile["position"],
            created_at=timezone.now(),
        )
        selected_skills = []
        for name in profile["skills"]:
            skill, _ = Skill.objects.get_or_create(skill_name=name)
            selected_skills.append(skill)
        user.skills.set(selected_skills)
        result = Result.objects.create(
            user=user,
            risk_index=report["risk"]["score"],
            analysis=report,
            recommended_skills=report["suggested_skills"],
            recommended_jobs={
                job["title"]: (
                    job["risk"]["score"] / 100
                    if job["risk"]["score"] is not None
                    else None
                )
                for job in report["jobs"]
            },
        )
        result.matched_skills.set(
            [
                skill
                for skill in selected_skills
                if skill.skill_name in report["matched_skills"]
            ]
        )
    request.session["result_ids"] = (
        request.session.get("result_ids", []) + [result.pk]
    )[-20:]
    return redirect("result", result_id=result.pk)


def owned_result(request, result_id):
    if result_id not in request.session.get("result_ids", []):
        raise Http404("This report is not available in this browser session.")
    return get_object_or_404(Result.objects.select_related("user"), pk=result_id)


@require_GET
@never_cache
def detail(request, result_id):
    result = owned_result(request, result_id)
    response = render(
        request,
        "risk_check/result.html",
        {
            "report": result.analysis,
            "display_name": result.user.user_name,
            "result": result,
            "active_page": "assessment",
        },
    )
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@require_POST
def delete_result(request, result_id):
    result = owned_result(request, result_id)
    with transaction.atomic():
        skill_ids = list(result.user.skills.values_list("id", flat=True))
        result.user.delete()
        Skill.objects.filter(
            id__in=skill_ids,
            user__isnull=True,
            matched_skills__isnull=True,
            post_skills__isnull=True,
        ).delete()
    request.session["result_ids"] = [
        pk for pk in request.session.get("result_ids", []) if pk != result_id
    ]
    return redirect("index")


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "engine": settings.SECUREER_ENGINE})
