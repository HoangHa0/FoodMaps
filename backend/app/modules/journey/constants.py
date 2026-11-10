"""Numbers of the Food Journey module that the team may want to change.

Everything tunable lives in this one file. Change a value here and rebuild; nothing else
needs to move (schemas, service and tests all read these names).
"""

# --- share links ---------------------------------------------------------------------------
# How long a share link stays valid. After this many days the snapshot is deleted from the
# database (on the next "create share link" request) and the link answers 404.
SHARE_LIFETIME_DAYS = 7

# Max share links one network address may create per hour. The address is stored only as a
# keyed hash, just to count. Raise it if a class or a team demo shares many links at once.
SHARES_PER_IP_PER_HOUR = 10

# Random bytes in a share code (token_urlsafe gives about 1.3 characters per byte, so 8 bytes
# is a code of 11 characters). Longer = harder to guess. Keep the code column wide enough
# (see CODE_COLUMN_LENGTH).
SHARE_CODE_BYTES = 8
CODE_COLUMN_LENGTH = 32

# --- library -------------------------------------------------------------------------------
# Max journeys one account may keep. Saving another one answers 409 `journey_limit`.
MAX_JOURNEYS_PER_USER = 20

# --- inside one journey --------------------------------------------------------------------
# Max stops per journey (also per share link). Google Maps links hold about 9 waypoints each,
# so a 20-stop journey becomes at most 3 chained links.
MAX_STOPS_PER_JOURNEY = 20

TITLE_MAX_LENGTH = 100
NOTE_MAX_LENGTH = 300
