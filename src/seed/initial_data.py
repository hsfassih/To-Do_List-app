# hardcoded entries for users table
users_db = [
    {
        "id": 1,
        "full_name": "Jameel Hussain",
        "username": "jamil",
        "password": "jameel@123",
        "role": "admin",
    },
    {
        "id": 2,
        "full_name": "Roshan Kaleem",
        "username": "roshan",
        "password": "roshan@123",
        "role": "admin",
    },
    {
        "id": 3,
        "full_name": "Syed Fassih",
        "username": "hsfassih",
        "password": "fassih@1730",
        "role": "user",
    },
    {
        "id": 4,
        "full_name": "Nauman Ahmed",
        "username": "nauman",
        "password": "nauman@123",
        "role": "user",
    },
    {
        "id": 5,
        "full_name": "Musadiq Ashfak",
        "username": "musadiq",
        "password": "musadiq@123",
        "role": "user",
    },
]

# hardcoded entries for tasks table
tasks_db = [
    {
        "id": 1,
        "assigner": "jamil",
        "assignee": "hsfassih",
        "detail": "Complete project documentation",
        "task_status": "pending",
    },
    {
        "id": 2,
        "assigner": "jamil",
        "assignee": "nauman",
        "detail": "Fix bug in authentication module",
        "task_status": "in_progress",
    },
    {
        "id": 3,
        "assigner": "roshan",
        "assignee": "musadiq",
        "detail": "Review pull requests",
        "task_status": "pending",
    },
    {
        "id": 4,
        "assigner": "roshan",
        "assignee": "hsfassih",
        "detail": "Update database schema",
        "task_status": "done",
    },
    {
        "id": 5,
        "assigner": "jamil",
        "assignee": "nauman",
        "detail": "Implement unit tests",
        "task_status": "pending",
    },
    {
        "id": 6,
        "assigner": "roshan",
        "assignee": "musadiq",
        "detail": "Deploy to staging environment",
        "task_status": "in_progress",
    },
    {
        "id": 7,
        "assigner": "jamil",
        "assignee": "musadiq",
        "detail": "Create API documentation",
        "task_status": "pending",
    },
    {
        "id": 8,
        "assigner": "roshan",
        "assignee": "nauman",
        "detail": "Optimize database queries",
        "task_status": "done",
    },
    {
        "id": 9,
        "assigner": "jamil",
        "assignee": "hsfassih",
        "detail": "Setup monitoring alerts",
        "task_status": "pending",
    },
    {
        "id": 10,
        "assigner": "roshan",
        "assignee": "hsfassih",
        "detail": "Refactor legacy code",
        "task_status": "in_progress",
    },
]
