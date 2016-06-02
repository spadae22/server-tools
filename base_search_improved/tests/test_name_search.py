# -*- coding: utf-8 -*-
# © 2016 Daniel Reis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase, at_install, post_install


@at_install(False)
@post_install(True)
class NameSearchCase(TransactionCase):

    def setUp(self):
        super(NameSearchCase, self).setUp()
        phone_field = self.env.ref('base.field_res_partner_phone')
        model_partner = self.env.ref('base.model_res_partner')
        model_partner.name_search_ids = phone_field
        self.Partner = self.env['res.partner']
        self.partner1 = self.Partner.create(
            {'name': 'Johann Gambolputty of Ulm',
             'phone': '555-555-555'})

    def test_NameSearchPhone(self):
        """Name Search on Phone field"""
        res = self.Partner.name_search('555-555-555')
        self.assertTrue(res)

    def test_NameSearchUnordered(self):
        """Name Search on unordered words"""
        res = self.Partner.name_search('ulm gambol')
        self.assertTrue(res)

    def test_NameSearchFalsePositive(self):
        """Name Search no False Positive"""
        res = self.Partner.name_search('ulm 555-555')
        self.assertFalse(res)
