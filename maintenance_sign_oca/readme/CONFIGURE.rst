#. Go to Sign > Roles and create a new one with the following data:

- Partner type: Expression
- Expression: ${object.owner_user_id.partner_id.id}

#. Go to Sign > Templates and create a template with the following data:

- Model: Maintenance Equipment
- In some of the elements you will have to set the previously created role.

#. Go to Maintenance > Configuration > General settings.
#. Defines the template previously created (optional, only for automatic creation of signature requests).
