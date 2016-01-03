# -*- coding: utf-8 -*-
##############################################################################
#
#    (c) Daniel Reis 2014 - 2015
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

import logging
from openerp import models, fields, api
from openerp import SUPERUSER_ID
from openerp import exceptions
from openerp.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class ActionRule(models.Model):
    _inherit = 'base.action.rule'
    ruleset_id = fields.Many2one(
        'rule.set', 'Rule Set')
    rule_ids = fields.Many2many(
        'rule.rule',
        'base_action_rule_rule_rel',
        domain="[('model_id', 'in', (model_id, False)),"
               " ('ruleset_id', '=', ruleset_id),"
               " ('type', '!=', 'state'))]",
        string='Rules')

    @api.model
    def _process(self, actions, record_ids, old_recs=None):
        """
        New API wrapper around the _process() upstream method.
        Implements evaluation of the Rules engine, user impersonation,
        and makes the Rule memory accessible from the Server Actions
        to be executed, through a ``var()`` funtion in the Context.
        """
        model = self.env[action[0].model_id.model]
        new_recs = model.browse(record_ids)
        # Handle case where record_ids is empty
        for new_rec in new_recs:
            memory = dict()  # memory is shared between all the eval'd Actions
            old_rec = old_recs and old_recs.get(new_rec.id)
            for action in actions.filtered('active'):
                result, memory = action.compute(new_rec, memory, old_rec)
                if result:
                    _logger.debug(
                        'Action Rule triggered: %s on record %s.',
                        action.name, repr(new_rec))
                    # Fixed: Add folllowers before assigning a responsible User
                    # Otherwise followers won't be notified upon Assignment
                    if action.act_followers:
                        if hasattr(model, 'message_subscribe'):
                            new_rec.message_subscribe(action.act_followers)
                    # Change the user running the action, if told so
                    if action.ruleset_id.runas_user_id:
                        action = action.sudo(action.ruleset_id.runas_user_id)
                    # Add var() to eval context, to allow access to the memory
                    action = action.with_context(var=lambda x: memory.get(x))
                    if not action.ruleset_id.silence_errors:
                        super(ActionRule, self)._process(action, [new_rec.id])
                    else:
                        # Error are silenced and reported to the server log
                        try:
                            super(ActionRule, self)._process(action,
                                                             [new_rec.id])
                        except exceptions.Warning as e:
                            # TODO: check Warning is diplayed correctly
                            raise exceptions.Warning(e)
                        except Exception as e:  # Don't propagate to the user!
                            _logger.error(e)
        return True

    # ~~~~~~~~~~
    # Copy of the original method from base_action_rule,
    # with only a few additions.
    # Changes made are between ``>>>>`` and ``<<<<`` blocks.
    # ~~~~~~~~~~
    def _register_hook(self, cr, ids=None):
        #
        # Note: the patched methods create and write must be defined inside
        # another function, otherwise their closure may be wrong. For instance,
        # the function create refers to the outer variable 'create', which you
        # expect to be bound to create itself. But that expectation is wrong if
        # create is defined inside a loop; in that case, the variable 'create'
        # is bound to the last function defined by the loop.
        #

        def make_create():
            """ instanciate a create method that processes action rules """
            def create(self, cr, uid, vals, context=None, **kwargs):
                # avoid loops or cascading actions
                if context and context.get('action'):
                    return create.origin(self, cr, uid, vals, context=context)

                # call original method with a modified context
                context = dict(context or {}, action=True)
                new_id = create.origin(
                    self, cr, uid, vals, context=context, **kwargs)

                # as it is a new record, we do not consider
                # the actions that have a prefilter
                action_model = self.pool.get('base.action.rule')
                action_dom = [
                    ('model', '=', self._name),
                    ('kind', 'in', ['on_create', 'on_create_or_write'])]
                action_ids = action_model.search(
                    cr, uid, action_dom, context=context)

                # check postconditions, and execute actions
                # on the records that satisfy them
                actions = action_model.browse(cr, uid, action_ids,
                                              context=context)
                for action in actions:
                    if action_model._filter(cr, uid, action, action.filter_id,
                                            [new_id], context=context):
                        action_model._process(cr, uid, action, [new_id],
                                              context=context)
                return new_id

            return create

        def make_write():
            """ instanciate a write method that processes action rules """
            def write(self, cr, uid, ids, vals, context=None, **kwargs):
                # avoid loops or cascading actions
                if context and context.get('action'):
                    return write.origin(
                        self, cr, uid, ids, vals, context=context)

                # modify context
                context = dict(context or {}, action=True)
                ids = [ids] if isinstance(ids, (int, long, str)) else ids

                action_model = self.pool.get('base.action.rule')
                action_dom = [
                    ('model', '=', self._name),
                    ('kind', 'in', ['on_write', 'on_create_or_write'])]
                action_ids = action_model.search(
                    cr, uid, action_dom, context=context)
                actions = action_model.browse(
                    cr, uid, action_ids, context=context)

                # check preconditions
                pre_ids = {}
                for action in actions:
                    pre_ids[action] = action_model._filter(
                        cr, uid, action,
                        action.filter_pre_id,
                        ids,
                        context=context)

                # >>>> Old values
                old_recs = {x.id: x
                            for x in self.browse(cr, uid, ids, context=context)}
                # <<<< Old values

                # retrieve the action rules to possibly execute
                # call original method
                write.origin(self, cr, uid, ids, vals,
                             context=context, **kwargs)

                # check postconditions, and execute actions on the records
                # that satisfy them
                # >>>> Changed: all actions should be eval'd for each record
                all_ids = set()
                for action in actions:
                    result = action_model._filter(
                        cr, uid, action,
                        action.filter_pre_id,
                        pre_ids[action],
                        context=context)
                    post_ids[action] = result
                    all_ids |= result
                for rec_id in all_ids:
                    action_model._process(
                        cr, uid, actions,
                        [rec_id], old_recs,
                        context=context)
                # <<<<
                return True

            return write

        updated = False
        if ids is None:
            ids = self.search(cr, SUPERUSER_ID, [])
        for action_rule in self.browse(cr, SUPERUSER_ID, ids):
            model = action_rule.model_id.model
            model_obj = self.pool.get(model)
            if model_obj and not hasattr(model_obj, 'base_action_ruled'):
                # monkey-patch methods create and write
                model_obj._patch_method('create', make_create())
                model_obj._patch_method('write', make_write())
                model_obj.base_action_ruled = True
                updated = True

        return updated
