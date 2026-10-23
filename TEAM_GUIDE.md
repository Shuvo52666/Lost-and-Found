# Three-person team workflow

## Ownership
- Member 1: `accounts/`, `communities/`, repo integration and environment configuration.
- Member 2: `newsfeed/`, common templates and CSS.
- Member 3: `verification/`, `messaging/`, `notifications/`.

## Start each feature
```bash
git switch main
git pull origin main
git switch -c feature/short-task-name
```
After coding, run tests, then:
```bash
git status
git add <files-you-changed>
git commit -m "Explain the change"
git push -u origin feature/short-task-name
```
Open a Pull Request on GitHub. Reviewer runs the app/tests and leaves feedback; merge when approved.

## Coordination rules
1. Never commit secrets, private data, or media files.
2. Discuss changes to shared templates, models and config before editing.
3. Model changes require migrations; commit migrations to your feature branch.
4. Use Issues or Projects with an owner and acceptance criteria.
5. Every PR should include test steps and screenshots for visual changes.
6. Update requirements when adding libraries.

## Next milestones
- Add proper reports moderation for community admins (reports currently visible in Django admin).
- Refine lost-post vs found-post claim flows and evidence handling.
- Add password reset/email verification and abuse prevention.
- Production-ready PostgreSQL, object storage, deployment, and monitoring.
