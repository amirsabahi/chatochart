#from django.db import models
from djongo import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager)
from django import forms
import uuid


class MainUserManager(BaseUserManager):
    def create_user(self, email, mobile, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            mobile=mobile,
        )
        user.is_mobile_active = False
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, mobile, password=None):
        user = self.create_user(
            email,
            password=password,
            mobile=mobile,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_mobile_active = False
        user.save(using=self._db)
        return user


# Create your models here.
class User(AbstractBaseUser):
    id = models.ObjectIdField()
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=50, unique=True)
    email = models.EmailField(
        verbose_name='Email address',
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_mobile_active = models.BooleanField(default=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['mobile']
    objects = MainUserManager()

    def __str__(self):
        return self.email

    def has_perms(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class SpacePolicy(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500)

    class Meta:
        abstract = True


class SpacePolicyForm(forms.ModelForm):
    class Meta:
        model = SpacePolicy
        fields = ('title', 'description')


class Space(models.Model):
    guid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    slug = models.SlugField(max_length=10)
    visibility_status = [
        ('PV', 'Private'),
        ('PC', 'Public'),
        ('IN', 'Invite Only'),
    ]
    visibility = models.CharField(
        max_length=2,
        choices=visibility_status,
        default='PC',
    )
    is_blocked = models.BooleanField(default=True)
    premium_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='space_created_by_user', null=True, blank=True
                                   , on_delete=models.CASCADE)  # User ID
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='space_updated_by_user', null=True, blank=True
                                   , on_delete=models.CASCADE)  # User ID
    auto_add_new_members = models.BooleanField(default=False)
    members_can_leave = models.BooleanField(default=True)
    policy = models.EmbeddedField(model_container=SpacePolicy, model_form_class=SpacePolicyForm, null=True, blank=True)
    blocked_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    blocked_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='space_blocked_by_user', null=True, blank=True
                                   , on_delete=models.CASCADE)  # User ID


class SpaceMembership(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followed_by',
                                on_delete=models.CASCADE)  # User ID
    space_id = models.ForeignKey(Space, related_name='space_followed', on_delete=models.CASCADE)  # User ID
    mute_space_post = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    unfollow_space = models.BooleanField(default=False)


class Post(models.Model):
    title = models.CharField(max_length=200, null=False)
    description = models.TextField(max_length=5000, null=False)
    visible = models.BooleanField(default=True)
    post_status = [
        ('D', 'Draft'),
        ('P', 'Published'),
    ]
    status = models.CharField(
        max_length=1,
        choices=post_status,
        default='D',
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_updated_by_user',
                                   null=True, blank=True, on_delete=models.CASCADE)  # User ID
    deleted_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_deleted_by_user',
                                   null=True, blank=True, on_delete=models.CASCADE)  # User ID


class Comment(models.Model):
    body = models.TextField(max_length=5000, null=False)
    visible = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_updated_by_user', null=True,
                                   blank=True, on_delete=models.CASCADE)  # User ID
    total_votes_up = models.PositiveIntegerField(default=0)
    total_votes_down = models.PositiveIntegerField(default=0)
    deleted_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_deleted_by_user', null=True,
                                   blank=True, on_delete=models.CASCADE)  # User ID


# Files attached to posts
class Attachment(models.Model):
    file_name = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    mime_type = models.CharField(max_length=100)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='attachment_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='attachment_updated_by_user', null=True,
                                   blank=True, on_delete=models.CASCADE)  # User ID


class Vote(models.Model):
    given_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vote_given_by_user',
                                 on_delete=models.CASCADE)  # User ID
    given_vote_on_post = models.ForeignKey(Post, blank=True, null=True, on_delete=models.CASCADE)
    given_vote_on_comment = models.ForeignKey(Comment, blank=True, null=True,
                                              on_delete=models.CASCADE)
    object_types = [
        ('CMT', 'Comment'),
        ('PST', 'Post'),
    ]
    given_object_type = models.CharField(
        max_length=3,
        choices=object_types,
    )
    vote_types = [
        ('UP', 'UP'),
        ('DWN', 'DOWN'),
    ]
    given_vote_type = models.CharField(
        max_length=3,
        choices=vote_types,
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vote_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vote_updated_by_user',
                                   null=True, blank=True, on_delete=models.CASCADE)  # User ID


class Report(models.Model):
    report_types = [
        ('break_rules', 'Break Rules'),
        ('harassment', 'Harassment'),
        ('hate', 'Hate'),
        ('sexual', 'Sexual'),
        ('spam', 'Spam'),
        ('misinformation', 'misinformation'),
        ('share_personal_info', 'Share Personal Info'),
        ('violence', 'Violence'),
    ]
    report_type = models.CharField(
        max_length=19,
        choices=report_types,
    )
    report_types = [
        ('AC', 'Accepted'),
        ('RJ', 'Rejected'),
        ('RV', 'In Review'),
    ]
    is_accepted = models.CharField(
        max_length=2,
        choices=report_types,
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='report_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='report_updated_by_user',
                                   null=True, blank=True, on_delete=models.CASCADE)  # User ID

''' 
### 
class Notification (models.Model):
class UserInvite(models.Model):
class UserFollow (models.Model):
class Notification (models.Model):
class poll(models.Model):
class poll_answer_user
class moderators:
class Tag():
class PostTag():
'''