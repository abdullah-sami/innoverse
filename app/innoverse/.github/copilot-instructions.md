# Copilot Instructions for innoverse Expo App

## Project Overview
- This is an [Expo](https://expo.dev) React Native project using TypeScript, created with `create-expo-app`.
- The main app code is in the `app/` directory, using [file-based routing](https://docs.expo.dev/router/introduction).
- UI components are in `components/`, with a `ui/` subfolder for reusable primitives.
- Assets (images) are in `assets/images/`.
- Constants, hooks, interfaces, and types are organized in their respective folders.
- The project uses Tailwind CSS via `nativewind` (see `tailwind.config.js`).

## Key Workflows
- **Install dependencies:** `npm install`
- **Start development server:** `npx expo start`
- **Reset project to blank state:** `npm run reset-project` (runs `scripts/reset-project.js`)
- **Edit app code:** Work inside the `app/` directory. Routing is file-based.

## Patterns & Conventions
- **File-based routing:** Each file in `app/` (and subfolders) is a route. Use `_layout.tsx` for layout wrappers.
- **Theming:** Use hooks in `hooks/` (e.g., `use-theme-color.ts`) and constants in `constants/theme.ts` for color and theme logic.
- **Component structure:** Prefer splitting UI into small, reusable components in `components/` and `components/ui/`.
- **TypeScript:** All code should be typed. Shared types/interfaces go in `types/` and `interfaces/`.
- **API & services:** Place API logic in `services/` (e.g., `api.ts`, `useFetch.ts`).
- **Assets:** Reference images via `constants/images.ts` for consistency.

## External Integrations
- **Expo**: Core platform for development, builds, and device features.
- **Nativewind**: Tailwind CSS for styling React Native components.

## Examples
- To add a new screen: create a new file in `app/` (e.g., `app/profile.tsx`).
- To add a new reusable button: add to `components/ui/`.
- To add a new API call: extend `services/api.ts` or add a new service file.

## Notable Files
- `app/_layout.tsx`: Root layout for all screens.
- `app/(tabs)/_layout.tsx`: Layout for tabbed navigation.
- `components/`: Custom and shared UI components.
- `constants/`: App-wide constants (icons, images, theme).
- `services/`: API and device service logic.
- `tailwind.config.js`: Tailwind/Nativewind config.
- `scripts/reset-project.js`: Script to reset the app to a blank state.

## Tips for AI Agents
- Follow the file/folder structure for new features.
- Use TypeScript types for all new code.
- Prefer hooks and constants for theme and color logic.
- Reference assets through `constants/images.ts`.
- Use Expo/Nativewind documentation for platform-specific features.
