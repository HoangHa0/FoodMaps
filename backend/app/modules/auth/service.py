"""M1 business logic. Routers call these functions; no SQL in routers.

Planned functions:
    register(db, data: RegisterIn) -> User         # 409 "username_taken"
    authenticate(db, data: LoginIn) -> User        # 401 "invalid_credentials" (same error for
                                                   #     unknown user and wrong password)
    get_user(db, user_id) -> User | None
"""
