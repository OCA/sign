1.  Go to Sign > Settings > Roles and create a role with the following data:

- Partner type: Expression
- Expression: {{object.partner_id.id}}

2.  Go to Sign > Templates and create a template with the following data:

- Model: Project Task
- In one of the fields, you must set the previously created role.

3.  (Optional) Go to Project > Configuration > Settings.

- In the Task Sign section, define a template to enable automatic task sign requests.
- Use the template previously created.
