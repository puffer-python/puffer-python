# coding=utf-8
import time

from sqlalchemy import or_, not_, text
from sqlalchemy.orm import joinedload
from flask_login import current_user
from catalog.services import Singleton
from catalog import models
from .query import CategoryQuery, CategoryRepository, ProductCategoryQuery
from catalog.extensions.signals import (
    category_created_signal,
    clone_master_category_request_signal,
    category_apply_shipping_type_to_sku_signal, ram_category_created_signal, ram_category_updated_signal,
)
from catalog.services.master_categories import MasterCategoryService
import logging

from catalog.extensions.exceptions import BadRequestException
from catalog.utils.validation_utils import validate_required
from catalog.models import db
from catalog.services.shipping_types.category_shipping_type import CategoryShippingTypeService
from ..attribute_sets import AttributeSetService

_logger = logging.getLogger(__name__)


def apply_shipping_type_to_skus(category_id, shipping_type_ids=[]):
    entity = models.Category.query.get(category_id)
    validate_required(entity, f'Không tồn tại bản ghi có id = {category_id} trong bảng categories')
    sell_id = current_user.seller_id
    if entity.seller_id != sell_id:
        raise BadRequestException('Bạn không quản lý ngành hàng này')
    if not shipping_type_ids and not entity.shipping_types:
        raise BadRequestException('Ngành hàng này không có loại hình vận chuyển')

    params = {
        'email': current_user.email,
        'created_from': f'categories.id={category_id}',
        'category_id': category_id,
        'path': f'{entity.path}/%'
    }
    insert_sql = text("""insert into sellable_product_shipping_type 
                        (sellable_product_id, 
                            shipping_type_id, 
                            created_by, 
                            created_from,
                            updated_by)
                        select a.sellable_product_id, 
                                b.shipping_type_id, 
                                :email,
                                :created_from,
                                :email from
                            (select sp.id as sellable_product_id from sellable_products sp
                                where sp.category_id in (SELECT cat.id 
                                    from categories cat where cat.id = :category_id 
                                                            or cat.path like :path)) a,
                            (select cst.shipping_type_id from category_shipping_type cst 
                                where cst.category_id = :category_id) b
                            where not exists (select 1 from sellable_product_shipping_type spst
                                                    where spst.sellable_product_id = a.sellable_product_id 
                                                                and spst.shipping_type_id = b.shipping_type_id)""")

    if shipping_type_ids:
        s_ids = ','.join(str(x) for x in shipping_type_ids)
        insert_sql = text(f"""insert into sellable_product_shipping_type 
                        (sellable_product_id, 
                            shipping_type_id, 
                            created_by, 
                            created_from,
                            updated_by)
                        select a.sellable_product_id, 
                                b.shipping_type_id, 
                                :email,
                                :created_from,
                                :email from
                            (select sp.id as sellable_product_id from sellable_products sp
                                where sp.category_id in (SELECT cat.id 
                                    from categories cat where cat.id = :category_id 
                                                            or cat.path like :path)) a,
                            (select st.id shipping_type_id from shipping_types st 
                                where st.id IN ({s_ids})) b
                            where not exists (select 1 from sellable_product_shipping_type spst
                                                    where spst.sellable_product_id = a.sellable_product_id 
                                                                and spst.shipping_type_id = b.shipping_type_id)""")
    db.engine.execute(insert_sql, params)
    db.session.commit()
    category_apply_shipping_type_to_sku_signal.send(category_id)


class CategoryService(Singleton):
    def __get_category_shipping_types(self, category_ids):
        category_shipping_types = models.CategoryShippingType.query.filter(
            models.CategoryShippingType.category_id.in_(category_ids)).all()
        shipping_type_ids = set(map(lambda x: x.shipping_type_id, category_shipping_types))
        map_categories_shipping_types = {}
        if shipping_type_ids:
            shipping_types = models.ShippingType.query.filter(models.ShippingType.id.in_(shipping_type_ids)).all()
            for cat_id in category_ids:
                a_cat_shipping_types = list(filter(lambda x: x.category_id == cat_id, category_shipping_types))
                a_cat_shipping_type_ids = map(lambda x: x.shipping_type_id, a_cat_shipping_types)
                map_categories_shipping_types[cat_id] = list(
                    filter(lambda x: x.id in a_cat_shipping_type_ids, shipping_types))
        return map_categories_shipping_types

    def get_list_categories(self, filters, page=0, page_size=10, **kwargs):
        query = CategoryQuery()
        if 'seller_id' in kwargs and filters.get('seller_ids') == None:
            if not kwargs['seller_id']:
                return [], 0
            query.restrict_by_seller(kwargs['seller_id'])
        query.apply_filters(filters)
        total_records = len(query)
        query.pagination(page, page_size)
        categories = query.all()
        category_ids = list(map(lambda x: x.id, categories))
        if category_ids:
            map_categories_shipping_types = self.__get_category_shipping_types(category_ids)
            for category in categories:
                category.mapping_shipping_types = map_categories_shipping_types.get(category.id) or []
        return categories, total_records

    def get_category_tree(self, category_id, seller_id=None):
        query = CategoryQuery()
        if seller_id:
            query.restrict_by_seller(seller_id)
        root = query.apply_filters({'id': category_id}).first()
        all_nodes = models.Category.query.filter(
            or_(
                models.Category.path.like(f'{root.id}/%'),
                models.Category.path.like(f'%/{root.id}/%'),
            ),
            models.Category.is_active.is_(True)
        ).all()
        all_nodes.append(root)
        for node in all_nodes:
            children = list(filter(lambda x: x.parent_id == node.id, all_nodes))
            if len(children) > 0:
                setattr(node, "_children", children)
        return root

    def create_category(self, data):
        master_cat_service = MasterCategoryService.get_instance()

        # Init path and depth
        path = ''
        depth = 1
        parent_id = data["parent_id"]
        if parent_id and parent_id != 0:
            parent = CategoryRepository.get_by_id(parent_id)
            path = str(parent.path) + '/'
            depth += parent.depth
        data["depth"] = depth
        data["path"] = path

        # Init master_category_id and attribute_set_id
        if not data.get("master_category_id"):
            recommended_master_category = master_cat_service.get_recommendation_category(
                name=data["name"],
                limit=1
            )
            if recommended_master_category:
                data["master_category_id"] = recommended_master_category[0].id

        inherited_cat = None
        if not data.get("attribute_set_id"):
            inherited_cat = self._get_attribute_set_inherited_category(path)

        if not data.get("attribute_set_id") and data.get("master_category_id"):
            master_category = master_cat_service.get_master_category(data["master_category_id"])
            data["attribute_set_id"] = master_category.attribute_set_id

        data["seller_id"] = current_user.seller_id

        shipping_types = data.pop("shipping_types", None)

        category = CategoryRepository.transaction_insert(data)
        category.path = category.path + str(category.id)
        category.is_active = True

        if shipping_types:
            for shipping_type_id in shipping_types:
                CategoryShippingTypeService.create(
                    category_id=category.id,
                    shipping_type_id=shipping_type_id,
                    auto_commit=False
                )

        models.db.session.commit()
        ram_category_created_signal.send({'id': category.id})

        if inherited_cat:
            return category, f"Tạo mới danh mục thành công. Danh mục sẽ thừa hưởng bộ thuộc tính " \
                             f"{inherited_cat.attribute_set.name} của danh mục cha: {inherited_cat.name}"

        return category, "Tạo mới danh mục thành công"

    def update_category(self, data, obj_id):
        """ For the case update parent_id
        Example:

        Current trees         If Move: parent B = F       If Move: parent B = C
               A                    A                           A
              / \                   |                          / \
             B   F                  F                         C   F
             |                      |                       / | \
             C                      B                       D E  B
            / \                     |
           D   E                    C
                                   / \
                                  D   E
        """
        current_node = models.Category.query.get(obj_id)
        # update_info to current node from "data"

        # update depth, path, is_active for current_node and child's current node
        parent_id = data.get("parent_id")
        send_parent_to_queue = False
        if parent_id is not None:
            parent_node = models.Category.query.get(parent_id)
            is_child = self._is_child(current_node, parent_id)  # check parent_id is child of current_node
            if is_child:
                self.move_node_to_new_parent(parent_node, current_node.parent)
                models.db.session.flush()
                self.move_node_to_new_parent(current_node, parent_node)
                send_parent_to_queue = True
            else:
                self.move_node_to_new_parent(current_node, parent_node)

        shipping_types = data.pop("shipping_types", None)
        if shipping_types is not None:
            CategoryShippingTypeService.delete(current_node.id, auto_commit=False)
            for shipping_type_id in shipping_types:
                CategoryShippingTypeService.create(current_node.id, shipping_type_id, auto_commit=False)

        for k, v in data.items():
            setattr(current_node, k, v)

        if send_parent_to_queue:
            ram_category_updated_signal.send(parent_node)

        is_adult = data.get("is_adult")

        if is_adult is not None and current_node.is_adult != is_adult:
            current_node.is_adult = is_adult

        models.db.session.commit()
        ram_category_updated_signal.send(current_node)

        inherited_cat = None
        if not data.get("attribute_set_id"):
            inherited_cat = self._get_attribute_set_inherited_category(current_node.path)

        if inherited_cat:
            return current_node, f"Cập nhập danh mục thành công. Danh mục sẽ thừa hưởng bộ thuộc tính " \
                                 f"{inherited_cat.attribute_set.name} của danh mục cha: {inherited_cat.name}"

        return current_node, "Cập nhập danh mục thành công"

    def _get_attribute_set_inherited_category(self, path):
        ancestor_categories = CategoryRepository.get_all_by_path(path)
        cat_ids = path.split("/")
        for id in reversed(cat_ids):
            for cat in ancestor_categories:
                if str(cat.id) == id and cat.attribute_set:
                    return cat

    def move_node_to_new_parent(self, current_node, parent_node):
        if parent_node is None:
            current_node.path = current_node.id
            current_node.depth = 1
            current_node.parent_id = 0
        else:
            current_node.path = "{}/{}".format(parent_node.path, current_node.id)
            current_node.depth = parent_node.depth + 1
            current_node.parent_id = parent_node.id

        child_nodes = current_node.children
        if child_nodes:
            for child_node in child_nodes:
                self.move_node_to_new_parent(child_node, current_node)

    def get_category_with_id(self, category_id):
        query = CategoryQuery().apply_filters({
            'id': category_id
        })
        query.query = query.query.options(
            joinedload('master_category').load_only('id', 'name', 'code', 'path')
        )

        category = query.first()
        # Find the first category has attribute_set in the tree levels
        attribute_set = None
        parent = category
        while parent:
            if getattr(parent, 'attribute_set'):
                attribute_set = parent.attribute_set
                break
            if not parent.parent:
                break
            parent = parent.parent

        if attribute_set:
            attribute_set_service = AttributeSetService.get_instance()
            # groups
            setattr(category, 'groups', list(attribute_set.groups))
            # attributes
            attributes = attribute_set_service.get_attributes_of_attribute_set(
                [group.id for group in attribute_set.groups]
            )
            setattr(category, 'attributes', attributes)
            # has_product
            has_product = False
            product = models.Product.query.filter(
                models.Product.attribute_set_id == attribute_set.id
            ).first()
            if product:
                has_product = True
            setattr(category, 'has_product', has_product)
        else:
            raise BadRequestException('Danh mục chưa có bộ thuộc tính')
        return category

    def get_category_with_code(self, category_code, seller_id):
        return models.Category.query.filter(models.Category.code == category_code,
                                            models.Category.seller_id == seller_id).first()

    def _is_child(self, current_node, id):
        if current_node.id == id:
            return True
        child_nodes = current_node.children
        check = False
        if child_nodes:
            for child_node in child_nodes:
                check = self._is_child(child_node, id)
                if check:
                    break
        return check

    def clone_from_master_category(self, **kwargs):
        clone_master_category_request_signal.send(kwargs)

    def clone_top_level_cat(self, master_cat_id, seller_id):
        check_cloned_cat = models.Category.query.filter(
            models.Category.master_category_id == master_cat_id,
            models.Category.seller_id == seller_id).first()
        if check_cloned_cat:
            return False
        master_cat_service = MasterCategoryService.get_instance()
        master_cat_tree = master_cat_service.get_master_category_tree(master_cat_id)
        if not master_cat_tree:
            return False
        root_cat = self.create_seller_cat_from_master_cat(master_cat_tree, None, seller_id)
        self.clone_cat_tree_from_master_cat(master_cat_tree, root_cat, seller_id)
        return root_cat

    def clone_cat_tree_from_master_cat(self, master_cat_root, root_cat, seller_id):
        _logger.info("Cloning children of master cat: %s" % master_cat_root.id)
        if root_cat:
            _logger.info("root cat: %s" % root_cat.id)
        if hasattr(master_cat_root, "_children") and master_cat_root._children:
            for child in master_cat_root._children:
                child_cat = self.create_seller_cat_from_master_cat(child, root_cat, seller_id)
                self.clone_cat_tree_from_master_cat(child, child_cat, seller_id)
        else:
            _logger.info("No child to clone for master cat: %s" % master_cat_root.id)

    def create_seller_cat_from_master_cat(self, master_cat: models.MasterCategory, parent, seller_id):
        path = ''
        depth = 1
        data = {
            "name": master_cat.name,
            "code": "%s_%s" % (seller_id, master_cat.code),
            "parent_id": parent.id if parent else None,
            "tax_in_code": master_cat.tax_in_code,
            "tax_out_code": master_cat.tax_out_code,
            "attribute_set_id": master_cat.attribute_set_id,
            "manage_serial": master_cat.manage_serial,
            "auto_generate_serial": master_cat.auto_generate_serial,
            "master_category_id": master_cat.id
        }
        if parent:
            path = str(parent.path) + '/'
            depth += parent.depth
        data["depth"] = depth
        data["path"] = path
        data["seller_id"] = seller_id
        category = CategoryRepository.transaction_insert(data)
        category.path = category.path + str(category.id)
        category.is_active = True
        models.db.session.flush()
        # models.db.session.commit() # Test to commit category eachtime a cat is created
        # category_created_signal.send(category)
        return category

    def create_category_on_srm(self, root_cat):
        time.sleep(1)  # wait before creating cart on srm to prevent srm from dying
        category_created_signal.send(root_cat)
        if hasattr(root_cat, "_children") and root_cat._children and isinstance(root_cat._children, list):
            for child in root_cat._children:
                self.create_category_on_srm(child)


def get_leaf_tree(cat_model=models.Category, seller_id=None):
    """
    Get all active leaf Categories. If all child cateogiries is inactive, the closest parent will be got as leaf
    """
    alias_cat = models.db.aliased(cat_model)

    query = cat_model.query.filter(
        cat_model.is_active == 1,
        not_(alias_cat.query.filter(
            alias_cat.parent_id == cat_model.id,
            alias_cat.is_active == 1
        ).exists())
    )

    if seller_id:
        query = query.filter(
            cat_model.seller_id == seller_id
        )

    return query


class ProductCategoryService:

    @staticmethod
    def get_product_category(product_ids, seller_ids):
        product_category_query = ProductCategoryQuery()
        product_category_filter = {
            'product_ids': product_ids,
            'seller_ids': seller_ids,
        }
        product_category_query.apply_filter(**product_category_filter)
        product_categories = product_category_query.all()
        return product_categories
