from rest_framework.throttling import UserRateThrottle


class CustomPostThrottle(UserRateThrottle):
    scope = 'post_scope'

    def allow_request(self, request, view):
        """ if request.method == 'GET':
             self.scope = 'get_scope'
             self.rate = '1000/hour'
             return True"""
        if request.method == 'POST' or request.method == 'PUT' or request.method == 'DELETE':
            self.scope = 'post_scope'
            self.rate = '50/day'
            return True

        return super().allow_request(request, view)


class CustomCommentThrottle(UserRateThrottle):
    scope = 'comment_scope'

    def allow_request(self, request, view):
        """ if request.method == 'GET':
             self.scope = 'get_scope'
             self.rate = '1000/hour'
             return True"""
        if request.method == 'POST' or request.method == 'PUT' or request.method == 'DELETE':
            self.scope = 'post_scope'
            self.rate = '2/minute'
            return True

        return super().allow_request(request, view)