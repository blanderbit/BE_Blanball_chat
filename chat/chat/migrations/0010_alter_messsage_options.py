# Generated by Django 4.2.1 on 2023-06-11 19:10

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0009_messsage_edited"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="messsage",
            options={
                "ordering": ["-id"],
                "verbose_name": "message",
                "verbose_name_plural": "messages",
            },
        ),
    ]
