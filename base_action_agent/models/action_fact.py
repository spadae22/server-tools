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

from datetime import datetime, timedelta
import dateutil
from openerp import models, fields, api, exceptions
from openerp.tools.safe_eval import safe_eval


BASE_EVAL_CTX = {
    'dateutil': dateutil,
    'datetime': datetime,
    'timedelta': timedelta,
    'Date': fields.Date,
    'Datetime': fields.Datetime
}


class ActionFact(models.Model):
    _name = 'base.action.fact'
    _order = 'sequence'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=100, index=True)
    model_id = fields.Many2one('ir.model', 'Model')
    fact_type = fields.Selection(
        [('state', 'State'), ('cond', 'Condition')],
        string='Type',
        default='cond')
    fact_code = fields.Char(
        'Assigns Variable',
        index=True,
        help="The result from this fact evaluation will be stored"
             " in this and available to other Facts.")
    parent_id = fields.Many2one(
        'base.action.fact',
        'Requires')
    negate_parent = fields.Boolean(
        'Negate Condition',
        help="True when the parent condition is False")
    filter_expr = fields.Text(
        'Expression to Evaluate',
        help='Python expression, able to use a "new" and "old"')
    calc_expr = fields.Char(
        'Computed Expression',
        readonly=True,
        compute='_compute_filter_expr')
    note = fields.Text('Description')
    # TODO usage count

    @api.model
    def get_one_eval_context(self, new_rec=None, operation=None,
                             vals=None, old_row=None):
        "Return an Evaluation context dict"
        if not old_row:
            old_row = {}
        creating = operation == 'create'
        writing = operation == 'write'
        old_row = old_row or {}
        if new_rec is None and self.model_id:
            new_rec = self.env[self.model_id.model]
        old = lambda f, d=None: old_row.get(f, d)
        new = lambda f, d=None: getattr(new_rec, f, d)
        chg = lambda f: repr(old(f)) != repr(new(f))
        changed = lambda *ff: any(chg(f) for f in ff)
        changed_to = lambda f: chg(f) and new(f)
        res = dict(BASE_EVAL_CTX)
        res.update({
            'self': new_rec,  # allows object.notation
            'obj': new_rec,
            'env': self.env,
            'context': self.env.context,
            'user': self.env.user,
            'old': old,
            'new': new,
            'vals': vals or dict(),
            'changed': changed,
            'changed_to': changed_to,
            'creating': creating,
            'inserting': creating,
            'writing': writing,
            'updating': writing})
        return res

    @api.multi
    def eval_facts(self, eval_ctx, fact_cache=None, var_memory=None):
        "Returns a dict mapping Facts with  results, plus the final memory"
        fact_cache = fact_cache or dict()
        for fact in self:
            # Do not reevaluate facts
            if fact in fact_cache:
                pass
            # Make sure required parent fact is evaluated
            if fact.parent_id and fact.parent_id not in fact_cache:
                fact_cache, var_memory = fact.parent_id.eval_facts(
                    eval_ctx, fact_cache, var_memory)
            # Evaluate trigger expression
            # Don't use the "Run As" User when evaluating these filters
            # since we want to be able to query the User running the action
            eval_ctx['vars'] = var_memory or dict()
            eval_result = safe_eval(fact.calc_expr, eval_ctx)
            fact_cache[fact] = eval_result
            if fact.fact_code and eval_result:
                var_memory[fact.fact_code] = eval_result
        return fact_cache, var_memory

    @api.multi
    @api.constrains('filter_expr')
    def _check_filter_expr(self):
        eval_ctx = self.get_one_eval_context()
        for fact in self.filtered('filter_expr'):
            try:
                safe_eval(fact.filter_expr, {}, eval_ctx)
            except:
                raise exceptions.ValidationError(
                    '%s: Invalid evaluated expression «%s»'
                    % (fact.name, fact.filter_expr))

    @api.model
    def calc_join_exprs(self, exprs):
        "Return expression that results from joining the Facts"
        particles = ['(%s)' % e for e in exprs if e]
        return ' and '.join(particles)

    @api.multi
    @api.depends('parent_id', 'parent_id.filter_expr')
    def _compute_filter_expr(self):
        "Compute Python expression to evaluate from list of facts"
        for fact in self:
            if not fact.negate_parent:
                this_expr = expr and fact.filter_expr.repalce('\n', ' ') or ''
                parent_expr = fact.parent_id.calc_expr
                fact.calc_expr = self.calc_join_exprs([parent_expr, this_expr])
            elif fact.parent_id.calc_expr:
                fact.calc_expr = 'not ' + fact.parent_id.calc_expr
            else:
                fact.calc_expr = ''

    @api.multi
    def rule_engine(self, rules, operation, record,
                    vals=None, old_vals=None):
        """
        Filter a single Action for a list of record_ids
        It is expected to be called alongside _filter() and not inside it.
        Works for one Record at a time.

        Evaluates rules to find the ones to be triggered:
        a) Inactive or disabled Rules are ignored
        b) Check "From State", using old values
        c) Check "To State", using new values
        d) Check fact "Conditions" using new values
        Returns ?...
        """
        # Don't trigger disabled Action rules and Rulesets
        is_enabled = lambda r: (r.active and
                                (not r.parent_id or r.parent_id.enabled))
        rules = self.filtered(is_enabled)
        # Rules passing the post filter
        rules = rules.filtered(
            lambda r: (r.filter_id and r._filter(r.filter_id, [record.id])))

        # Fact pre-conditions
        facts_from = rules.mapped('from_fact_id')
        if facts_from:
            old_ctx = dict(BASE_EVAL_CTX)
            old_ctx['self'] = old_vals.get('self') #TODO
            fact_cache, _ = facts_from.eval_facts(old_ctx)
            rules.filtered(lambda r: fact_cache.get(r.from_fact_id))

        # Rules with facts
        rules = rules.filtered(lambda r:
            r.fact_ids or r.from_fact_id, or r.to_fact_id)
        # Evaluated rule facts to a fact cache
        if fact_rules:
            eval_ctx = self.fact_ids.get_one_eval_context(
                record, operation, vals, old_vals or dict())
            fact_cache = {}
            var_memory = {}
            for rule in fact_rules:
                fact_cache, var_memory = rule.fact_ids.eval_facts(
                    eval_ctx, fact_cache, var_memory)
            # Filter out rules with falsy values
            rules.filtered(lambda r: fact_cache.get(r, True))

        # Process the rules that were triggered
        if not simulate:
            for rule in rules:
                rules._process([record.id])
        return True
