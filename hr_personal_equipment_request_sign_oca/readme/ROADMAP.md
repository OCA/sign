If the Employee in the Personal Equipment Request is not linked to a User, when generating the Sign Request the following is raised:
> ERROR:  null value in column "partner_id" of relation "sign_oca_request_signer" violates not-null constraint

because the Sign Role created in module's data assumes a User is linked to the Employee.
The problem is that an Employee may not be linked to a User or even a Partner.
Moreover, the Sign Role's Expression can be customized so that no exception is raised: added a new configuration instruction to warn the user.
