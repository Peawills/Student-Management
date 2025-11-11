from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from records.models import Student
from .models import StudentProfile


@receiver(post_save, sender=Student)
def create_student_user_and_profile(sender, instance, created, **kwargs):
    """
    Automatically create a User and StudentProfile when a new Student is created.
    """
    if created and not instance.user:
        # 1. Create a User account
        # Username is the admission number, password is the lowercase surname
        username = instance.admission_no
        password = instance.surname.lower()

        # Avoid creating a user if one with the same username already exists
        if User.objects.filter(username=username).exists():
            return

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=instance.other_name,
            last_name=instance.surname,
        )

        # Add user to "Students" group if it exists
        student_group, created = Group.objects.get_or_create(name="Students")
        user.groups.add(student_group)

        # 2. Link the new User back to the Student instance
        instance.user = user
        instance.save(update_fields=["user"])

        # 3. Create the StudentProfile
        StudentProfile.objects.create(
            user=user, student=instance, date_of_birth=instance.date_of_birth
        )