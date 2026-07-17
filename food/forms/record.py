from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import QuerySet, Max, Min
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from ..models import Day, Group, Item, Record, Meal


class ItemSearchForm(forms.Form):
    query = forms.CharField(max_length=128, required=False, empty_value="", initial="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_items(self, user: User) -> QuerySet | None:
        if not self.is_valid():
            return None
        
        queryset = user.food_items.all()
        if query := self.cleaned_data["query"]:

            def filter_item(item):
                if query.lower() in str(item).lower():
                    return True
                return False

            queryset = filter(filter_item, queryset)

        return queryset


class RecordDialogForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"] = forms.ModelChoiceField(
            user.food_items.all(), required=False
        )


class RecordForm(forms.ModelForm):
    template_name = "food/forms/record_form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk is None:
            return

        if Record.Type.PIECE in self.instance.item.get_available_record_types():
            self['type'].initial = Record.Type.PIECE
            self['value'].initial = 1
        else:
            self['type'].initial = Record.Type.MASS
            self['value'].initial = 100

    def clean(self):
        super().clean()
        if self.errors:
            return

        type = self.cleaned_data['type']
        item = self.cleaned_data['item']
        if type not in item.get_available_record_types():
            raise ValidationError(f'type "{type}" is not supported by item "{item}"')

    class Meta:
        model = Record
        fields = ['item', "type", "value"]
