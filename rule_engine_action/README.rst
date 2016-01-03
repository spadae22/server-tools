.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Action Rules using Rule Engine
==============================

Use a more powerful rule engine to decide triggering Action Rules.

The triggered Server Actions can make use of values computed by the
rule engine and stored in a work memory, and can be performed
using an alternative user, allowing to implement bots.


Configuration
=============

This module depends and automatically installs the Automated Action Rules
and Rule Engine addon modules.


Usage
=====

Action Rules are created at: Settings > Technical > Automation

The additional "Rules" field indicates the Rules form the rule engine
to apply to the Action Rule.

These Rules are computed and the actions will be triggered if the
rule engine evalution ends with a truthy value. If any of the Rules
fail, the actions won't be triggered.

The Rule Engine keeps a work memory during it's computations.
If triggered, the Server Actions are able to access this memory
using a ``var()`` with the memory key to get, usually a Rule code.

Triggered Server Actions can be executed using a specific User.
This can be used to implement Bots.performing actions when certain conditions
are met.
This is achieved by assigning a User to the Rule Set of the Rules.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/149/8.0


Known issues / Roadmap
======================

None.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/server-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/server-tools/issues/new?body=module:%20base_rule_agent%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Daniel Reis


Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
