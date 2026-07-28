import math


class _ApiPaginator:
    def __init__(self, total: int, per_page: int) -> None:
        self.count = total
        self.per_page = per_page
        self.num_pages = max(1, math.ceil(total / per_page))
        self.page_range = range(1, self.num_pages + 1)


class ApiPage:
    """Mimics Django's Page interface for use with the pagination partial template."""

    def __init__(self, items: list, total: int, page: int, per_page: int) -> None:
        self.object_list = items
        self.number = page
        self.paginator = _ApiPaginator(total, per_page)

    @property
    def has_previous(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.paginator.num_pages

    def previous_page_number(self) -> int:
        return self.number - 1

    def next_page_number(self) -> int:
        return self.number + 1

    def __iter__(self):
        return iter(self.object_list)

    def __len__(self) -> int:
        return len(self.object_list)

    def __bool__(self) -> bool:
        return bool(self.object_list)
