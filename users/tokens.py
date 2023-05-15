from django.contrib.auth.tokens import PasswordResetTokenGenerator
import datetime


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)

    # default timeout to 7 days
    def _get_timestamp(self):
        return int(datetime.datetime.now().timestamp()) // (60 * 60 * 24 * 7)


account_activation_token = AccountActivationTokenGenerator()
