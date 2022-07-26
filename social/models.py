from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager)
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from autoslug import AutoSlugField
from autoslug.settings import slugify as default_slugify
from django.utils.text import slugify
import string
import random
from django import forms
import uuid
import re
from .api.utils import Str


def slugify(value):
    rand = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
    value = re.sub("(\.|\?|\!|\~|\`|\@|\#|\$|\%|\^|\&|\*|\(|\)|\_|\+|\[\|\]|\{|\}|\/|\\|\,|\.|\_|(\s{2,}))+", "", value)
    value = rand+'-'+value.replace(' ', '-').replace('.', '-')
    return value


class MainUserManager(BaseUserManager):
    def random_word(self, length):
        alphanum = string.ascii_lowercase+string.digits
        return ''.join(random.choice(alphanum) for i in range(length))

    def create_user(self, email, mobile, first_name, last_name, username=None, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            mobile=mobile,
        )
        user.display_name = f"coc_{Str.rand_num()}" if not username else username
        user.first_name = first_name
        user.last_name = last_name
        user.is_admin = False
        user.is_mobile_active = False
        user.set_password(password)
        user.about = ' '
        user.invitation_code = self.random_word(6)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, mobile, first_name, last_name, username=None, password=None):
        user = self.create_user(
            email,
            mobile=mobile,
            first_name=first_name,
            last_name=last_name,
            dispay_name=username,
            password=password,
        )
        user.is_admin = True
        user.is_mobile_active = False
        user.about = 'Admin user'
        user.invitation_code = self.random_word(64)
        user.save(using=self._db)
        return user


# Create your models here.
class User(AbstractBaseUser):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200, default=None, help_text="A unique user name")
    show_real_name = models.BooleanField(default=False, help_text="Should real name be displayed?")
    about = models.CharField(max_length=500, default=None)
    mobile = models.CharField(max_length=50, unique=True)
    email = models.EmailField(
        verbose_name='Email address',
        max_length=255,
        unique=True,
    )
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invited_by_user', null= True, default= None,
                                   on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_mobile_active = models.BooleanField(default=True)
    invitation_counter = models.PositiveSmallIntegerField(default=50)
    invitation_counter_default = models.PositiveSmallIntegerField(default=50)
    invitation_code = models.CharField(max_length=150, unique=True, null=True, default=None)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['mobile']
    objects = MainUserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

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


class Invitation(models.Model):
    invitor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invitor_user',
                                          on_delete=models.CASCADE)  # User ID
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invitee_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Space(models.Model):

    def custom_slugify(value):
        return default_slugify(value).replace('-', '_')

    guid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    symbol = models.TextField(max_length=25, default=None, null=True)
    symbol_description = models.TextField(max_length=200, default=None, null=True)
    thumbnail = models.FileField(upload_to='static/spaces/', default=None, null=True)
    slug = AutoSlugField(populate_from='title', unique_with='title', slugify=slugify)
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
    user_can_post = models.BooleanField(default=True)
    premium_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='space_created_by_user', null=True, blank=True
                                   , on_delete=models.CASCADE)  # User ID
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='space_updated_by_user', null=True, blank=True
                                   , on_delete=models.CASCADE)  # User ID
    auto_add_new_members = models.BooleanField(default=False)
    members_can_leave = models.BooleanField(default=True)
    blocked_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    blocked_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='space_blocked_by_user', null=True, blank=True
                                   , on_delete=models.CASCADE)  # User ID

    def __str__(self):
        return self.title


class SpacePolicy(models.Model):
    space = models.ForeignKey(Space, related_name="space_policy", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500)

    def __str__(self):
        return self.title

    class Meta:
        abstract = False


class SpacePolicyForm(forms.ModelForm):
    class Meta:
        model = SpacePolicy
        fields = ('title', 'description')


class SpaceMembership(models.Model):
    followed_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followed_by',
                                    on_delete=models.CASCADE)  # User ID
    space = models.ForeignKey(Space, related_name='space_followed', on_delete=models.CASCADE)  # User ID
    mute_space_post = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    unfollow_space = models.BooleanField(default=False)


class Post(models.Model):
    space = models.ForeignKey(Space, related_name='space_post', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=False)
    description = models.TextField(max_length=5000, null=False)
    visible = models.BooleanField(default=True)
    total_votes_up = models.PositiveIntegerField(default=0)
    total_votes_down = models.PositiveIntegerField(default=0)

    post_status = [
        ('D', 'Draft'),
        ('P', 'Published'),
    ]
    status = models.CharField(
        max_length=1,
        choices=post_status,
        default='D',
    )
    slug = AutoSlugField(populate_from='title', slugify=slugify, max_length=300)
    comment_depth = models.PositiveIntegerField(default=0, null=True, help_text="Zero means no comment")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_updated_by_user',
                                   null=True, blank=True, on_delete=models.CASCADE)  # User ID
    deleted_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_deleted_by_user',
                                   null=True, blank=True, on_delete=models.CASCADE)  # User ID

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('-created_at',)


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='post_comment', on_delete=models.CASCADE)
    parent_comment = models.ForeignKey('self', related_name='post_parent_comment', on_delete=models.CASCADE, null=True)
    lft = models.PositiveIntegerField(default=1)
    rgt = models.PositiveIntegerField(default=2)
    body = models.TextField(max_length=5000, null=False)
    depth = models.PositiveIntegerField(default=1, null=True, help_text="One means first level") # One means first level
    visible = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_updated_by_user', null=True,
                                   blank=True, on_delete=models.CASCADE)  # User ID
    total_votes_up = models.PositiveIntegerField(default=0)
    total_votes_down = models.PositiveIntegerField(default=0)
    deleted_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_deleted_by_user', null=True,
                                   blank=True, on_delete=models.CASCADE)  # User ID

    class Meta:
        ordering = ('-created_at',)


# Files attached to posts
class Attachment(models.Model):
    post = models.ForeignKey(Post, related_name='post_attachment', on_delete=models.CASCADE)
    file_name = models.CharField(max_length=250)
    file_uri = models.ImageField(upload_to='posts/attachments/%Y/%m/%d/', null=True)
    title = models.CharField(max_length=250)
    mime_type = models.CharField(max_length=100)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='attachment_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='attachment_updated_by_user', null=True,
                                   blank=True, on_delete=models.CASCADE)  # User ID

    def __str__(self):
        return self.file_uri


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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vote_updated_by_user',
                                   null=True, blank=True, on_delete=models.CASCADE)  # User ID


class Report(models.Model):
    post = models.ForeignKey(Post, related_name='post_report', on_delete=models.CASCADE)
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
    status = [
        ('AC', 'Accepted'),
        ('RJ', 'Rejected'),
        ('RV', 'In Review'),
    ]
    is_accepted = models.CharField(
        max_length=2,
        choices=status,
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='report_created_by_user',
                                   on_delete=models.CASCADE)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='report_updated_by_user',
                                   null=True, blank=True, on_delete=models.CASCADE)  # User ID


class ActivationCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='activation_user_codes',
                             on_delete=models.CASCADE)  # User ID
    activation_code = models.PositiveIntegerField(unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Bookmarks(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='bookmark',
                             db_index=True,
                             on_delete=models.CASCADE)
    # As of now you can only bookmark a post
    object_bookmarked = models.ForeignKey(Post, related_name="post_bookmarked", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)


class Action(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='actions',
                             db_index=True,
                             on_delete=models.CASCADE)
    space = models.ForeignKey(Space, related_name='action_space', db_index=True, on_delete=models.CASCADE)
    verb_types = [
        ('PTC', 'Post to Channel'),
        ('COP', 'Comment on post'),
        ('COC', 'COC'),
        ('VGU', 'Gained a vote up')
    ]
    verb = models.CharField(max_length=3, choices=verb_types, )
    # In generic relations, ContentType objects play the role of pointing to the model used for the relationship.
    target_content = models.ForeignKey(ContentType, blank=True, null=True, related_name='target_obj',
                                       on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True, blank=True, )
    target = GenericForeignKey('target_content', 'target_id')

    edge_rank = models.PositiveIntegerField(default=0)  # the rank for this particular activity
    parent_types = [
        ('P', 'Post'),
        ('C', 'Comment'),
        ('V', 'V'),
    ]
    parent_type = models.CharField(max_length=1, choices=parent_types, blank=True, null=True)
    is_notification = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-created_at',)


# Only store the token and get the latest
class SMSToken(models.Model):
    token = models.CharField(max_length=256, default=None, null=True)
    is_refreshed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)


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
