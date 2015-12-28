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
    _name = 'base.rule.rule'

    name = fields.Char(required=True)
    active =Boolean(default=True)
    sequence = fields.Integer(default=100, index=True)
    model_id = fields.Many2one('ir.model', 'Model')
    ruleset_id = fields.Many2one('base.rule.set', 'Rule Set')
    code = fields.Char(
        'Code',
        index=True,
        help="The result from this rule evaluation will be stored"
             " in this and available to other Facts.")
    rule_ids = fields.Many2many(
        'base.rule.rule',
        domain="[('model_id', 'in', (model_id, False))]",
        string='Rules')
    rule_expr = fields.Text(
        'Expression to Evaluate',
        help='Python expression, able to use a "new" and "old"')
    note = fields.Text('Description')
    #fact_type = fields.Selection(
    #    [('state', 'State'), ('cond', 'Condition')],
    #    string='Type',
    #    default='cond')

    @api.model
    def get_eval_context(self, new_rec=None, eval_dict=None, old_rec=None):
        "Return an Evaluation context dict"
        self.ensure_one()
        new_rec = new_rec or self.model_id or self
        writing = bool(old_rec)
        creating = not writing
        old = lambda f, d=None: getattr(old_rec, f, d)
        new = lambda f, d=None: getattr(new_rec, f, d)
        chg = lambda f: old(f) != new(f)
        changed = lambda *ff: any(chg(f) for f in ff)
        changed_to = lambda f: chg(f) and new(f)
        rule = lambda c, d=None: eval_dict.get(c, d)
        res = dict(BASE_EVAL_CTX)
        if eval_dict:
            res.update(eval_dict)
        res.update({
            'self': new_rec,  # allows object.notation
            'obj': new_rec,
            'env': self.env,
            'context': self.env.context,
            'user': self.env.user,
            'rule': rule,
            'old': old,
            'new': new,
            'changed': changed,
            'changed_to': changed_to,
            'creating': creating,
            'inserting': creating,
            'writing': writing,
            'updating': writing})
        return res

    @api.multi
    def get_eval_contexts(self, new_recs, eval_dict=None, old_recs=None):
        "Get list of eval contexts for the record_ids"
        self.ensure_one()
        if not old_recs:
            old_recs = dict()
        res = [self.get_eval_context(x, eval_dict, old_recs.get(x.id))
               for x in new_recs]
        return res

    @api.multi
    def compute_rules(self, record=None, memory=None, old_rec=None):
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
        memory = memory or {}
        is_enabled = lambda a: (
                a.active and (not a.recordset_id or a.recordset_id.enabled))
        for rule in rules:
            # Do not reevaluate facts
            if rule in memory or not is_enabled(rule):
                pass
            memory = rule.rule_ids.compute_rules(record, memory, old_rec)
            if not rule_expr:
                pass
            eval_ctx = rule.get_eval_context(record, memory, old_rec)
            result = safe_eval(rule.rule_expr, eval_ctx)
            memory[rule] = result
            if rule.code:
                memory[rule.code] = result
        return memory

    @api.multi
    @api.constrains('rule_expr')
    def _check_rule_expr(self):
        try:
            rule.compute_rules()
        except:
            raise exceptions.ValidationError(
                '%s: Invalid evaluated expression «%s»'
                % (rule.name, rule.rule_expr))
