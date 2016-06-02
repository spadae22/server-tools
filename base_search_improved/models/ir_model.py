# -*- coding: utf-8 -*-
# © 2016 Daniel Reis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from openerp import SUPERUSER_ID


class ModelExtended(models.Model):
    _inherit = 'ir.model'

    def _register_hook(self, cr, ids=None):

        def make_search():

            prefixes = ['=', '<', '>', '!']
            infixes = ['..']

            def can_expand(val, prefixes, infixes):
                return (any(str(val).startswith(x) for x in prefixes) or
                        any(x in str(val) for x in infixes))

            @api.model
            def search(self, args=None, offset=0, limit=None, order=None,
                    count=False):
                # Regular name search
                res = search.origin(
                    self, args=args, offset=offset,
                    limit=limit, order=order, count=count)
                if res:
                    return res

                def expand_element(elem, op):
                    if (len(elem) == 3 and
                            op in ['ilike', 'like', '='] and
                            can_expand(elem[2])):
                        pass
                        return [(elem[0], elem[2][:1], elem[2][1:])]
                    else:
                        return [e]

                if not res and self._rec_name:
                    # Support a list of fields to search on
                    model = self.env['ir.model'].search(
                        [('model', '=', str(self._model))])
                    other_names = model.name_search_ids.mapped('name')
                    # Try regular search on each additional search field
                    for rec_name in other_names:
                        domain = [(rec_name, operator, name)]
                        recs = self.search(domain, limit=limit)
                        if recs:
                            return recs.name_get()
                    # Try ordered word search on each of the search fields
                    for rec_name in self._rec_name + other_names:
                        domain = [(rec_name, operator, name.replace(' ', '%'))]
                        recs = self.search(domain, limit=limit)
                        if recs:
                            return recs.name_get()
                    # Try unordered word search on each of the search fields
                    for rec_name in self._rec_name + other_names:
                        domain = [(rec_name, operator, x)
                                  for x in name.split() if x]
                        recs = self.search(domain, limit=limit)
                        if recs:
                            return recs.name_get()
                return res
            return name_search

        if ids is None:
            ids = self.search(cr, SUPERUSER_ID, [])
        for model in self.browse(cr, SUPERUSER_ID, ids):
            Model = self.pool.get(model.model)
            if Model:
                Model._patch_method('search', make_search())
        return super(ModelExtended, self)._register_hook(cr)
