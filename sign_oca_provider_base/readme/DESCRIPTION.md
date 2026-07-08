This module provides a provider-agnostic abstraction layer to connect
`sign_oca` with external electronic signature services.

It introduces a common provider API so that each signature service can
be implemented in a separate addon without adding provider-specific code
to `sign_oca`.

The module provides:

- signature provider configuration;
- provider transaction lifecycle management;
- request and signer extensions;
- normalized provider states;
- per-signer provider state tracking;
- generic webhook entry points;
- signed document and evidence artifact handling;
- automatic refresh of pending transactions;
- automatic retry of incomplete artifact downloads;
- synchronization of signed documents and evidence with the related
  `sign.oca.request`.

A provider-specific addon is expected to implement the remote API
integration by extending the hooks defined on `sign.oca.provider`.

The module does not claim that installing or configuring a provider
automatically makes every signature process compliant with a specific
legal signature level. The effective legal assurance depends on the
selected provider, identity verification method, signing ceremony,
certificate policy, evidence retention and applicable legislation.
