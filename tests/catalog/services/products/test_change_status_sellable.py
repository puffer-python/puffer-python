# coding=utf-8
from unittest import mock

import pytest

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.products.sellable import update_sellable_editing_status


class UpdateStatusServiceTestCase(APITestCase):
    ISSUE_KEY = 'SC-458'

    def setUp(self):
        self.product = None
        self.variant = None
        self.sellable = None

    def _setup_data(self, product_status, variant_status, sellable_status):
        self.product = fake.product(editing_status_code=product_status)
        self.variant = fake.product_variant(product_id=self.product.id, editing_status_code=variant_status)
        self.sellable = fake.sellable_product(variant_id=self.variant.id, editing_status_code=sellable_status)

    def assert_status(self, product_status, variant_status, sellable_status):
        assert self.product.editing_status_code == product_status
        assert self.variant.editing_status_code == variant_status
        assert self.sellable.editing_status_code == sellable_status

    def test_check_updated_by(self):
        updated_by = fake.text()
        self._setup_data('processing', 'processing', 'processing')
        update_sellable_editing_status(ids=[self.sellable.id], status='pending_approval', updated_by=updated_by)
        self.assert_status('pending_approval', 'pending_approval', 'pending_approval')
        self.assertEqual(self.sellable.updated_by, updated_by)

    def test_changeProcessingToPendingApproval(self):
        self._setup_data('processing', 'processing', 'processing')
        update_sellable_editing_status(ids=[self.sellable.id], status='pending_approval', updated_by=fake.text())
        self.assert_status('pending_approval', 'pending_approval', 'pending_approval')

    def test_changeProcessingToPendingApproval__whenProductActived(self):
        self._setup_data('active', 'processing', 'processing')
        update_sellable_editing_status(ids=[self.sellable.id], status='pending_approval', updated_by=fake.text())
        self.assert_status('active', 'pending_approval', 'pending_approval')

    def test_changeProcessingToPendingApproval__whenVarianrActived(self):
        self._setup_data('active', 'active', 'processing')
        update_sellable_editing_status(ids=[self.sellable.id], status='pending_approval', updated_by=fake.text())
        self.assert_status('active', 'active', 'pending_approval')

    def test_changePendingApprovalToActive(self):
        self._setup_data('pending_approval', 'pending_approval', 'pending_approval')
        update_sellable_editing_status(ids=[self.sellable.id], status='active', updated_by=fake.text())
        self.assert_status('active', 'active', 'active')

    def test_changePendingApprovalToReject(self):
        self._setup_data('pending_approval', 'pending_approval', 'pending_approval')
        update_sellable_editing_status(ids=[self.sellable.id], status='reject', updated_by=fake.text())
        self.assert_status('reject', 'reject', 'reject')

    def test_changePendingApprovalToReject__whenProductActived(self):
        self._setup_data('active', 'pending_approval', 'pending_approval')
        update_sellable_editing_status(ids=[self.sellable.id], status='reject', updated_by=fake.text())
        self.assert_status('active', 'reject', 'reject')

    def test_changePendingApprovalToReject__whenVariantActived(self):
        self._setup_data('active', 'active', 'pending_approval')
        update_sellable_editing_status(ids=[self.sellable.id], status='reject', updated_by=fake.text())
        self.assert_status('active', 'active', 'reject')

    def test_changeActiveToInactive__whenSellableActived(self):
        self._setup_data('active', 'active', 'active')
        update_sellable_editing_status(ids=[self.sellable.id], status='inactive', updated_by=fake.text())
        self.assert_status('active', 'active', 'inactive')

    def test_changeActiveToInactive__whenSellablePendingApproval(self):
        self._setup_data('active', 'pending_approval', 'pending_approval')
        update_sellable_editing_status(ids=[self.sellable.id], status='inactive', updated_by=fake.text())
        self.assert_status('active', 'inactive', 'inactive')

    def test_changeActiveToSuspend__whenSellableActive(self):
        self._setup_data('active', 'active', 'active')
        update_sellable_editing_status(ids=[self.sellable.id], status='suspend', updated_by=fake.text())
        self.assert_status('active', 'active', 'suspend')

    def test_changePendingApprovalToSuspend__whenSellableActive(self):
        self._setup_data('active', 'active', 'pending_approval')
        update_sellable_editing_status(ids=[self.sellable.id], status='suspend', updated_by=fake.text())
        self.assert_status('active', 'active', 'suspend')

    def test_changeProcessingToSuspend__whenSellableActive(self):
        self._setup_data('active', 'active', 'processing')
        update_sellable_editing_status(ids=[self.sellable.id], status='suspend', updated_by=fake.text())
        self.assert_status('active', 'active', 'suspend')

    def test_changeRejectToSuspend__whenSellableActive(self):
        self._setup_data('active', 'active', 'reject')
        update_sellable_editing_status(ids=[self.sellable.id], status='suspend', updated_by=fake.text())
        self.assert_status('active', 'active', 'suspend')

    def test_changeInactiveToSuspend__whenSellableActive(self):
        self._setup_data('active', 'active', 'inactive')
        update_sellable_editing_status(ids=[self.sellable.id], status='suspend', updated_by=fake.text())
        self.assert_status('active', 'active', 'suspend')

    def test_changeSuspendToActive__whenSellableActive(self):
        self._setup_data('active', 'active', 'suspend')
        update_sellable_editing_status(ids=[self.sellable.id], status='active', updated_by=fake.text())
        self.assert_status('active', 'active', 'active')

    def test_changeSuspendToProcessing__whenSellableActive(self):
        self._setup_data('active', 'active', 'suspend')
        update_sellable_editing_status(ids=[self.sellable.id], status='processing', updated_by=fake.text())
        self.assert_status('active', 'active', 'processing')

    def test_changeSuspendToReject__whenSellableActive(self):
        self._setup_data('active', 'active', 'suspend')
        update_sellable_editing_status(ids=[self.sellable.id], status='reject', updated_by=fake.text())
        self.assert_status('active', 'active', 'reject')

    def test_changeSuspendToInactive__whenSellableActive(self):
        self._setup_data('active', 'active', 'suspend')
        update_sellable_editing_status(ids=[self.sellable.id], status='inactive', updated_by=fake.text())
        self.assert_status('active', 'active', 'inactive')

    def test_changeSuspendToPendingApproval__whenSellableActive(self):
        self._setup_data('active', 'active', 'suspend')
        update_sellable_editing_status(ids=[self.sellable.id], status='pending_approval', updated_by=fake.text())
        self.assert_status('active', 'active', 'pending_approval')
