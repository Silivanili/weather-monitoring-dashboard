# Contributing

This project follows GitHub Flow.

## Branching strategy

The `main` branch represents the stable and deployable state of the project.

Changes are developed on short-lived branches and merged into `main` through
Pull Requests.

Branch names should describe the purpose of the change, for example:

- `feature/weather-api`
- `feature/location-search`
- `fix/database-connection`
- `docs/update-readme`

## Workflow

1. Start from the latest `main`.
2. Create a short-lived feature or fix branch.
3. Make small, focused commits with meaningful commit messages.
4. Push the branch to GitHub.
5. Open a Pull Request.
6. Describe what changed and why.
7. Ensure automated checks are green.
8. Merge the Pull Request into `main`.

Direct feature development on `main` should be avoided.
