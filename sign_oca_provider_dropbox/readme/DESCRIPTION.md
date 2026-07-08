This module connects `sign_oca` with Dropbox Sign.

It implements the provider interface supplied by
`sign_oca_provider_base`.

The module supports API key authentication, test mode, non-embedded
signature request creation, multiple signers, sequential signing,
expiration, decline, optional eID flag, polling, callback processing
with HMAC verification, per-signer synchronization, cancellation and
final signed PDF download.

A callback is treated as an authenticated notification trigger. After
verification, the addon refreshes the canonical signature request state
from the Dropbox Sign API.

The legal effect of a Dropbox Sign workflow depends on the subscribed
product, identity verification method, signing mode and applicable
legislation.
