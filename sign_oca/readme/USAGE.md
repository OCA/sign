## Creation of templates

- Access Sign / Templates
- Create a new template
- Add a PDF File
- Access the configuration menu
- You can add a field by doing a right click inside a page
- Click on the field in order to delete or edit some configuration of it
- The template is autosaved

## Sign role

- Access Sign / Settings / Roles
- Create a new role (Equipment employee for example)
- You can set the Partner type you need (empty, default or expression).
- With the expression option you can set: {{object.field_name.id}}
- If you create a sign request from template signer will be auto-create
  according to roles

## Sign a document from template

- Access Sign / Templates
- Press the Sign button from a template
- Fill all the possible partners that will sign the document
- You can link the template to a model (maintenance.equipment for
  example)
- The signature action will be opened.
- There, you can fill all the data you need.
- Once you finish, press the sign button on the top
- When the last signer signs it, the final file will be generated as a
  PDF

## Sign a pending document

- Go to the pencil icon in the upper right corner (systray) of the sign
  request to access the pending signatures.
- Press the Sign button from signer request
- The signature action will be opened.
- There, you can fill all the data you need.
- Once you finish, press the sign button on the top
- When the last signer signs it, the final file will be generated as a
  PDF

## Sign from template

- Go to any list view or form view (except sign.oca models), e.g.:
  Contacts
- Select multiple records (3 for example).
- The "Sign from template" action will be available if there are any
  sign templates created that are not linked to any model and/or any
  linked to the corresponding model.
- Select a template.
- Click on the "Generate" button.
- 3 requests will be created (each linked to each selected record) BUT
  no signer will be set.
- Some extra modules (e.g. maintenance_sign_oca) will automatically set
  the signers for each request.

## Sign from portal
- customers who are using portal can sign their documents from portal 
  directly in addition to being able to sign them from emails.

## Signing reports from Odoo

There is a way to automatically sign PDF reports.
In this reports we can force elements to sign by using invisible boxes with some specific texts.

``` xml
  <template
        id="report_saleorder_document"
        inherit_id="sale.report_saleorder_document"
    >
        <span name="order_note" position="before">
            <div
                class="w-50"
                style="height: 6rem;background-color: rgba(0,0,0,0.004); color: rgba(0,0,0,0.004);"
            >##SIGN_OCA##sign_oca.sign_field_signature##sign_oca.sign_role_customer</div>
        </span>
    </template>
```

From a code perspective you just need to do something like:

``` python

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def send_and_sign_action(self):
        self.ensure_one()
        pdf, _ = (
            self.env["ir.actions.report"]
            .sudo()
            ._render_qweb_pdf("sale.action_report_saleorder", self.ids)
        )
        self.env["sign.oca.request"]._process_signature(
            self,
            pdf,
            {self.sudo().env.ref("sign_oca.sign_role_customer").id: self.partner_id.id},
        )
```