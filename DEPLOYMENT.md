# Long-term deployment

This project is configured for GitHub Pages long-term static deployment.

## What gets deployed

- Frontend: Vue app in `frontend/`
- Build command: `npm run build:static`
- Output folder: `frontend/dist`
- Demo mode: enabled by `frontend/.env.static`

The static deployment includes sample/demo business data so the system can be opened from any computer without running the FastAPI backend. If you need the full live backend later, deploy the backend separately and build the frontend with `VITE_BACKEND_URL=https://your-backend-domain`.

## GitHub Pages URL

After pushing to GitHub and enabling Pages with GitHub Actions, the public URL is expected to be:

```text
https://hanhanzhang575-svg.github.io/pet-hospital-his/
```

## One-time setup

1. Log in to GitHub in your browser.
2. Create a new empty public repository, for example `pet-hospital-his`.
3. Send the repository HTTPS URL back to Codex, for example:

```text
https://github.com/hanhanzhang575-svg/pet-hospital-his.git
```

Codex can then add the remote, commit the deployment files, push to GitHub, and wait for GitHub Actions to publish the site.

If Git asks you to sign in, complete the Git Credential Manager browser login window. After that, future pushes should reuse the saved credential.
