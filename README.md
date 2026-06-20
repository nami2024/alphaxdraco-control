# AlphaXDraco Control

This repository is the remote license control plane for AlphaXDraco V3.

- `control.json` is fetched from this exact GitHub repository over HTTPS.
- License keys are never stored here. Only domain-separated SHA-256 hashes are stored.
- Only the repository owner can add, activate, revoke, or delete licenses through the admin panel.
- Licenses support optional device binding and expiry.

## Admin panel

Open [AlphaXDraco License Admin](https://nami2024.github.io/alphaxdraco-control/).

- Admin ID: `nami2024`
- Password: a GitHub personal access token belonging to `nami2024`, with Contents read/write access to this repository
- The token is kept in browser `sessionStorage` and is removed on logout/browser close.

The panel can generate/add, activate, revoke, and delete licenses. It does not expose model controls.

The bot checks this fixed GitHub control URL before login and refreshes it between signal scans. If GitHub is temporarily unreachable, the last valid cached control file is accepted for the configured offline grace period.

## VeloQ signed Gmail/password control

VeloQ uses an independent Ed25519-signed control under `veloq/`. User emails
are domain-separated SHA-256 hashes and passwords are salted PBKDF2-SHA256
hashes; plaintext credentials are not committed.

- Owner panel: https://nami2024.github.io/alphaxdraco-control/veloq.html
- Editable source: `veloq/control.json`
- Client-consumed signed file: `veloq/manifest.json`
- Signer: `.github/workflows/sign-veloq-control.yml`

On the owner PC, run `VELOQ_GITHUB_ADMIN.cmd` from the VeloQ project. It can
add/update Gmail and password accounts, revoke/reactivate users, and change the
OpenRouter model. Each account supports either Unlimited usage or a total
request limit. The tool signs both `control.json` and `manifest.json`, then
pushes the update through the already authenticated GitHub CLI.
