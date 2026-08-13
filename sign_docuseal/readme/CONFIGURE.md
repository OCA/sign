Go to *Settings > DocuSeal* and fill in the three parameters. They are stored
in `ir.config_parameter` and never shipped in source.

| Setting | Parameter | Value |
|---|---|---|
| DocuSeal URL | `docuseal.base_url` | The instance root, no trailing slash, e.g. `https://sign.example.com` |
| API Key | `docuseal.api_key` | An API token from *DocuSeal > Settings > API*. Sent as `X-Auth-Token`. |
| Webhook Secret | `docuseal.webhook_secret` | A random string you generate. Compared in constant time on every inbound call. |

Generate a webhook secret with something like:

```
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Webhook on the DocuSeal side

In *DocuSeal > Settings > Webhooks*, add an endpoint pointing at your Odoo:

```
https://odoo.example.com/docuseal/webhook
```

and add the request header:

```
X-Odoo-Webhook-Secret: <the secret you generated>
```

Subscribe at least to `submission.completed`, `form.completed`,
`form.viewed`, `form.declined` and `submission.expired`.

A second route, `POST /docuseal/webhook/<secret>`, accepts the secret in the
URL instead. It exists for instances already configured that way and works
identically, but **prefer the header**: a secret in a URL is written to
web-server logs, proxy logs and referrer headers.

Calls with a missing or wrong secret are answered `403` and logged as a
warning. If the secret parameter is empty, every call is rejected — the
module never falls back to accepting unauthenticated events.

### Reconciliation cron

*DocuSeal: reconcile pending submissions* runs hourly and re-reads any
submission that has been pending for more than an hour. It is the safety net
for a webhook that never arrived; leave it enabled.
