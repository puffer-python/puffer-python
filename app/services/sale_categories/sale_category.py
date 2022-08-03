# coding=utf-8
import logging
import queue
import re

from flask_login import current_user
from sqlalchemy import or_, func

from catalog import models as m
from catalog import utils
from catalog.services import Singleton
from .query import SaleCategoryQuery


__author__ = 'Thanh.NK'
__logger__ = logging.getLogger(__name__)



class SaleCategoryService(Singleton):
    def get_sale_category_list(self, filters, page, page_size):
        """Get list sale_category
        """
        query = SaleCategoryQuery()
        query.apply_filters(filters)
        total_records = len(query)
        query.pagination(page, page_size)
        return query.all(), total_records

    def get_sale_category_tree(self, sale_category_id):
        root = m.SaleCategory.query.filter(
            m.SaleCategory.id == sale_category_id
        ).first()
        ret = {}
        parent_of = {root: None}
        q = queue.Queue()
        q.put(root)
        while not q.empty():
            curr_node = q.get()
            dump_data = {
                'id': curr_node.id,
                'code': curr_node.code,
                'name': curr_node.name,
            }
            parent = parent_of[curr_node]
            if parent:
                if 'children' not in parent:
                    parent['children'] = []
                parent['children'].append(dump_data)
            else:
                ret = dump_data
            for child in curr_node.children:
                parent_of[child] = dump_data
                q.put(child)
        return ret

    def update_position(self, id_node, parent_id, left_node_id):
        """
        Update sale category node

        :param: id_node, int: id of sale node
        :param: parent_id: int, id of parent node
        :param: left_node_id: int, left node id
        :return: None
        """
        current_node = m.SaleCategory.query.get(id_node)
        self._move_node(current_node, parent_id, left_node_id)
        self._update_path_for_tree(current_node, parent_id)

        return


    def _move_node(self, current_node, parent_id, left_node_id):
        """
        :param current_node:
        :param parent_id:
        :param left_node_id:
        :return:
        """
        new_siblings = m.SaleCategory.query.filter(
            m.SaleCategory.parent_id == parent_id,
            m.SaleCategory.id != current_node.id
        ).order_by(
            m.SaleCategory.priority
        ).all()

        if left_node_id:
            left_node = m.SaleCategory.query.get(left_node_id)
            index_left_node = new_siblings.index(left_node)
            new_siblings.insert(index_left_node + 1, current_node)
        else:
            new_siblings.insert(0, current_node)

        self.__resort_node(new_siblings)

        if current_node.parent_id != parent_id:
            current_siblings = m.SaleCategory.query.filter(
                m.SaleCategory.parent_id == current_node.parent_id,
                m.SaleCategory.id != current_node.id
            ).order_by(
                m.SaleCategory.priority
            ).all()
            self.__resort_node(current_siblings)

        current_node.parent_id = parent_id
        m.db.session.commit()


    def __resort_node(self, nodes):
        """
        :param nodes:
        :type nodes: list[m.SaleCategory]
        :return:
        """
        for i, node in enumerate(nodes):
            node.priority = i + 1

        return nodes


    def _update_path_for_tree(self, current_node, parent_id):
        """
        Use BFS for update path

        :param current_node:
        :param parent_id:
        """

        if not parent_id:
            current_node.path = current_node.id
            current_node.depth = 1
        else:
            parent_node = m.SaleCategory.query.get(parent_id)
            current_node.path = "{}/{}".format(parent_node.path, current_node.id)
            current_node.depth = parent_node.depth + 1

        child_nodes = m.SaleCategory.query.filter(
            m.SaleCategory.parent_id == current_node.id
        ).all()
        if child_nodes:
            for child_node in child_nodes:
                self._update_path_for_tree(child_node, current_node.id)

        m.db.session.commit()
        return


    def create_sale_category(self, data):
        """
        Chi tiết xem tại:
        https://jira.teko.vn/browse/SC-112
        :param data:
        :return:
        """
        path = ''
        depth = 1

        parent_id = data['parent_id']
        if parent_id:
            parent = m.SaleCategory.query.filter(
                m.SaleCategory.id == parent_id
            ).first()  # type: m.SaleCategory
            path = str(parent.path) + '/'
            depth += parent.depth

        category = m.SaleCategory()
        category.path = path
        category.depth = depth
        category.code = data.get('code')
        category.name = data.get('name')
        category.is_active = data.get('is_active')
        category.image = data.get('image')
        category.parent_id = parent_id

        # find the category's priority
        right_most = m.SaleCategory.query \
            .filter(m.SaleCategory.parent_id == parent_id) \
            .order_by(m.SaleCategory.priority.desc()) \
            .first()
        category.priority = (right_most.priority if right_most else 0) + 1
        category.seller_id = current_user.seller_id

        m.db.session.add(category)
        m.db.session.commit()
        category.path = category.path + str(category.id)

        return category


    def _check_edit_master_category(self, sale_category_id, name, code):
        name = utils.normalized(name)
        code = utils.normalized(code)
        category = m.SaleCategory.query.filter(
            m.SaleCategory.id != sale_category_id,
            or_(
                func.lower(m.SaleCategory.name) == name,
                func.lower(m.SaleCategory.code) == code
            )
        ).first()  # type: m.SaleCategory
        return category is None


    def _check_ancestor(self, sale_category):
        """
        Check ancestor
        :return: False if ancestor is inactive
        """
        parent = m.SaleCategory.query.get(sale_category.parent_id)
        if not parent:
            return True

        return parent.is_active == 1 and self._check_ancestor(parent)


    def _allow_edit_master_category(self, sale_category_id, is_active):
        sale_category = m.SaleCategory.query.get(sale_category_id)
        if not sale_category:
            return False

        if is_active and not self._check_ancestor(sale_category):
            return False
        return True


    def _deactivate_master_category(self, sale_category):
        """
        Deactivate a sale category and its children
        :type sale_category: m.SaleCategory
        """
        sale_category.is_active = 0
        m.db.session.add(sale_category)

        children = m.SaleCategory.query.filter(
            m.SaleCategory.parent_id == sale_category.id
        ).all()
        for child in children:
            self._deactivate_master_category(child)


    def _check_image_url(self, image_url):
        return re.match("(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|jpeg|png)",
                        image_url) is not None or image_url == ''


    def update_sale_category(self, sale_category_id, data):
        """

        :param sale_category_id:
        :param data:
        :return:
        """
        sale_category = m.SaleCategory.query.get(sale_category_id)
        for k, v in data.items():
            if hasattr(sale_category, k):
                setattr(sale_category, k, v)

        if not sale_category.is_active:
            self._deactivate_master_category(sale_category)
        m.db.session.commit()

        return sale_category
