import csv
from random import choice

from django.db import migrations
from django.conf import settings

GROUPS = [
    dict(name="Bellini", color="#ffffff"),
    dict(name="Перцы", color="#ff0000"),
    dict(name="Cheez", color="#fff200"),
    dict(name="Фрукты", color="#ff8c00"),
]


def insert_food_items(apps, schema_editor):
    Item = apps.get_model("food", "Item")
    Group = apps.get_model("food", "Group")
    User = apps.get_model(settings.AUTH_USER_MODEL)

    try:
        user = User.objects.get(username="nikita")
    except User.DoesNotExist:
        user = User.objects.create_superuser("nikita", password="nikita")

    for group_data in GROUPS:
        user.food_groups.create(**group_data)

    with open("food/csv/food.csv", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            piece_mass = (
                float(row[5].replace(",", ".").replace('"', ""))
                if row[5]
                else None
            )
            item = Item(
                user=user,
                name=row[0],
                protein=float(row[1].replace(",", ".").replace('"', "")),
                fat=float(row[2].replace(",", ".").replace('"', "")),
                carbs=float(row[3].replace(",", ".").replace('"', "")),
                calories=float(row[4].replace(",", ".").replace('"', "")),
                piece_mass=piece_mass,
                pack_mass=None,
            )
            item.full_clean()
            item.save()


def delete_food_items(apps, schema_editor):
    Day = apps.get_model("food", "Day")
    Item = apps.get_model("food", "Item")
    Group = apps.get_model("food", "Group")

    Day.objects.all().delete()
    Item.objects.all().delete()
    Group.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("food", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(insert_food_items, delete_food_items),
    ]
