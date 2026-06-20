# AlphaXDraco Control

This repository is the remote license and model control plane for AlphaXDraco V3.

- `control.json` is fetched from this exact GitHub repository over HTTPS.
- License keys are never stored here. Only domain-separated SHA-256 hashes are stored.
- Only repository collaborators can activate/revoke licenses or change the model.
- Licenses support optional device binding and expiry.

## Add a license

1. Open the [License Tool](https://nami2024.github.io/alphaxdraco-control/).
2. Generate a key. Save the plaintext key and give it to the customer.
3. Ask the customer for the device code printed by AlphaXDraco if device binding is wanted.
4. Copy the generated JSON record.
5. [Edit `control.json`](https://github.com/nami2024/alphaxdraco-control/edit/main/control.json), add the record inside the `licenses` array, and commit.

## Revoke or reactivate

Edit the matching record in `control.json` and set `status` to `revoked` or `active`.

## Change model

Edit the top-level `model` value in `control.json` and commit. Use a valid OpenRouter model ID such as `z-ai/glm-5.2`.

The bot checks this fixed GitHub control URL before login and refreshes it between signal scans. If GitHub is temporarily unreachable, the last valid cached control file is accepted for the configured offline grace period.
