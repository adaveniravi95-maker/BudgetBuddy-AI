from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('core', 'Profile')
    existing_user_ids = Profile.objects.values_list('user_id', flat=True)
    Profile.objects.bulk_create(
        Profile(user_id=user.id, role='student')
        for user in User.objects.exclude(id__in=existing_user_ids)
    )


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_profile_role'),
    ]

    operations = [
        migrations.RunPython(
            create_missing_profiles,
            migrations.RunPython.noop,
        ),
    ]