import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.decorators.http import require_GET

from food.forms.record import ItemSearchForm
from food.models import Day


class ItemListView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest):
        item_search_form = ItemSearchForm(request.GET)

        return render(
            request,
            "food/day/record_dialog/items.html",
            {"day": day, "meal": meal, "items": item_search_form.get_items(request.user)},
        )
