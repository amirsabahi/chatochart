from abc import ABC

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from .permission import IsSpaceMember
from ..models import *


class Utils:
    @staticmethod
    def space_post_count(space):
        post_count = Post.objects.filter(space_id=space).count()
        return post_count

    @staticmethod
    def post_comment_count(post):
        comment_count = Comment.objects.filter(post_id=post).count()
        return comment_count


class UserSerializer(serializers.ModelSerializer):
    permission_classes = (IsAuthenticated,)
    def to_representation(self, value):
        if value.is_active is True:
            if value.show_real_name:
                return {'show_real_name': value.show_real_name,
                        'user_name': f"{value.first_name} {value.last_name}",
                        'first_name': value.first_name,
                        'last_name': value.last_name,
                        'about': value.about, }
            else:
                return {'show_real_name': value.show_real_name,
                        'user_name': f"{value.display_name}",
                        'about': value.about, }
        else:
            return {'show_real_name': False,
                    'user_name': '-',
                    'about': '-', }
    class Meta:

        model = User
        fields = ['first_name',  'last_name', 'about']


class MyAccountSerializer(serializers.ModelSerializer):
    permission_classes = (IsAuthenticated,)

    class Meta:
        model = User
        fields = ['first_name',  'last_name', 'about', 'display_name', 'mobile', 'email', 'invitation_code']


class SpacePolicySerializer(serializers.ModelSerializer):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    class Meta:
        model = SpacePolicy
        fields = ['title',  'description']


class SpaceSerializer(serializers.ModelSerializer):
    # authentication_classes = (BasicAuthentication, )
    permission_classes = (IsAuthenticatedOrReadOnly,)
    is_following = serializers.BooleanField()
    post_count = serializers.IntegerField( min_value=0)
    space_policy = SpacePolicySerializer(many=True, read_only=False)

    class Meta:
        model = Space
        fields = ['guid', 'id', 'title', 'description', 'symbol', 'symbol_description', 'slug', 'visibility', 'is_blocked', 'premium_only',
                  'members_can_leave', 'created_at', 'is_following', 'space_policy', 'post_count', 'thumbnail']


class CreatedAtField(serializers.RelatedField, ABC):
    def to_representation(self, value):
        if value.is_active is True:
            if value.show_real_name:
                return {'show_real_name': value.show_real_name,
                        'user_name': f"{value.first_name} {value.last_name}",
                        'about': value.about, }
            else:
                return {'show_real_name': value.show_real_name,
                        'user_name': f"{value.display_name}",
                        'about': value.about, }
        else:
            return {'show_real_name': False,
                    'user_name': '-',
                    'about': '-', }


class AttachmentSerializer(serializers.ModelSerializer):
    permission_classes = (IsAuthenticated, IsSpaceMember)

    class Meta:
        model = Attachment
        fields = ['file_uri', 'mime_type']


class SpacePostSerializer(serializers.ModelSerializer):
    permission_classes = (IsAuthenticated, IsSpaceMember, )
    created_by = CreatedAtField(many=False, read_only=True)
    post_attachment = AttachmentSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(min_value=0)
    space = serializers.CharField()
    space_slug = serializers.CharField()

    def validate(self, attrs):
        # Apply custom validation either here, or in the view.
        return True

    class Meta:
        model = Post
        fields = ['space','space_slug', 'slug', 'title', 'description', 'status', 'total_votes_up', 'total_votes_down',
                  'comment_count', 'created_at', 'created_by', 'post_attachment']
        extra_kwargs = {'created_by': {'required': False}, 'post_attachment': {'required': False}}
        validators = []

    def create(self, validated_data):
        """
        Create and return a new `post` instance, given the validated data.
        """
        return Post.objects.create(**validated_data)


class SpaceMemberSerializer(serializers.ModelSerializer):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    followed_by = CreatedAtField(many=False, read_only=True)

    class Meta:
        model = SpaceMembership
        fields = ['followed_by']


class PostCommentSerializer(serializers.ModelSerializer):
    permission_classes = (IsAuthenticated, IsSpaceMember, )
    created_by = CreatedAtField(many=False, read_only=True)
    #post = SpacePostSerializer()

    class Meta:
        model = Comment
        fields = ['id', 'body', 'visible', 'total_votes_up', 'total_votes_down', 'depth', 'parent_comment_id',
                  'created_by', 'created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    permission_classes = (IsAuthenticated, IsSpaceMember)

    class Meta:
        model = Attachment
        fields = ['title']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

