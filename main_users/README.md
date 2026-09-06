# main_users

Authentication app with a custom email-based user model.

## Owns

- `MainUser` (`AUTH_USER_MODEL`)
- Registration, login, logout, profile update flows

## User Model

- `username` removed
- `email` is unique login identifier
- extra optional fields: `profile_picture`, `country`, `language`

## Routes

- `/users/register/`
- `/users/login/`
- `/users/logout/`
- `/users/profile/`

## Settings Requirements

- `AUTH_USER_MODEL = 'main_users.MainUser'`
- `LOGIN_URL = '/users/login/'`
- `LOGIN_REDIRECT_URL = '/main/'`

## Notes

- Superusers are created with email (no username).
- Default profile image path: `main_media/profile_pictures/default_profile_picture.jpg`.
