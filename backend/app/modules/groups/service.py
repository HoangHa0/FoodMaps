"""M5 business logic. Routers call only these functions.

Planned functions:
    create_room(db, data, user)                 -> (room, participant, token)
    join_room(db, code, data, user)             -> (participant, token)
    authenticate_participant(db, code, token)   -> (room, participant)   # 401 / 404
    start_room(db, room, host, criteria, provider)                       # 403 if not host
    cast_vote(db, room, participant, data)      # locks the room row (SELECT ... FOR UPDATE),
                                                # then applies rules.decide
    get_state(db, room, participant, since_version) -> RoomStateOut
    expire_if_needed(db, room)                  # called at the start of every request
                                                # (lazy expiry, no background job needed)
"""
