PERMISSIONS = [
    # users
    {"code": "users.view", "module": "users", "description": "View users"},
    {"code": "users.create", "module": "users", "description": "Create users"},
    {"code": "users.edit", "module": "users", "description": "Edit users"},
    {"code": "users.deactivate", "module": "users", "description": "Deactivate users"},
    {"code": "users.reset_password", "module": "users", "description": "Reset user passwords"},
    {"code": "users.force_logout", "module": "users", "description": "Force logout users"},

    # roles / permissions
    {"code": "roles.view", "module": "roles", "description": "View roles"},
    {"code": "roles.edit", "module": "roles", "description": "Edit roles"},
    {"code": "permissions.view", "module": "permissions", "description": "View permissions"},
    {"code": "permissions.manage", "module": "permissions", "description": "Manage permissions"},

    # specialists
    {"code": "specialists.view", "module": "specialists", "description": "View specialists"},
    {"code": "specialists.create", "module": "specialists", "description": "Create specialists"},
    {"code": "specialists.edit", "module": "specialists", "description": "Edit specialists"},
    {"code": "specialists.deactivate", "module": "specialists", "description": "Deactivate specialists"},
    {"code": "specialists.assign_group", "module": "specialists", "description": "Assign specialists to groups"},

    # groups
    {"code": "groups.view", "module": "groups", "description": "View groups"},
    {"code": "groups.create", "module": "groups", "description": "Create groups"},
    {"code": "groups.edit", "module": "groups", "description": "Edit groups"},
    {"code": "groups.manage_members", "module": "groups", "description": "Manage group members"},

    # sessions / audit / dashboard
    {"code": "sessions.view_all", "module": "sessions", "description": "View all sessions"},
    {"code": "audit.view_scope", "module": "audit", "description": "View scoped audit logs"},
    {"code": "audit.view_all", "module": "audit", "description": "View all audit logs"},
    {"code": "audit.export", "module": "audit", "description": "Export audit logs"},
    {"code": "dashboards.view_admin", "module": "dashboard", "description": "View admin dashboard"},
    {"code": "dashboards.view_dispatcher", "module": "dashboard", "description": "View dispatcher dashboard"},
]