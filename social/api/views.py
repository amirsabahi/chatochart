import re

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from rest_framework import generics
from .pagination import ManualPaginator, PaginationHandlerMixin
from ..models import Space, ActivationCode
from .throttling import CustomPostThrottle, CustomCommentThrottle
from django.db.models import F, Q
from .serializers import *
from django.http import Http404, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.parsers import JSONParser, FileUploadParser
import random
from PIL import Image
from datetime import datetime, timezone, timedelta
from .tasks import send_activation_code

'''
Taking care of paginator
Resource is: https://medium.com/@fk26541598fk/django-rest-framework-apiview-implementation-pagination-mixin-c00c34da8ac2
'''


class BasicPagination(PageNumberPagination):
    page_size_query_param = 'limit'



class TaskQueueView(APIView):
    permission_classes = ()

    def get(self, request):
        token = SMSToken.objects.get(pk=1)
        print(token.token)
        result = send_activation_code.delay(request.data['mobile'], '1234', token.token)

        return Response()


class LoginView(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        if request.data and request.data['mobile']:
            try:
                # select mobile if there is any user create a code and SMS it
                mobile = request.data['mobile']
                user = User.objects.filter(mobile=mobile).get()
                # Check it there is a valid code within 2 minutes Return error else return true
                if user:
                    try:
                        # Get ActivationCode for user
                        latest = ActivationCode.objects.latest('created_at')
                        now = datetime.now(timezone.utc)
                        delay = latest.created_at + timedelta(minutes=2)

                        if latest and (now <= delay):
                            return Response({'status': 'WAIT', 'detail': "Wait for 2 minutes"},
                                            status=status.HTTP_406_NOT_ACCEPTABLE)
                    except ObjectDoesNotExist as e:
                        pass

                    # create and send activation code
                    otp_utl = ActivationCodeUtil()
                    otp_utl.send_otp(user=user)
                    response = Response({'code': 'true'}, status=status.HTTP_200_OK)
                    return response
            except Exception:
                # import traceback
                # traceback.print_exc()  # prints to stdout
                # print(Exception)
                return Response({'code': 'false', 'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        return Response({'code': 'false', 'detail': 'Mobile is not provided.'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    permission_classes = ()
    throttle_scope = 'verify_code'

    def post(self, request, *args, **kwargs):
        if request.data and 'code' in request.data:
            code = request.data['code']
            now_two = datetime.now(timezone.utc) + timedelta(minutes=2)
            is_valid = ActivationCode.objects.filter(created_at__lte=now_two).filter(is_used=False) \
                .filter(activation_code=code).all()
            if is_valid:
                is_valid = is_valid[0]
                is_valid.is_used = True
                is_valid.save()
                user = User.objects.get(pk=is_valid.user_id)
                token = self.create_token(user)
                return Response({'token': token, 'name': user.display_name, 'about': user.about},
                                status=status.HTTP_202_ACCEPTED)

        return Response({'status': 'false'}, status=status.HTTP_403_FORBIDDEN)

    def create_token(self, user):
        token, created = Token.objects.update_or_create(user=user)
        return {
            'code': 'true',
            'access': str(token),
        }


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'logout'

    def post(self, request):
        try:
            request.user.auth_token.delete()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class SpaceListView(APIView, PaginationHandlerMixin):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Space.objects.all()
    pagination_class = PageNumberPagination
    serializer_class = SpaceSerializer
    page_size = 20
    throttle_scope = 'space'

    def get(self, request):
        spaces = Space.objects.order_by('-created_at').all()
        for space in spaces:
            space.is_following = False
            post_count = Utils.space_post_count(space)
            space.post_count = post_count
            try:
                follow = space.space_followed.filter(space_id=space)\
                    .filter(followed_by=request.user)\
                    .latest('created_at')
                space.is_following = not follow.unfollow_space  # We check if user is following
            except Exception as e:
                pass
        # Pagination
        serializer = self.prepare_pagination(spaces)
        # @todo weill be removed serializer = SpaceSerializer(spaces, many=True)
        return Response(serializer.data)


class MySpaceListView(APIView, PaginationHandlerMixin):
    pagination_class = PageNumberPagination
    serializer_class = SpaceSerializer
    throttle_scope = 'space'
    page_size = 20

    def get(self, request):
        spaces_joined = SpaceMembership.objects.filter(followed_by=request.user).filter(unfollow_space=False)
        spaces = Space.objects.filter(id__in=spaces_joined.values('space'))
        for space in spaces:
            post_count = Utils.space_post_count(space)
            space.post_count = post_count
            space.is_following = False
            try:
                follow = space.space_followed.filter(space_id=space).filter(followed_by=request.user)\
                    .latest('created_at')
                space.is_following = not follow.unfollow_space  # We check if user is following
            except Exception as e:
                pass
        # Pagination
        serializer = self.prepare_pagination(spaces)
        # @todo will be removed serializer = SpaceSerializer(spaces, many=True)
        return Response(serializer.data)


class SpaceDetailView(APIView):
    serializer_class = SpaceSerializer
    throttle_scope = 'space'

    def get_object(self, request, slug):
        try:
            space = Space.objects.get(slug=slug)
            space.is_following = False
            post_count = Utils.space_post_count(space)
            space.post_count = post_count
            try:
                follow = space.space_followed.filter(space_id=space)\
                    .filter(followed_by=request.user)\
                    .latest('created_at')
                space.is_following = not follow.unfollow_space  # We check if user is following
            except Exception as e:
                pass

            return space
        except Space.DoesNotExist:
            raise Http404

    def get(self, request, slug):
        space = self.get_object(request, slug)
        serializer = SpaceSerializer(space)
        return Response(serializer.data)

    # Create a space
    # @todo WIP
    def post(self, request):
        serializer = SpaceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SymbolsListView(APIView, PaginationHandlerMixin):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Space.objects.filter(symbol__isnull=False).all()
    pagination_class = PageNumberPagination
    serializer_class = SpaceSerializer
    page_size = 20
    throttle_scope = 'space'

    def get(self, request):
        spaces = Space.objects.filter(symbol__isnull=False).order_by('-created_at').all()
        for space in spaces:
            space.is_following = False
            post_count = Utils.space_post_count(space)
            space.post_count = post_count
            try:
                follow = space.space_followed.filter(space_id=space)\
                    .filter(followed_by=request.user)\
                    .latest('created_at')
                space.is_following = not follow.unfollow_space  # We check if user is following
            except Exception as e:
                pass
        # Pagination
        serializer = self.prepare_pagination(spaces)
        # @todo weill be removed serializer = SpaceSerializer(spaces, many=True)
        return Response(serializer.data)


class SpacePostsView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    serializer_class = SpacePostSerializer
    throttle_classes = [CustomPostThrottle]

    # parser_classes = [FileUploadParser]

    def get_object(self, request, slug, flag='published'):
        flag = 'P' if flag == 'published' else 'D'
        try:
            posts = Post.objects.select_related('space').filter(status=flag) \
                .filter(space__slug=slug) \
                .filter(deleted_at__isnull=True)

            if flag.upper() == 'draft':
                return posts.filter(created_by=request.user).all()
            return posts.all()

        except Space.DoesNotExist:
            raise Http404

    def get(self, request, slug, flag='published'):
        flag = flag.lower()
        if request.user.is_authenticated:
            flag = 'published'
        posts = self.get_object(request, slug, flag)
        for post in posts:
            post.comment_count = Utils.post_comment_count(post)
            post.space_slug = post.space.slug

        # Pagination
        serializer = self.prepare_pagination(posts)
        # @todo will be removed: serializer = SpacePostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Add a new post
    def post(self, request, slug):
        data = request.data
        errors = {}
        if 'title' not in data:
            errors['title'] = "Title can not be empty!"
        if 'description' not in data:
            errors['description'] = "Description can not be empty!"

        # I did not use validator. there was a problem with created_by
        # serializer = SpacePostSerializer(data=data)
        # if serializer.is_valid():
        #    serializer.save()
        #    return Response(serializer.data)
        if len(errors) > 0:
            return Response(errors, status=400)
        else:
            space = Space.objects.get(slug=slug)

            # Check if user is a member
            try:
                isFollowing = space.space_followed.filter(space_id=space).filter(followed_by=request.user).get()
            except Exception as e:
                raise Http404

            post = Post()
            post.title = data['title']
            post.description = data['description']
            post.created_by = request.user
            post.status = data['status'] if ('status' in data) else 'D'
            post.space = space
            post.comment_count = 0
            post.save()

            post.space_slug = space.slug  # For serialization

            if 'status' in data and data['status'] == 'P':
                # @todo  We can add it to queue to update the activity streamm later.
                action = Action()
                action.user = request.user
                action.space = space
                action.verb = 'PTC'
                action.target = post
                action.save()

            if 'file' in data:
                img = Image.open(data['file'])
                file_obj = data['file']

                attachment = Attachment()
                attachment.post_id = post.id
                attachment.title = img.filename
                attachment.file_name = img.filename
                attachment.file_uri = request.data['file']
                attachment.mime_type = img.format
                attachment.created_by = request.user
                attachment.save()

            serializer = SpacePostSerializer(post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Update a post
    def put(self, request, slug, pk):
        post = None
        try:
            post = Post.objects.filter(created_by=request.user).get(pk=pk)
        except Exception as e:
            raise Http404

        data = JSONParser().parse(request)
        errors = {}
        if not 'title' in data:
            errors['title'] = "Title can not be empty!"
        if not 'description' in data:
            errors['description'] = "Description can not be empty!"
        if len(errors) > 0:
            return Response(errors, status=400)
        else:
            post.title = data['title']
            post.description = data['description']
            post.created_by = request.user
            post.status = data['status'] if ('status' in data) else 'D'
            post.save()
            serializer = SpacePostSerializer(post)
            # check if it is already in actions

            in_stream = Action.objects.filter(target_id=pk).exists()
            if not in_stream:
                action = Action()
                action.user = request.user
                action.space = post.space_id
                action.verb = 'PTC'
                action.target = post
                action.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, slug, pk):
        post = None
        try:
            post = Post.objects.filter(created_by=request.user).get(pk=pk)
            post.deleted_at = datetime.now()
            post.deleted_by = request.user
            Comment.objects.filter(post=post).update(deleted_at=datetime.now(), visible=False, deleted_by=request.user)
            return Response({}, status.HTTP_202_ACCEPTED)
        except Exception as e:
            raise Http404


class SinglePostsView(APIView):
    serializer_class = SpacePostSerializer
    throttle_classes = [CustomPostThrottle]

    def get_object(self, request, slug, flag='published'):
        flag = 'P' if flag == 'published' else 'D'
        try:
            post = Post.objects.select_related('space')\
                .filter(slug=slug) \
                .filter(status=flag) \
                .filter(deleted_at__isnull=True)
            return post.get()
        except Space.DoesNotExist:
            raise Http404

    def get(self, request, slug, flag='published'):

        if request.user.is_authenticated:
            flag = 'published'
        post = self.get_object(request, slug, flag)

        post_obj = post
        post_obj.space_slug = post.space.slug
        post_obj.comment_count = Utils.post_comment_count(post)

        serializer = SpacePostSerializer(post_obj, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostAttachmentView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    serializer_class = AttachmentSerializer
    parser_classes = [FileUploadParser]

    def put(self, request, slug):
        errors = {}
        if 'file' not in request.data:
            errors['image_file'] = "Image can not be empty!"
            if len(errors) > 0:
                return Response(errors, status=400)
        user = request.user

        post_query_set = Post.objects.filter(slug__contains=slug) \
            .filter(deleted_at__isnull=True) \
            .filter(user=user)
        post = get_object_or_404(post_query_set)

        img = Image.open(request.data['file'])
        file_obj = request.data['file']
        file_obj.post_id = post
        attachment = Attachment()
        attachment.title = img.filename
        attachment.file_name = img.filename
        attachment.file_uri = request.data['file']
        attachment.mime_type = img.format
        attachment.created_by = request.user
        attachment.save()

        serializer = AttachmentSerializer(attachment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostBookmarkView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'post_scope'

    def get(self, request):

        page = 1
        if 'page' in request.GET:
            page = int(request.GET['page'])

        query_set = Bookmarks.objects.filter(user=request.user).filter(deleted_at__isnull=True)
        paginator = ManualPaginator(query_set.count(), request.build_absolute_uri('?'))
        start_offset = paginator.paginator(page)
        bookmarks = query_set.all()[start_offset[0]: start_offset[1]]
        posts = []
        for bookmark in bookmarks:
            post = bookmark.object_bookmarked
            post.comment_count = Utils.post_comment_count(post)
            posts.append(post)

        serializer = SpacePostSerializer(posts, many=True, )

        return Response(paginator.get_paginated_response(serializer.data, page),
                        status=status.HTTP_200_OK,
                        )

    # bookmark a post
    def put(self, request, slug):
        post = Post.objects.filter(slug__contains=slug).filter(deleted_at__isnull=True).all()

        bookmark = Bookmarks()
        bookmark.user = request.user
        bookmark.object_bookmarked = post[0]
        bookmark.save()
        return Response(None, status=status.HTTP_201_CREATED, )

    # Remove bookmarked post
    def delete(self, request, slug):
        post = None
        try:
            post = Post.objects.filter(slug__contains=slug).filter(deleted_at__isnull=True).all()

            bookmark = Bookmarks.objects.filter(user=request.user).filter(object_bookmarked_id=post[0].id).all()
            bk = bookmark[0]
            bk.deleted_at = datetime.now()
            bk.save()
            return Response(None, status=status.HTTP_202_ACCEPTED, )
        except Exception as e:
            raise Http404


class PostVoteView(APIView):
    throttle_scope = 'vote'

    # To vote up
    def put(self, request, slug):
        user = request.user
        # Get the post

        post = get_object_or_404(Post, slug=slug, status='P')

        # check if it is already voted
        try:
            vote = Vote.objects.filter(given_by=user) \
                .filter(given_vote_on_post=post) \
                .latest('created_at')
        except Vote.DoesNotExist:
            vote = None

        if not vote or (vote and vote.given_vote_type == 'DWN'):
            # add vote
            vote_up = Vote(given_by=user, given_vote_on_post=post, given_object_type='PST', given_vote_type='UP')
            vote_up.save()

            # Add to counter
            Post.objects.filter(pk=post.id).update(total_votes_up=F('total_votes_up') + 1)

            if vote and vote.given_vote_type == 'DWN':
                Post.objects.filter(pk=post.id).update(total_votes_down=F('total_votes_down') - 1)

        else:
            # Do nothing
            pass
        return Response(None, status=status.HTTP_202_ACCEPTED, )

    # To vote down
    def delete(self, request, slug):
        user = request.user
        # Get the post

        post = get_object_or_404(Post, slug=slug, status='P')

        # check if it is already voted
        try:
            vote = Vote.objects.filter(given_by=user) \
                .filter(given_vote_on_post=post) \
                .latest('created_at')
        except Vote.DoesNotExist:
            vote = None

        if not vote or (vote and vote.given_vote_type == 'UP'):
            # add vote
            vote_down = Vote(given_by=user, given_vote_on_post=post, given_object_type='PST', given_vote_type='DWN')
            vote_down.save()

            # Add to down counter
            Post.objects.filter(pk=post.id).update(total_votes_down=F('total_votes_down') + 1)

            if vote and vote.given_vote_type == 'UP':
                Post.objects.filter(pk=post.id).update(total_votes_up=F('total_votes_up') - 1)

        else:
            # Do nothing
            pass
        return Response(None, status=status.HTTP_202_ACCEPTED, )


class GlobalStreamView(APIView, PaginationHandlerMixin):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = BasicPagination
    serializer_class = SpacePostSerializer
    page_size = 20

    def get(self, request):
        #  Get spaces for the member
        # @todo should we exclude user actions.exclude(user=request.user)
        actions = Action.objects
        if request.user.is_authenticated:
            user = request.user
            # @todo first get users SpaceMembership from redis cache. If no cache select it and add it to redis for the user
            space_followed = SpaceMembership.objects.filter(followed_by=user).values_list('space_id', flat=True)
            actions = actions.filter(space_id__in=space_followed).filter(is_notification=False).filter(verb='PTC') \
                .values_list('target_id', flat=True)
        else:
            actions = actions.filter(is_notification=False).filter(verb='PTC') \
                .values_list('target_id', flat=True)

        try:
            posts = Post.objects.prefetch_related('space').filter(id__in=actions).all()
            for post in posts:
                post.comment_count = Utils.post_comment_count(post)
                post.space_slug = post.space.slug

        except Space.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)
        # Pagination
        serializer = self.prepare_pagination(posts)
        # serializer = SpacePostSerializer(posts, many=True,)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get all members
class SpaceMembersView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    serializer_class = SpaceMemberSerializer

    def get(self, request, pk, format=None):
        space_members = SpaceMembership.objects.filter(space_id=pk).filter(unfollow_space=0).all()
        # Pagination
        serializer = self.prepare_pagination(space_members)
        # @todo will be removed serializer = SpaceMemberSerializer(space_members, many=True)

        return Response(serializer.data)


# Join a space
class SpaceMemberView(APIView):
    throttle_scope = 'space'

    # JOIN
    def put(self, request, pk, format=None):
        user = request.user
        try:
            space = Space.objects.get(pk=pk)
            space_member = SpaceMembership(space_id=space.id, followed_by=user, unfollow_space=False)
            space_member.save()
            return Response(status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # LEAVE the space
    def delete(self, request, pk, format=None):
        user = request.user
        space_member = SpaceMembership.objects.filter(space_id=pk).filter(followed_by=user).get()
        space_member.unfollow_space = True
        space_member.save()
        return Response(status=status.HTTP_200_OK)


class PostCommentsView(APIView, PaginationHandlerMixin):
    pagination_class = BasicPagination
    serializer_class = PostCommentSerializer
    throttle_classes = [CustomCommentThrottle]

    def get(self, request, slug):
        post = Post.get_object_404(slug=slug)
        comments = Comment.objects.raw('SELECT node.id, node.parent_comment_id, (COUNT(parent.id) - 1) '
                                       'AS depth, node.deleted_at FROM social_comment AS node, social_comment AS parent '
                                       'WHERE node.lft BETWEEN parent.lft AND parent.rgt '
                                       'and node.post_id = %s '
                                       'GROUP BY node.id,node.parent_comment_id '
                                       'ORDER BY node.id', [post.id])

        for comment in comments:
            if comment.deleted_at is not None:
                comment.id = 0
                comment.body = '[DELETED]'
                comment.created_by = None
                comment.created_at = None
                comment.total_votes_up = 0
                comment.total_votes_down = 0
        # Pagination
        serializer = self.prepare_pagination(comments)
        # @todo will be removed: serializer = PostCommentSerializer(comments, many=True)

        return Response(serializer.data)

    # create comment
    def post(self, request, pk):
        data = JSONParser().parse(request)
        errors = {}
        if not 'body' in data:
            errors['body'] = "Comment can not be empty!"

        if len(errors) > 0:
            return Response(errors, status=400)
        else:
            post = Post.objects.get(pk=pk)
            post.comment_depth = post.comment_depth + 1
            post.save()

            rgt = 2  # right
            lft = 1  # left
            parent_comment_id = None
            if 'parent_comment_id' in data:
                parent_comment_id = int(data['parent_comment_id'])
                comment = Comment.objects.get(pk=parent_comment_id)
                if comment:
                    lft = comment.rgt
                    rgt = lft + 1
                    Comment.objects.filter(post=post).filter(rgt__gte=comment.rgt).update(rgt=F('rgt') + 2)
            '''SELECT node.id, (COUNT(parent.id) - 1) AS depth FROM social_comment AS node, social_comment AS parent WHERE node.lft BETWEEN parent.lft AND parent.rgt GROUP BY node.id ORDER BY node.lft'''
            comment = Comment()
            comment.body = data['body']
            comment.created_by = request.user
            comment.post = post
            comment.lft = lft
            comment.rgt = rgt
            comment.parent_comment_id = parent_comment_id
            comment.depth = post.comment_depth + 1
            comment.save()
            return Response(status=status.HTTP_201_CREATED)

    # Delete post
    def delete(self, request, pk):
        try:
            comment = Comment.objects.filter(created_by=request.user).get(pk=pk)
            comment.visible = False
            comment.deleted_at = datetime.now()
            comment.deleted_by = request.user
            comment.save()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)


# USER
class UserView(APIView):
    permission_classes = ()

    def post(self, request):
        # Get all fields and do a little clean up first.
        first_name = str.lower(str.strip(request.data["first_name"])) if "first_name" in request.data else False
        last_name = str.lower(str.strip(request.data["last_name"])) if "last_name" in request.data else False
        email = str.lower(str.strip(request.data["email"])) if "email" in request.data else False
        mobile = str.lower(str.strip(request.data["mobile"])) if "mobile" in request.data else False
        username = str.lower(str.strip(request.data["username"])) if "username" in request.data else None
        #invitor_code = str.lower(str.strip(request.data["invitor_code"])) if "invitor_code" in request.data else False

        if not first_name or not last_name or not mobile or not email:
            return Response({"detail": "Incomplete registration data."}, status.HTTP_400_BAD_REQUEST)

        # Check if mobile and email is already exists
        user_exists = User.objects.filter(Q(email=email) | Q(mobile=mobile)).exists()
        if user_exists:
            return Response({"detail": "User with email/mobile already exists!"}, status.HTTP_400_BAD_REQUEST)

        if username is not None:
            # Check if username is unique and valid
            v = re.compile(r'^[a-z]+[a-z0-9_]{2,29}$')
            is_username_valid = v.match(username)

            if not is_username_valid or len(username) > 29:
                return Response({"detail": "Username is not valid."}, status.HTTP_400_BAD_REQUEST)
            is_username_exists = User.objects.filter(display_name=username).exists()
            if is_username_exists:
                return Response({"detail": "Username already exists"}, status.HTTP_400_BAD_REQUEST)

        # query_set = User.objects.filter(invitation_code=invitor_code)
        # invitor_user = get_object_or_404(query_set)

        #if invitor_user.invitation_counter <= 0:
        #    return Response({"detail": "No more registration for this user. Try another link or next month."},
        #                    status.HTTP_403_FORBIDDEN)

        # Create user and send SMS
        user = User.objects.create_user(email, mobile, first_name, last_name, username)

        # Note invitor and invitee
        #invitor_user.invitation_counter -= 1
        #invitor_user.save()
        #user.invited_by = invitor_user
        #invitation_record = Invitation(invitor_id=invitor_user.id, invitee_id=user.id)
        #invitation_record.save()

        # create and send activation code
        # !!! We do not send, Instead we redirect the user to login at the frontendd
        # otp_utl = ActivationCodeUtil()
        # otp_utl.send_otp(user=user)

        # Get all auto join Spaces
        spaces_to_join = Space.objects.filter(auto_add_new_members=True).all()
        bulk_space_membership = []
        for space in spaces_to_join:
            bulk_space_membership.append(SpaceMembership(followed_by=user, space=space))

        SpaceMembership.objects.bulk_create(bulk_space_membership)

        # Return Success
        return Response({"detail": "Welcome alien!"}, status.HTTP_200_OK)

    def get_object(self, request, pk=None):
        if not pk:
            return request.user
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk=None, format=None):
        user = self.get_object(request, pk)

        if pk is None or int(pk) == request.user.id:
            serializer = MyAccountSerializer(user)
        else:
            serializer = UserSerializer(user)
        return Response(serializer.data)

    # Update user
    def put(self, request):
        user = request.user
        user.first_name = request.data["first_name"] if 'first_name' in request.data else request.user.first_name
        user.last_name = request.data["last_name"] if 'last_name' in request.data else request.user.last_name
        user.about = request.data["about"] if 'about' in request.data else request.user.about
        user.show_real_name = request.data[
            "show_real_name"] if 'show_real_name' in request.data else request.user.show_real_name
        user.save()
        return Response(data={'detail': 'Profile Updated!'}, status=status.HTTP_200_OK)


'''
        if request.data["new_password"] and request.data["re_new_password"] \
                and (request.data["new_password"] == request.data["re_new_password"]):
            from django.contrib.auth.hashers import make_password
            user.password = make_password(request.data["new_password"])
        else:
            return Response(data={'detail': 'Password did not match.'}, status=status.HTTP_406_NOT_ACCEPTABLE)
'''


class ReportView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, slug):
        post_query_set = Post.objects.filter(slug=slug).exclude(created_by=request.user)
        post = get_object_or_404(post_query_set)

        already_reported = Report.objects.filter(post=post).filter(created_by=request.user).exists()
        if already_reported:
            return Response({'detail': 'Already reported!'}, status.HTTP_406_NOT_ACCEPTABLE)

        report = Report()
        report.post = post
        report.report_type = request.data['report_type']
        report.created_by = request.user
        report.save()
        return Response({'detail': 'Report sent!'}, status.HTTP_202_ACCEPTED)

#username checker
class InvitationHelperView(APIView):

    def get(self, request, username):
        v = re.compile(r'^[a-z]+[a-z0-9_]{2,29}$')
        is_username_valid = v.match(username)

        if not is_username_valid or len(username) > 29:
            return Response({"detail": "Username is not valid."}, status.HTTP_400_BAD_REQUEST)
        is_username_exists = User.objects.filter(display_name=username).exists()
        if is_username_exists:
            return Response({"detail": "Username already exists"}, status.HTTP_400_BAD_REQUEST)

# Invitation Helper
'''
class InvitationHelperView(APIView):

    def post(self, request):
        invitor_code = request.data["invitor_code"] if "invitor_code" in request.data else False
        print(invitor_code)
        if not invitor_code:
            return Response({"detail": "Incomplete registration data."}, status.HTTP_400_BAD_REQUEST)
        query_set = User.objects.filter(invitation_code=invitor_code)
        invitor_user = get_object_or_404(query_set)

        if invitor_user.invitation_counter <= 0:
            return Response({"detail": "No more registration for this user. Try another link or try next month."},
                            status.HTTP_403_FORBIDDEN)
        else:
            return Response({"detail": "Invitation is valid"}, status.HTTP_202_ACCEPTED)
'''


# Creating and sending OTP code
# @todo move to a better place!
class ActivationCodeUtil:
    def get_code(self):
        return random.randrange(100000, 999999)

    def create_otp(self, user):
        activation = ActivationCode()
        activation.activation_code = self.get_code()
        activation.user_id = user.id
        activation.save()
        return activation

    def send_otp(self, user, activation_code=None):
        if activation_code is None:
            activation_code = self.create_otp(user)

        # Send token
        try:
            token = SMSToken.objects.get(pk=1)
            result = send_activation_code.delay(user.mobile, activation_code.activation_code, token.token)
            return result
        except Exception as e:
            return False