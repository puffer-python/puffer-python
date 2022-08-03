#coding=utf-8

from datetime import timedelta

from catalog.services import QueryBase
from catalog import models


class ImportHistoryQuery(QueryBase):
    """
    Query lịch sử import theo bộ filter
    """
    model = models.FileImport

    def apply_filters(self, filters):
        """
        Filter theo các điều kiện được truyền vào, bao gồm:
            - Kiểu import (product, attribute, ...)
            - Trạng thái import (chờ xử lý, hoàn tất, ...)
            - Khoảng thời gian upload file (từ ngày ... đến ngày ...)

        :param filters:
        :return:
        """
        hid = filters.get('id')
        if hid:
            self.query = self.query.filter(
                self.__class__.model.id == hid
            )

        import_type = filters.get('type')
        if import_type:
            self.query = self.query.filter(
                self.__class__.model.type.in_(import_type)
            )

        status = filters.get('status')
        if status:
            self.query = self.query.filter(
                self.__class__.model.status.in_(status)
            )

        start_at = filters.get('start_at')
        if start_at:
            self.query = self.query.filter(
                self.__class__.model.created_at >= start_at
            )

        end_at = filters.get('end_at')
        if end_at:
            self.query = self.query.filter(
                self.__class__.model.created_at <= end_at + timedelta(days=1)
            )

        created_by = filters.get('created_by')
        if created_by:
            self.query = self.query.filter(
                self.__class__.model.created_by.like(f'%{created_by}%')
            )
