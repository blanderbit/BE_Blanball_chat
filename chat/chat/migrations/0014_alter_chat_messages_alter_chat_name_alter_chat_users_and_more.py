# Generated by Django 4.2.1 on 2023-06-15 14:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0013_alter_messsage_reply_to"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chat",
            name="messages",
            field=models.ManyToManyField(
                blank=True, db_index=True, related_name="chat", to="chat.messsage"
            ),
        ),
        migrations.AlterField(
            model_name="chat",
            name="name",
            field=models.CharField(db_index=True, max_length=355),
        ),
        migrations.AlterField(
            model_name="chat",
            name="users",
            field=models.JSONField(db_index=True, default=list),
        ),
        migrations.AlterField(
            model_name="messsage",
            name="readed_by",
            field=models.JSONField(db_index=True, default=list),
        ),
        migrations.AlterField(
            model_name="messsage",
            name="text",
            field=models.CharField(db_index=True, max_length=500),
        ),
    ]
