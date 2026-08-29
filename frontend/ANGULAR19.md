# Angular 19 migration

This frontend is upgraded from Angular 18 to Angular 19 and now uses Angular Router for the three-step presentation workflow.

## Routes

- `/prompt` — create the presentation
- `/outline` — review and edit the generated outline
- `/preview` — preview/export the presentation

The old `StateService.goTo(1|2|3)` API is preserved, but it now updates the signal and navigates to the corresponding route.

## Install and run

```bash
npm install
npm start
```

The backend API URL remains configured in `src/environments/environment.ts`.

## Important

`package-lock.json` was intentionally removed because the original lockfile contained Angular 18 dependencies. Run `npm install` with Node.js compatible with Angular 19 to generate a fresh lockfile.
