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


class Condition(models.Model):
    _name = 'rule.condition'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=100, index=True)
    model_id = fields.Many2one('ir.model', 'Model')
    code = fields.Char(
        'Code',
        index=True,
        help="The result from this rule evaluation will be stored"
             " in this and available to other Facts.")
    parent_ids = fields.Many2many(
        'rule.condition',
        'rule_condition_parent_rel',
        'condition_id',
        'parent_id',
        domain="[('model_id', 'in', (model_id, False))]",
        string='Parent Conditions')
    condition_expr = fields.Text(
        'Expression to Evaluate',)
    note = fields.Text('Description')
    condition_type = fields.Selection(
        [('state', 'State'), ('input', 'Condition')],
        string='Type',
        default='input')

    @api.model
    def get_eval_context(self, rec=None, eval_dict=None,
                         new_rec=None, old_rec=None):
        "Return an Evaluation context dict"
        self.ensure_one()
        writing = bool(old_rec)
        creating = not writing
        if not eval_dict:
            eval_dict = dict()
        rec = rec or self.model_id or self
        new = new_rec or rec
        old = old_rec or rec
        chg = lambda f: getattr(old, f, None) != getattr(new, f, None)
        changed = lambda *ff: any(chg(f) for f in ff)
        changed_to = lambda f: chg(f) and getattr(new, f)
        rule = lambda c, d=None: eval_dict.get(c, d)
        res = dict(BASE_EVAL_CTX)
        if eval_dict:
            res.update(eval_dict)
        res.update({
            'self': rec,  # allows object.notation
            'obj': rec,
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
    def compute(self, record=None, memory=None, new_rec=None, old_rec=None):
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
        result, memory = None, memory or {}
        for cond in self:
            # Do not reevaluate facts
            if cond in memory or not cond.active:
                pass
            # Compute parent conditions
            result, memory = cond.parent_ids.compute(
                record, memory, new_rec, old_rec)
            if not result:
                break  # don't eval expr and don't store result
            # Evaluate condition expression
            if condition_expr:
                eval_ctx = cond.get_eval_context(record, memory,
                                                 new_rec, old_rec)
                result = safe_eval(cond.condition_expr, eval_ctx)
            # Store results in the working memory
            memory[cond] = result
            if cond.code:
                memory[cond.code] = result
        return result, memory

    @api.multi
    @api.constrains('rule_expr')
    def _check_rule_expr(self):
        try:
            rule.compute_rules()
        except:
            raise exceptions.ValidationError(
                '%s: Invalid evaluated expression «%s»'
                % (rule.name, rule.rule_expr))
