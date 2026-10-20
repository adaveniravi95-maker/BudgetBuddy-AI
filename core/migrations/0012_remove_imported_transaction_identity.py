from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_upi_transaction_import'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ImportedTransactionIdentity',
        ),
    ]
