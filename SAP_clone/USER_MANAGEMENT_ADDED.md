# User Management Feature Added

## Summary

Successfully added a comprehensive User Management page accessible from the main navigation. This admin-only feature allows administrators to view all users, create new users, change passwords, and delete users.

## Backend Changes

### 1. New API Endpoint: `/api/v1/users`

Created `backend/api/routes/users.py` with the following endpoints:

- **GET /api/v1/users** - List all users (admin only)
- **POST /api/v1/users** - Create a new user (admin only)
- **GET /api/v1/users/{username}** - Get user details (admin only)
- **PATCH /api/v1/users/{username}/password** - Change user password (admin only)
- **DELETE /api/v1/users/{username}** - Delete a user (admin only, cannot delete admin)

### 2. Shared User Store

- Moved user storage to a shared `USER_STORE` in `users.py`
- Updated `auth.py` to import and use the shared user store
- Default users: engineer, manager, finance, admin

### 3. Admin Authorization

- Added `require_admin` dependency that validates JWT tokens
- Checks for Admin role before allowing access to user management endpoints
- Returns 403 Forbidden if user doesn't have Admin role

### 4. Registered Routes

Updated `backend/main.py` to include the new users router

## Frontend Changes

### 1. New Page: User Management

Created `frontend/src/pages/UserManagement.tsx` with features:

**User List View:**
- Table showing all users with username, roles, and creation date
- Stats cards showing total users, admins, engineers, and managers
- Color-coded role badges

**Create User:**
- Modal form to create new users
- Username and password fields
- Multi-select checkboxes for roles:
  - Maintenance Engineer (PM)
  - Store Manager (MM)
  - Finance Officer (FI)
  - Administrator
- Validation to ensure at least one role is selected

**Change Password:**
- Modal form to change user passwords
- New password and confirm password fields
- Password match validation

**Delete User:**
- Delete button for each user (except admin)
- Confirmation dialog before deletion

### 2. Updated Navigation

Added "👥 User Management" tab to `TopNavLayout.tsx` navigation bar

### 3. Updated API Service

Added `usersApi` to `frontend/src/services/api.ts`:
- list()
- create()
- get()
- changePassword()
- delete()

### 4. Updated Routing

Added route `/user-management` in `App.tsx`

## Access Control

- **Admin Only**: All user management features require Admin role
- **JWT Protected**: All endpoints validate JWT tokens
- **Cannot Delete Admin**: The admin user cannot be deleted for safety

## Available Roles

1. **Maintenance_Engineer** - Access to PM (Plant Maintenance) module
2. **Store_Manager** - Access to MM (Materials Management) module
3. **Finance_Officer** - Access to FI (Financial Accounting) module
4. **Admin** - Access to all modules + user management

## Testing

To test the User Management feature:

1. Login as admin (username: `admin`, password: `admin123`)
2. Navigate to "👥 User Management" tab
3. View existing users
4. Create a new user with selected roles
5. Change a user's password
6. Delete a user (except admin)

## Security Features

- JWT token validation on all endpoints
- Role-based access control (RBAC)
- Admin-only access to user management
- Password confirmation for password changes
- Cannot delete the admin user
- Proper error handling and user feedback
