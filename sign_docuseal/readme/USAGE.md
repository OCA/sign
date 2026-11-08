This module ships no business flow of its own: it is the plumbing another
module calls. Submissions are visible under *Settings > DocuSeal >
Submissions* for auditing, but they are normally created from code.

### Send a document from a DocuSeal template

```python
submission = self.env["docuseal.submission"].create_and_send(
    template_id=8,
    submitters=[
        {"role": "First Party", "name": "ACME Ltd", "email": "legal@acme.example"},
        {"role": "Second Party", "name": partner.name, "email": partner.email},
    ],
    source=self,          # any record; keeps res_model / res_id pointing back
    name="Docking contract %s" % self.name,
    send_email=False,     # True lets DocuSeal email the signers itself
    order="preserved",    # sign in the given order; "random" for parallel
)
```

`order="preserved"` means the second signer is only invited once the first has
signed. Use `"random"` when everyone may sign at once.

### Send a document rendered by Odoo

Requires a paid DocuSeal plan (see the description).

```python
html = self.env["ir.qweb"]._render("my_module.contract_template", {"doc": self})
submission = self.env["docuseal.submission"].create_from_html(
    html, submitters, source=self, name="Contract %s" % self.name,
)
```

The HTML may carry DocuSeal text tags, matched to submitters by role:

```
{{Signature;role=Second Party;type=signature}}
{{Date;role=Second Party;type=date}}
```

### Give each signer their link

`submitter.signing_url` is the Odoo page to send out. Never send
`submitter.embed_src` — that is the raw DocuSeal URL and it grants signing
rights on its own.

```python
for submitter in submission.submitter_ids:
    submitter.partner_id.message_post(body=submitter.signing_url)
```

### React to completion

Define `_on_docuseal_completed` on the source model. It is called once, after
the signed PDF and the audit trail have been attached to the submission.

```python
class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _on_docuseal_completed(self, submission):
        self.write({"state": "sale"})
        self.message_post(body=_("Contract signed on %s.") % submission.name)
```

The hook runs inside the webhook transaction. Keep it short, and let it raise
if it must: a failure answers `500` and DocuSeal retries the event.

### What lands on the record

Once every signer is done, the submission holds `signed_document` (the merged
signed PDF), `audit_log_file` and `audit_log_url` (the DocuSeal trail),
`completed_date`, and a chatter entry for each transition.
