# coding=utf-8

from catalog.extensions.flask_cache import cache
from catalog import models as m
from catalog.models import db
from sqlalchemy import or_, and_


class AttributeSet(db.Model, m.TimestampMixin):
    """
    Lưu thông tin attribute set
    """
    __tablename__ = 'attribute_sets'

    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.String(100))
    is_default = db.Column(db.Integer, nullable=True, default=1)

    # @cache.memoize(300)
    def get_variation_attributes(self, get_all=True):
        group_ids = list(map(lambda x: x.id, self.groups))
        attr_group_attr = m.AttributeGroupAttribute.query.filter(
            m.AttributeGroupAttribute.is_variation.is_(True),
            m.AttributeGroupAttribute.attribute_group_id.in_(group_ids)
        ).all()
        attr_ids = list(map(lambda x: x.attribute_id, attr_group_attr))
        if get_all:
            return m.Attribute.query.filter(
                m.Attribute.id.in_(attr_ids)
            ).all()

        return attr_ids

    # @cache.memoize(300)
    def get_specifications_attributes(self):
        """
        :rtype: list[m.Attribute]
        :return: All attributes of the attribute_set which have is_variation = False (but not uom_ratio)
        """
        return m.Attribute.query.join(
            m.AttributeGroupAttribute,
            m.AttributeGroup
        ).filter(
            m.AttributeGroup.attribute_set_id == self.id,
            m.AttributeGroupAttribute.is_variation.is_(False)
        ).all()


class AttributeSetConfig(db.Model, m.TimestampMixin):
    def __setitem__(self, key, value):
        """
        Support direct assignment by dict
        :param key:
        :param value:
        :return:
        """
        if isinstance(value, list):
            pass

        setattr(self, key, value)

    __tablename__ = 'attribute_set_config'

    is_default = db.Column(db.Integer(), nullable=True)
    is_deleted = db.Column(db.Integer(), default=0)
    attribute_1_id = db.Column(db.Integer(), nullable=True)
    attribute_1_value = db.Column(db.Integer(), nullable=True)
    attribute_2_id = db.Column(db.Integer(), nullable=True)
    attribute_2_value = db.Column(db.Integer(), nullable=True)
    attribute_3_id = db.Column(db.Integer(), nullable=True)
    attribute_3_value = db.Column(db.Integer(), nullable=True)
    attribute_4_id = db.Column(db.Integer(), nullable=True)
    attribute_4_value = db.Column(db.Integer(), nullable=True)
    attribute_5_id = db.Column(db.Integer(), nullable=True)
    attribute_5_value = db.Column(db.Integer(), nullable=True)

    @property
    def attributes(self):
        res = []
        for i in range(5):
            attr = m.Attribute.query.get(getattr(self, f'attribute_{i + 1}_id'))
            opt = m.AttributeOption.query.get(getattr(self, f'attribute_{i + 1}_value'))
            if attr and opt:
                res.append({
                    'name': attr.name,
                    'value': opt.value
                })
        return res

    attribute_set_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'attribute_sets.id',
            name='fk_attribute_set_config_attribute_sets',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        )
    )
    attribute_set = db.relationship(
        'AttributeSet',
        backref='attribute_set_config',
        uselist=False
    )

    brand_id = db.Column(db.Integer(), db.ForeignKey('brands.id'), nullable=True)
    brand = db.relationship('Brand', backref='attribute_set_configs')


class AttributeSetConfigDetail(db.Model, m.TimestampMixin):
    __tablename__ = 'attribute_set_config_detail'

    attribute_set_config_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'attribute_set_config.id',
            name='fk_attribute_set_config_detail_attribute_set_config',
            onupdate='CASCADE',
            ondelete='RESTRICT'
        ),
    )
    attribute_set_config = db.relationship(
        'AttributeSetConfig',
        backref='details',
        uselist=False
    )

    field_display = db.Column(db.String(255), nullable=True)
    object_type = db.Column(db.String(255), nullable=True)
    object_value = db.Column(db.String(255), nullable=True)
    text_before = db.Column(db.String(255), nullable=True)
    text_after = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.Integer(), default=0)
