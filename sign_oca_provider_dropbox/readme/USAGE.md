To send a signature request through Dropbox Sign:

1.  Create a `sign.oca.request`.
2.  Add the required signers.
3.  Ensure every signer has an email address.
4.  Select the Dropbox Sign provider.
5.  Click **Prepare provider**.
6.  Click **Start provider**.

## Signer synchronization

The addon maps Dropbox Sign signature entries back to OCA signers by
normalized email address.

The integration updates provider signer reference, provider signer
state, status update date, native OCA `signed_on` date and identity
metadata when available.

## Callbacks and refresh

The transaction can be updated by callback, manual refresh or scheduled
refresh.

The callback signature is verified before processing and then used as a
trigger for an authenticated API refresh.

## Artifacts

When the signature request is complete, the addon downloads the final
merged PDF.

The provider can temporarily report completion before the final
downloadable files are ready. The base scheduled action can retry
artifact download later.

The evidence ZIP contains the canonical Dropbox Sign signature request
status JSON.
