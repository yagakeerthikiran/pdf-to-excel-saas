## Next.js: Use a single `app/` directory

We previously had both `app/` and `src/app/`. Next.js will use **one**:
- If `app/` exists at project root, that wins.
- `src/app/` is only used if root `app/` is absent.

This caused routes under `src/app/` to be ignored in production.

**Fix**: Move everything from `frontend/src/app/**` into `frontend/app/**`, then delete `src/app`:

```powershell
pwsh -File scripts/move-src-app-to-app.ps1 -FrontendRoot frontend
