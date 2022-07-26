import math
import json


class PaginationHandlerMixin(object):
    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator

    def paginate_queryset(self, queryset):

        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset,
                                                self.request, view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def prepare_pagination(self, data, many=True):
        data = self.paginate_queryset(data)
        if data is not None:
            serializer = self.get_paginated_response(self.serializer_class(data, many=many).data)
        else:
            serializer = self.serializer_class(data, many=many)
        return serializer


class ManualPaginator(object):
    limit = 10
    start = 0
    offset = limit
    total_page_count = 1

    def __init__(self, data_count, url):
        self.limit = 10
        self.total_page_count = math.ceil(data_count / self.limit)
        print(math.ceil(data_count / self.limit))
        self.data_count = data_count
        self.url = url

    def total(self, total):
        self.total_page_count = total
        return self.total_page_count

    def limit(self, limit=10):
        self.limit = limit
        return self.limit

    def paginator(self, page=1):
        page = int(page)
        if page == 1 or page < 1:
            return self.start, self.offset
        else:
            self.start = (page - 1) * 10
            self.offset = self.start + self.limit
            return self.start, self.offset - 1

    def next(self, url, page=1):
        if self.total_page_count >= page:
            return f"{url}?page={self.total_page_count}"
        return f"{url}?page={page + 1}"

    def previous(self, url, page):
        if page <= 1:
            return f"{url}?page=1"
        return f"{url}?page={page - 1}"

    def get_paginated_response(self, data, page):
        response_payload = {
            "count": self.data_count,
            "next": self.next(self.url, page),
            "previous": self.previous(self.url, page),
            "results": data
        }
        return response_payload
    def count(self):
        pass
