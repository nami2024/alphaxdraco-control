# AlphaXDraco Control

This repository is the signed remote control plane for AlphaXDraco V3.

- `manifest.json` is fetched by the bot.
- License keys are never stored here. Only domain-separated SHA-256 hashes are stored.
- The manifest is signed by GitHub Actions. The private RSA key is held in the repository secret `LICENSE_SIGNING_KEY_PEM`.
- A valid signed manifest can change the bot's OpenRouter model, activate/revoke licenses, bind a license to one device, and set an expiry.

## Add a license

1. Open the [License Tool](https://nami2024.github.io/alphaxdraco-control/).
2. Generate a key. Save the plaintext key and give it to the customer.
3. Ask the customer for the device code printed by AlphaXDraco if device binding is wanted.
4. Open **Actions → Manage license and model → Run workflow**.
5. Select `add`, paste the license SHA-256, optional device code, expiry, and label.

## Revoke or reactivate

Run the same workflow with `revoke` or `activate` and the license SHA-256.

## Change model

Run the workflow with action `model` and a valid OpenRouter model ID such as `z-ai/glm-5.2`.

The bot checks the signed manifest before login and refreshes it between signal scans. If GitHub is temporarily unreachable, the last valid signed manifest is accepted for the configured offline grace period.
