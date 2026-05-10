from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """По умолчанию 10 записей; через query можно попросить другой размер, но не больше max."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
