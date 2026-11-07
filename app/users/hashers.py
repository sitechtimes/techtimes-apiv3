from django.contrib.auth.hashers import BCryptPasswordHasher

# This matches the amount of rounds used in techtimesv2 (django's default is 12)
class BCryptHasher(BCryptPasswordHasher):
    rounds = 10
