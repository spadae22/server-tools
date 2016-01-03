.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Generic Rule Engine
===================

Provides a powerful rule engine capable to support complex workflows
or user designed computations.

It is capable to implement the features provided by the several
varaints on finite state machines (FSM), thus providing adequate support
for business workflows when used in conjuction with Automated Actions.

The rule engine was also designed to support Production Rule systems,
allowing for user managed business rules or to support Expert systems.


Summary of features provided:

  * Rule Sets organize Automated Rules in logical sets
  * Run Automated Actions using a specific user.
  * Define Rule filters composed of several combined Python snippets


Rule sets are capable to provide an alternative workflow system:

  * A Workflow is defined using a Rule Set
  * Nodes, or States, are represented by Facts
  * Signals, or transition conditions, are represented by Facts using
    changed / old vs new values
  * Transitions are represented by Action Rules


With the "Run As" feature we have basic support for Bots or Agents:

  * Create a User for the Bot. Make sure it has the necessary security permissions.
  * Create a new Ruleset and set the Bot as its User.
  * Create the Automated Action to be ran by the Bot.
  * Check the Bot's ruleset "Enabled" flag to active the Rules.

Make your OdooBot the best worker in the company!


Rule Sets
---------

Rule Sets are a logical organization for he engine Rules.
A Set could represent a business workflow,
or a particular production rule system.

Additionally User can be assigned to a Rule Set.
When used with Automated Actions, this makes the Server Actions
fired to be performed using that particular user, allowing to
implement worker Bots.

The "Silence Error?" option allows for exceptions, other than
``raise Warning()``, to be recorded in the server log without being
propagated to the end user.
This is useful for some helper Bot use cases, where we don't want
any Bot malfunction (missing security access, for example) to disturb
the end user.


Rules
-----

A Rule is a set of conditions to evaluate. If all conditions return
a truthy value, the result of the Rule computation is the result
for the last condition evaluated.
If any of the Rule conditions is falsy, the Rule will return a False
value.

The conditions are organized into three groups:

  * From State: to identify the origin State in a FSM, evaluated against
    the "old" record values, if available.
  * To State: to identify the destination State in a FSM.
  * Conditions: to identify any other non-State related conditions.
    In a FSM they identify the transition triggering conditions.


Conditions
----------

Conditions are logic expressions to be evaluated.
They can express state (ex: "Is Open") or events (ex: "Changed to Open").

These are Python expressions, and their evaluation context has available:

  * ``self``, ``obj``: is the record object, after the create/write operation
  * ``env``, ``context``, and ``user``
  * ``creating``, ``inserting``: True if triggered by a create operation
  * ``writing``, ``updating``: True if triggered by a write operation
  * ``old('<field>')``: gets the old value before the write operation
  * ``new('<field>')``: gets the new value after the create/write operation
  * ``changed('<fld1>'[,...])``: checks if the any of the fields changed value
  * ``changed_to('<field>')``: checks if the field changed and returns the new value
  * ``datetime``, ``timedelta``, ``dateutil`` modules
  * ``Date`` and ``Datetime`` references to the Odoo field classes

Values are retrieved from a ORM record browse, so dot notation is available.
``old`` and ``new`` also accept a seconf parameter with a default value to use.
These expressions are more powerful and succint than the standard domain filters.

Examples:

  * ``old('user_id').login='brian' and new('user_id').login=='eric'``: changed from brian to eric
  * ``changed('user_id') and self.user_id.login=='brian'``: responsible changed to 'brian'
  * ``changed('project_id') and not changed('user_id')``: project changed but responsible user didn't


Action Rules
------------

The Rule Engine can be made available to use with Automated Actions
by also installing the "Automated Actions using Rule Engine" module
(``rule_engine_action``).


Configuration
=============

Workflows
---------

It also intends to provide an alternative workflow system:
  * A Workflow is defined using a Rule Set
  * Nodes, or States, are represented by Facts
  * Signals, or transition conditions, are represented by Facts using
    changed / old vs new values
  * Transitions are represented by Action Rules

For example, part of a customer service workflow we want an Issue
to change to Open only after the Sales Rep. approves the new Issue.

Rules:
  * If "Is New Unapproved", "Is Not Customer Manager", "Changed to Ready"
    Then raise Warning.
  * If "Is New Approved Issue" Then set Stage to Open

Facts:
  * "Is Not Customer Manager", current User is different from
    the Issue's Customer Manager:
    ``user != self.partner_id.user_id``
  * "Changed to Ready", Kanban State changed to Ready:
    ``changed_to('kanban_state')=='ready'``
  * "New Unapproved Issue", in the New Stage with a Kanban State
    different from Ready:
    ``self.stage_id.name=='New' and self.kanban_state!='ready'``
  * "New Approved Issue", in the New Stage with a Kanban State
    equal to Ready:
    ``self.stage_id.name=='New' and self.kanban_state=='ready'``


Usage
=====

The new feature can be configured at Settings > Technical > Automation:

  * Rule Sets and Rule Facts are available in new menu options.
  * Automated Actions have new fields available.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/149/8.0


Known issues / Roadmap
======================

  * Implement the "Run As" for scheduler run actions.
  * Add optional logging / tracking for Ruleset actions.
  * Setting up workflow conditions can be tricky. How to aid the user?
  * The Bot support can be greatly expanded.
    It could be plugged to Artificial Intelligence techniques, starting with
    rule based expert systems up to machine learning techniques.
    Adding better Production Rule System would be interesting.

Also some TODO marker have been left in the source code, signaling some
very specific improvements that could be made-


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

Partly based on the 6.1 module `base_Action_rule_triggers`:
https://github.com/dreispt/odoo-addons/tree/6.1/base_action_rule_triggers


Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
