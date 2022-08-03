# coding=utf-8

from datetime import timedelta

from requests import session

from catalog.services import QueryBase
from catalog import models


class ImportItemQuery(QueryBase):
    """
    Query lịch sử import theo bộ filter
    """
    model = models.ResultImport

    def apply_filters(self, filters):
        """
        Apply filter for Result Import

        :param filters:
        :return:
        """
        status = filters.get('status')
        if status:
            self.query = self.query.filter(
                self.__class__.model.status == status
            )

        self.query = self.query.filter(
            self.__class__.model.import_id == filters.get('import_id')
        )

        query = filters.get('query')
        if query:
            self.query = self.query.filter(
                self.__class__.model.data.like('%{}%'.format(query))
            )
