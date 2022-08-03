# coding=utf-8
import logging
from flask import g

from catalog.extensions import flask_restplus as fr
from catalog.services import shipping_policy as svr
from catalog.validators import shipping_policy as validators

from . import schema

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)

shipping_policy_ns = fr.Namespace(
    'shipping_policy',
    path='/shipping_policies',
    description='Manage shipping policy for providers'
)


@shipping_policy_ns.route('', methods=['GET', 'POST'])
class ShippingPolicies(fr.Resource):
    @shipping_policy_ns.expect(schema.ShippingPolicyListRequest, location='args')
    @shipping_policy_ns.marshal_with(schema.ShippingPolicyListSchema)
    def get(self):
        """

        :return:
        """
        params = g.args
        res = svr.get_shipping_policy_list(params)
        return res

    @shipping_policy_ns.expect(schema.ShippingPolicyCreateRequest, location='body')
    @shipping_policy_ns.marshal_with(schema_cls=schema.ShippingPolicySchema)
    def post(self):
        validators.CreateShippingPolicyValidator.validate(g.body)
        sp = svr.create_shipping_policy(g.body)
        return sp, "Tạo mới shipping rule thành công"


@shipping_policy_ns.route('/<int:policy_id>', methods=['GET', 'PATCH'])
class ShippingPolicy(fr.Resource):
    @shipping_policy_ns.expect(schema.ShippingPolicyUpdateRequest, location='body')
    @shipping_policy_ns.marshal_with(schema.ShippingPolicyUpdateResponse)
    def patch(self, policy_id):
        validators.UpdateShippingPolicyValidator.validate(g.body, policy_id)
        return svr.update_shipping_policy(policy_id, g.body), "Cập nhật shipping rule thành công"

    @shipping_policy_ns.marshal_with(schema_cls=schema.ShippingPolicySchema)
    def get(self, policy_id):
        return svr.get_shipping_policy(policy_id)
