.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3


Also allow authentication with user email
=========================================

For some users the user login is not an email address.
For example, that's the case for ``admin`` and ``demo``
in the demonstration data.

Since the login form asks for an "Email" and "Password",
users can expect for the email address to wrok as well as 
the login name.

This addon makes that possible: if login auth fails, it will 
try again using the user's email.


Configuration
=============

None.

Usage
=====

At the login form, use the user's email instead of its login name.
In this case the system will also use the email address to lookup the 
user login iand then try the authentication again.


Known issues / Roadmap
======================

None.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/hr/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/hr/issues/new?body=module:%20hr_recruitment_partner%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Daniel Reis


Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
