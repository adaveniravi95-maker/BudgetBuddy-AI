from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_deduplicate_monthly_reports'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='income',
            name='upi_reference',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='expense',
            name='upi_reference',
            field=models.CharField(blank=True, max_length=150),
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
