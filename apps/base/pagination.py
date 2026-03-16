from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"  # enables ?page_size=50
    max_page_size = 200
    page_query_param = "page"            # default is "page" anyway, kept for clarity