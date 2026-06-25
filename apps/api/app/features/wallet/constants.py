"""Wallet credit constants.

These are intentionally defined in code (not the database) so they are reviewed
through version control rather than mutated at runtime.
"""

# Credits granted once when a user registers, when the signup bonus is enabled
# via Settings.signup_bonus_enabled.
SIGNUP_BONUS_CREDITS = 1000

# Capped rollover: when a subscription plan has rollover enabled, the balance
# after a renewal grant is capped at this multiple of the plan's per-cycle
# credit allowance. Unused credits roll over only up to this ceiling.
ROLLOVER_CAP_MULTIPLIER = 2

# --- Metering / pricing -----------------------------------------------------
# An AI request is converted to credits via:
#   weighted = input_tokens * INPUT_WEIGHT + output_tokens * OUTPUT_WEIGHT
#   credits  = max(MIN_CREDITS_PER_REQUEST,
#                  ceil(weighted / TOKENS_PER_CREDIT * MARGIN_MULTIPLIER))
# Output tokens are weighted higher because OpenAI bills them at a higher rate.
INPUT_WEIGHT = 1
OUTPUT_WEIGHT = 4
# Defines the credit unit: 1 credit ~= this many weighted tokens. A larger value
# keeps user-facing credit numbers small/friendly.
TOKENS_PER_CREDIT = 100
# Business markup over the raw converted cost.
MARGIN_MULTIPLIER = 1.5
# Floor so trivial requests still cost something; also the minimum balance a user
# must hold before a token-metered request is allowed.
MIN_CREDITS_PER_REQUEST = 5

# Flat credit cost for image workflows, which do not report token usage.
FLAT_CREDITS_PER_IMAGE = 20
