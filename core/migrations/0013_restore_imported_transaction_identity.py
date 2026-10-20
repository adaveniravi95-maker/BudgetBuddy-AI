from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_remove_imported_transaction_identity'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='category',
            field=models.CharField(
                choices=[
                    ('Food', 'Food'),
                    ('Travel', 'Travel'),
                    ('Shopping', 'Shopping'),
                    ('Education', 'Education'),
                    ('Entertainment', 'Entertainment'),
                    ('Miscellaneous', 'Miscellaneous'),
                    ('Uncategorized', 'Uncategorized'),
                ],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name='budget',
            name='category',
            field=models.CharField(
                choices=[
                    ('Food', 'Food'),
                    ('Travel', 'Travel'),
                    ('Shopping', 'Shopping'),
                    ('Education', 'Education'),
                    ('Entertainment', 'Entertainment'),
                    ('Miscellaneous', 'Miscellaneous'),
                    ('Uncategorized', 'Uncategorized'),
                ],
                max_length=100,
            ),
        ),
        migrations.CreateModel(
            name='ImportedTransactionIdentity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identity_key', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='imported_transaction_identities',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
        migrations.AddConstraint(
            model_name='importedtransactionidentity',
            constraint=models.UniqueConstraint(
                fields=('user', 'identity_key'),
                name='unique_imported_transaction_identity',
            ),
        ),
    ]
