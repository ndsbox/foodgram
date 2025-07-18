from rest_framework.pagination import PageNumberPagination

from .constants import PAGE_SIZE


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
