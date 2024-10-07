#. Go to Sign > Roles and create a role with the following data:

- Partner type: Expression
- Expression: ${object.partner_id.id}

#. Go to Sign > Templates and create a template with the following data:

- Model: Sale Order
- In one of the fields, you must set the previously created role.

#. Go to Sales > Configuration > Settings.

- In the Sale Order Sign section, mark the field Sale Order Sign Template, define the template that will be used to generate the sales order sign request.
- Use the template previously created.
- And choose the state in which this will happen.
