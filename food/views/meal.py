import datetime

from django.http import HttpRequest, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import QueryDict
from django.core.exceptions import BadRequest

from ..forms import MealForm
from ..models import Day


class MealView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, date: datetime.date):
        if not request.headers.get("HX-Request"):
            raise BadRequest

        day = Day.objects.get_or_create(user=request.user, date=date)[0]

        position = day.meals.count()
        meal = day.meals.create(position=position)

        return render(request, "food/day/meals.html", {"day": day}, status=201)

    def patch(self, request: HttpRequest, date: datetime.date, meal_id: int):
        day = get_object_or_404(Day, user=request.user, date=date)

        meal = get_object_or_404(day.meals, id=meal_id)
        old_position = meal.position

        form_data = QueryDict(request.body)
        meal_form = MealForm(form_data, instance=meal)
        if not meal_form.is_valid() or not meal_form.has_changed():
            return HttpResponseBadRequest()

        new_position = meal_form.cleaned_data["position"]

        if new_position < old_position:
            for sibling in day.meals.filter(position__lt=old_position, position__gte=new_position).exclude(id=meal.id):
                sibling.position += 1
                sibling.save()
        else:
            for sibling in day.meals.filter(position__gt=old_position, position__lte=new_position).exclude(id=meal.id):
                sibling.position -= 1
                sibling.save()

        meal.position = new_position
        meal.save()

        return HttpResponse(status=204)

    def delete(self, request: HttpRequest, date: datetime.date, meal_id: int):
        day = get_object_or_404(Day, user=request.user, date=date)

        meal = get_object_or_404(day.meals, id=meal_id)

        for sibling in day.meals.filter(position__gt=meal.position):
            sibling.position -= 1
            sibling.save()
        meal.delete()

        return HttpResponse()
