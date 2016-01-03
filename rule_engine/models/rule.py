# -*- coding: utf-8 -*-
##############################################################################
#
#    (c) Daniel Reis 2015
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from openerp import exceptions
from openerp.tools.safe_eval import safe_eval


class RuleEngine(models.Model):
    "Rule Engine"
    _name = 'rule.rule'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=100, index=True)
    model_id = fields.Many2one('ir.model', 'Model')
    ruleset_id = fields.Many2one('rule.set', 'Rule Set')
    state_from_ids = fields.Many2many(
        'rule.condition',
        'rule_from_rel',
        domain="[('model_id', 'in', (model_id, False)),"
               " ('type', '=', 'state')]",
        string='States From')
    state_to_ids = fields.Many2many(
        'rule.condition',
        'rule_to_rel',
        domain="[('model_id', 'in', (model_id, False)),"
               " ('type', '=', 'state')]",
        string='States To')
    condition_ids = fields.Many2many(
        'rule.condition',
        'rule_condition_rel',
        domain="[('model_id', 'in', (model_id, False)),"
               " ('type', '!=', 'state')]",
        string='Transition Conditions')
    note = fields.Text('Description')

    @api.multi
    def compute(self, record=None, memory=None, old_rec=None):
        """
        Rule engine used to process the rules.
        Rules dependended on will be previously processed.

        Args:
            self: the Rules to process
            record: the record the rules will act on
            memory: a dictionary with the already computed rules
            old_rec: record before changes, when in a write operation

        Returns:
            the memory dictionary, updated with the computed rules
        """
        is_enabled = lambda a: (
                a.active and (not a.recordset_id or a.recordset_id.enabled))
        result, memory = True, memory or {}
        memory_old = dict(memory)
        for rule in self.filtered(is_enabled):
            if rule.state_from_ids:
                result, memory_old = rule.state_from_ids.compute(
                        old_rec, memory_old, new_rec=record)
                if not result:
                    break
            if rule.state_to_ids:
                result, memory = rule.state_to_ids.compute(
                        record, memory, old_rec=old_rec)
                if not result:
                    break
            if rule.condition_ids:
                if rule.state_from_id and not rule.state_to_ids:
                    rec = old_rec
                else:
                    rec = record
                result, memory = rule.condition_ids.compute(
                        rec, memory, record, old_rec)
                if not result:
                    break
        return result, memory

    @api.model
    def compute_code(self, code, record=None, memory=None, old_rec=None):
        rule = self.search([('code', '=', code)])
        rule.ensure_one()
        return rule.compute(record, memory, old_rec)
