##############################################################################
#
#    Copyright (C) 2015 Daniel Reis
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


from openerp import models, api
from openerp.modules.registry import RegistryManager


class Users(models.Model):
    _inherit = 'res.users'

    @api.v7
    def _login(self, db, login, password):
        user_id = super(Users, self)._login(db, login, password)
        if not user_id and '@' in login:
            registry = RegistryManager.get(db)
            with registry.cursor() as cr:
                cr.execute("SELECT login FROM res_users u "
                           "INNER JOIN res_partner p ON u.partner_id = p.id "
                           "WHERE u.active=true and lower(p.email)=%s "
                           "ORDER BY u.id DESC", (login,))
                email_login = cr.fetchone()
            if email_login:
                user_id = super(Users, self)._login(db, email_login, password)
        return user_id
