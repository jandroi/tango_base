from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main_data_management", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dataimportjob",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("validating", "Validating"),
                    ("validated", "Validated"),
                    ("committing", "Committing"),
                    ("completed", "Completed"),
                    ("no_data", "No Data Imported"),
                    ("failed", "Failed"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
