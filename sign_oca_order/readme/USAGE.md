**Sequential Signing:**

1. Create a new sign request
2. Set Signing Mode to "Sequential"
3. Add signers and set their Signing Order (1, 2, 3...)
4. Send the request -- only order 1 signers are notified
5. After order 1 completes, order 2 signers are automatically notified
6. Repeat until all steps complete

**CC Recipients:**

1. Add partners to the CC Recipients field on the sign request
2. After all signers complete, CC recipients receive an email with the signed PDF attached

**Parallel Groups:**

Signers with the same signing order number sign simultaneously. For example:

- Order 1: Alice, Bob (both sign in parallel)
- Order 2: Carol (signs after Alice AND Bob complete)
