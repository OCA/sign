Create a Dropbox Sign API key and store it in an Odoo system parameter.

For example:

    Key:   dropbox_sign.api_key
    Value: <your Dropbox Sign API key>

Then:

1.  Create a signature provider.
2.  Set **Provider Type** to **Dropbox Sign**.
3.  Set **Credential Reference** to `dropbox_sign.api_key`.
4.  Enable **Test mode** while developing.
5.  Optionally configure API App Client ID, sequential signing, decline,
    expiration, eID, subject and message.
6.  Click **Check configuration**.

## Test mode

Development requests use the request-level Dropbox Sign test mode
option. Test mode requests must not be used as production signature
transactions.

## Callback

Configure the callback URL displayed on the provider as the appropriate
Dropbox Sign account or API App callback URL.

The callback must be publicly reachable. The addon verifies `event_hash`
before processing the notification.
