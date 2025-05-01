# Project File Overview

Below is a breakdown of each key file in this repository and its purpose:

```
./.env
./tailwind.config.cjs
./postcss.config.cjs

./src/apiClient.ts
./src/types/api.ts
./src/index.tsx
./src/index.css
./src/App.tsx

./src/services/
  ├ authService.ts
  ├ problemsService.ts
  ├ submissionsService.ts
  └ profileService.ts

./src/features/
  ├ auth/
  │  ├ LoginPage.tsx
  │  └ RegisterPage.tsx
  ├ problems/
  │  ├ ProblemListPage.tsx
  │  └ ProblemDetailPage.tsx
  ├ editor/
  │  └ CodeEditor.tsx
  ├ submissions/
  │  └ SubmissionsPage.tsx
  └ profile/
     └ ProfilePage.tsx

./src/components/
  ├ Button.tsx
  └ Input.tsx

./src/hooks/
  ├ useAuth.ts
  ├ useProblems.ts
  ├ useSubmissions.ts
  └ useProfile.ts

./src/store/
  └ authStore.ts

./src/utils/formatDate.ts
```

## Top-level Configuration

- **`.env`**: Defines environment variables (e.g. `REACT_APP_API_BASE_URL`) for local development.
- **`openapi.json`**: OpenAPI specification for the backend API, used to generate typed interfaces.
- **`tailwind.config.cjs`**: Tailwind CSS configuration (content paths, theme extensions).
- **`postcss.config.cjs`**: PostCSS setup for Tailwind processing.

## Core Bootstrap & Types

- **`src/apiClient.ts`**: Sets up an Axios instance with base URL and auth-header interceptor.
- **`src/types/api.ts`**: Generated TypeScript interfaces for all API request/response payloads via `openapi-typescript`.
- **`src/index.tsx`**: Entry point—initializes React, React Query client, and React Router, then mounts `<App />`.
- **`src/index.css`**: Imports Tailwind’s base, components, and utilities layers.
- **`src/App.tsx`**: Defines the top-level `<Routes>` and maps paths to feature pages.

## Services Layer (`src/services/`)

Each `*Service.ts` file exports typed functions to call the corresponding API endpoints:

- **`authService.ts`**: `login()`, `register()` calls for authentication.
- **`problemsService.ts`**: `getProblems()`, `getProblemById()` for problem catalog data.
- **`submissionsService.ts`**: `createSubmission()`, `getSubmissions()` for handling code submissions.
- **`profileService.ts`**: `getProfile()` to fetch user profile and stats.

## Feature Pages (`src/features/`)

Organized by domain, each folder contains page components for the MVP:

- **`auth/`**: `LoginPage.tsx`, `RegisterPage.tsx` — forms for sign-in and sign-up.
- **`problems/`**: `ProblemListPage.tsx`, `ProblemDetailPage.tsx` — display problem catalog and details.
- **`editor/`**: `CodeEditor.tsx` — wrapper around the code editor (e.g. Monaco/CodeMirror).
- **`submissions/`**: `SubmissionsPage.tsx` — list of user’s past submissions.
- **`profile/`**: `ProfilePage.tsx` — user profile and statistics dashboard.

## Shared UI Components (`src/components/`)

- **`Button.tsx`**: Reusable `<Button>` component with custom styling props.
- **`Input.tsx`**: Reusable `<Input>` component wrapping native `<input>`.

## Custom Hooks (`src/hooks/`)

Simplify data fetching and state across components:

- **`useAuth.ts`**: Manages authentication state (e.g. token storage).
- **`useProblems.ts`**: Fetches and caches problem list/details via React Query.
- **`useSubmissions.ts`**: Fetches user submissions.
- **`useProfile.ts`**: Fetches current user’s profile data.

## Client-side Store (`src/store/`)

- **`authStore.ts`**: Lightweight auth state store (e.g. using Zustand or Context API) to share user/session info.

## Utilities (`src/utils/formatDate.ts`)

- **`formatDate.ts`**: Helper to format timestamps into human-readable strings.

---
