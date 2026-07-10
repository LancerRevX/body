import datetime

from django.http import HttpRequest, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import QueryDict, HttpResponse
from django.forms import modelform_factory
from django.core.exceptions import FieldError
from django_htmx.http import trigger_client_event

from ..forms import RecordForm, RecordDialogForm, ItemSearchForm
from ..models import Day, Record


@require_GET
@login_required
def create_record(request: HttpRequest, date: datetime.date, meal_id: int):
    day = get_object_or_404(Day, user=request.user, date=date)
    meal = get_object_or_404(day.meals, id=meal_id)

    dialog_form = RecordDialogForm(request.user, request.GET)
    if not dialog_form.is_valid():
        return HttpResponseBadRequest()
    item = dialog_form.cleaned_data["item"]

    item_search_form = ItemSearchForm()

    record = Record(item=item)
    record_form = RecordForm(instance=record)

    if request.headers["HX-Target"] == "record-dialog-bottom":
        return render(
            request,
            "food/day/record_dialog/bottom.html",
            {"day": day, "meal": meal, "item": item, "form": record_form},
        )

    response = render(
        request,
        "food/day/record_dialog.html",
        {
            "day": day,
            "meal": meal,
            "item": item,
            "items": request.user.food_items.all(),
            "item_search_form": item_search_form,
            "record_form": record_form,
        },
    )
    return trigger_client_event(response, "open-record-dialog")


@require_GET
@login_required
def edit_record(
    request: HttpRequest,
    date: datetime.date,
    meal_id: int,
    record_id: int,
):
    day = get_object_or_404(Day, user=request.user, date=date)
    meal = get_object_or_404(day.meals, id=meal_id)
    record = get_object_or_404(meal.records, id=record_id)

    item_search_form = ItemSearchForm()

    record_form = RecordForm(instance=record)

    dialog_form = RecordDialogForm(request.user, request.GET)
    if not dialog_form.is_valid():
        return HttpResponseBadRequest()

    if dialog_form.cleaned_data["item"]:
        item = dialog_form.cleaned_data["item"]
    else:
        item = record.item

    return render(
        request,
        "food/day/record_dialog.html",
        {
            "day": day,
            "meal": meal,
            "item": item,
            "items": request.user.food_items.all(),
            "item_search_form": item_search_form,
            'record': record,
            "record_form": record_form,
        },
    )


@require_GET
@login_required
def index_items(request: HttpRequest, date, meal_id):
    day = get_object_or_404(Day, user=request.user, date=date)
    meal = get_object_or_404(day.meals, id=meal_id)
    item_search_form = ItemSearchForm(request.GET)

    return render(
        request, "food/day/record_dialog/items.html", {"day": day, "meal": meal, "items": item_search_form.get_items(request.user)}
    )


class RecordView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, date: datetime.date, meal_id: int):
        day = get_object_or_404(Day, user=request.user, date=date)

        meal = get_object_or_404(day.meals, id=meal_id)

        record_form = RecordForm(request.POST)
        if not record_form.is_valid():
            return HttpResponseBadRequest()

        position = meal.records.count()
        record = meal.records.create(**record_form.cleaned_data, position=position)

        response = render(request, "food/day/meal.html", {"day": day, "meal": meal}, status=201)
        # return trigger_client_event(response, "close-record-dialog")
        return response

    def patch(
        self,
        request: HttpRequest,
        date: datetime.date,
        meal_id: int,
        record_id: int,
    ):
        day = get_object_or_404(Day, user=request.user, date=date)
        meal = get_object_or_404(day.meals, id=meal_id)
        record = get_object_or_404(meal.records, id=record_id)

        old_position = record.position

        form_data = QueryDict(request.body)
        try:
            PartialRecordForm = modelform_factory(Record, form=RecordForm, fields=form_data.keys())
        except FieldError:
            return HttpResponseBadRequest()
        record_form = PartialRecordForm(form_data, instance=record)

        if not record_form.is_valid():
            return HttpResponseBadRequest()

        if not record_form.has_changed():
            return HttpResponse(status=204)

        record_form.save()

        new_position = record.position
        if new_position > old_position:
            for sibling in meal.records.filter(position__range=(old_position, new_position)).exclude(id=record.id):
                sibling.position -= 1
                sibling.save()
        elif new_position < old_position:
            for sibling in meal.records.filter(position__range=(new_position, old_position)).exclude(id=record.id):
                sibling.position += 1
                sibling.save()

        if record_form.changed_data == ["position"]:
            return HttpResponse(status=204)

        return render(
            request,
            "food/day/meal/record.html",
            {
                "day": day,
                "meal": meal,
                "record": record,
            },
        )

    def delete(
        self,
        request: HttpRequest,
        date: datetime.date,
        meal_id: int,
        record_id: int,
    ):
        day = get_object_or_404(Day, user=request.user, date=date)
        meal = get_object_or_404(day.meals, id=meal_id)
        record = get_object_or_404(meal.records, id=record_id)

        for sibling in meal.records.filter(position__gt=meal.position):
            sibling.position -= 1
            sibling.save()
        record.delete()

        return HttpResponse()
