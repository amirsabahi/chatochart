from django.urls import path
from . import views

app_name = 'social'
urlpatterns = [
        path('v1/login/', views.LoginView.as_view()),
        path('v1/login/verify/', views.VerifyCodeView.as_view()),
        path('v1/logout/', views.LogoutView.as_view()),

        # Main Stream
        path('stream/', views.GlobalStreamView.as_view(), name='stream'),

        # Space
        path('spaces/', views.SpaceListView.as_view(), name='space_list'),
        path('spaces/me', views.MySpaceListView.as_view(), name='my_space_list'),
        path('space/detail/<str:slug>/', views.SpaceDetailView.as_view(), name='space_detail'),
        path('symbols/', views.SymbolsListView.as_view(), name='symbol_list'),


        # Post(s)
        path('space/posts/<str:slug>/<str:flag>', views.SpacePostsView.as_view(), name='space_posts'),  # Get all posts
        path('space/post/<str:slug>/', views.SpacePostsView.as_view(), name='space_post_create'),  # Create a post
        path('space/post/<str:slug>/<int:pk>', views.SpacePostsView.as_view(), name='space_post_update'),  # Update given post
        path('post/<str:slug>/', views.SinglePostsView.as_view(), name='posts_detail'),  # Single post Detail
        path('post/attach/<str:slug>/', views.PostAttachmentView.as_view(), name='post_attachment'),  # Attach a file to a post
        path('post/vote/<str:slug>', views.PostVoteView.as_view(), name='vote'),
        path('bookmarks/', views.PostBookmarkView.as_view(), name='get_bookmark'),  # Get bookmark
        path('bookmarks/<str:slug>/', views.PostBookmarkView.as_view(), name='modify_bookmark'),  # add/remove bookmark
        path('report/post/<str:slug>/', views.ReportView.as_view(), name='report_post'),  # Report a post

        # Comment(s)
        path('post/comments/<str:slug>', views.PostCommentsView.as_view(), name='post_comments'),  # Get comments
        path('post/comment/<str:slug>', views.PostCommentsView.as_view(), name='post_create_comment'),  # Create/Delete comment


        # Space member(s) view
        path('space/members/<int:pk>/', views.SpaceMembersView.as_view(), name='space_members'),
        path('space/member/<int:pk>/', views.SpaceMemberView.as_view(), name='space_member'),

        # User
        path('user/<pk>/', views.UserView.as_view(), name='user'),
        path('user/me', views.UserView.as_view(), name='me'),
        path('register/user/', views.UserView.as_view(), name='register'),

        # Check if invitation is allowed for the given invitation code.
        # path('check/invitation/', views.InvitationHelperView.as_view(), name="invitation_check")
        path('check/invitation/', views.InvitationHelperView.as_view(), name="invitation_check")


        # Invitation
        #path('invite/', views.InviteView.as_view(), name='invite'),

        # Task test @todo remove
        #path('task/test', views.TaskQueueView.as_view(), name='task_test'),
]
