from django.http import HttpResponse
from django.template import loader
from .models import Skill, Result, User, Post
from django.shortcuts import render
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

import json
# Create your views here.

# Models
from .utils import recommend_job, calculate_job_risk, calculate_title_risk, calculate_skill_risk


def index(request):
    skills_data = Skill.objects.all()  # Get model instances
    # formatted_skills_data = [
    #     {"value": skill.skill_name } for skill in skills_data
    # ]
    formatted_skills_data= []
    for skills in skills_data:
        formatted_skills_data.append(skills.skill_name)
    return render(request, "risk_check/index.html", {'skills_data': formatted_skills_data})
    # return render(request, "risk_check/index.html", context)

# def results(request, result_id):
#     response = "You're looking at the results of question %s."
#     return HttpResponse(response % result_id)

# def check(request, result_id):
#     return HttpResponse("You're voting on question %s." % result_id)

# def index(request):
#     latest_question_list = Skill.objects.order_by("pub_date")[:5]
#     output = ", ".join([q.question_text for q in latest_question_list])
#     return HttpResponse(output)

def detail(request, result_id):
    result = get_object_or_404(Result, pk=result_id)
    print(type(result))
    return render(request, "risk_check/result.html", {'result': result})
    #return render(request, "risk_check/detail.html", {"result": result})

def check(request):
    # create a new user
    #skills = Skill.objects.get(pk=request.POST["skill"])
    # print(list(request.POST.items()))
    user_name = request.POST['user_name']
    position = request.POST['position']
    skills_string = json.loads(request.POST.get('skills'))
    skills = list()
    for skill in skills_string:
        skills.append(skill['value'])

    final_skills = ' and '.join(skills)

    # job risk
    current_job_risk = calculate_job_risk(position, final_skills)
    print(current_job_risk)

    # recommendation
    recommended_titles, recommended_skills = recommend_job(final_skills)
    recommended_job_risk = dict()
    for title, skills in zip(recommended_titles, recommended_skills):
        recommended_job_risk[title] = calculate_job_risk(title, skills)

    print(recommended_job_risk)


    created_at = timezone.now()
    user = User(user_name = user_name, position = position, created_at = created_at)
    user.save()
    #user.skills.add(request.POST['skills'])
    skills_string = json.loads(request.POST.get('skills'))
  
    for skills in skills_string:
        #skills = json.loads(skills)
        skill, created = Skill.objects.get_or_create(skill_name=skills['value'])
        user.skills.add(skill)
    user_id = user.pk
    # save to result

    result = Result(user_id = user_id, risk_index = 1, job_poll = 1, avg_salary = 1, industrial_risk_index = 1)
    result.save()
    result_id = result.pk

    return HttpResponseRedirect(reverse("result", args=(result_id,)))
    #return render(request, "risk_check/detail.html", {"result": result_id})



