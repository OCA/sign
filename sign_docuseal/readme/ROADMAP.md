- There is no UI to create a submission: another module has to call
  `create_and_send()` or `create_from_html()`. A generic "send this attachment
  for signature" wizard would make the module usable on its own.
- DocuSeal templates are referenced by their numeric id, kept as a plain
  `Char`. There is no synchronisation of the template catalogue into Odoo, so
  the id has to be looked up in DocuSeal and configured by hand.
- Only the first document of a completed submission is stored. DocuSeal is
  asked to merge (`merge=true`), so a multi-document submission arrives as one
  PDF; submissions that genuinely carry several distinct files keep only the
  first.
- The webhook trusts the shared secret only. DocuSeal can also sign its
  payloads; verifying that signature would be stronger than a shared secret
  and is not implemented.
- Sending is synchronous: the API call happens in the transaction of whoever
  triggered it. A slow DocuSeal instance is felt by the user. Moving the call
  to `queue_job` would decouple the two.
- `create_submission_from_html()` and `create_template_from_pdf()` need a paid
  DocuSeal plan and fail with a plain error message on a community instance.
