import hashlib
import hmac
import time
from functools import wraps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.response import Response
from rest_framework import status


def verify_request(request):
    slack_signature = request.META.get('HTTP_X_SLACK_SIGNATURE')
    slack_request_timestamp = request.META.get('HTTP_X_SLACK_REQUEST_TIMESTAMP')

    if not slack_signature or not slack_request_timestamp:
        return False

    if time.time() - int(slack_request_timestamp) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        return False

    request_body = request.body.decode("utf-8")

    basestring = "v0:{}:{}".format(slack_request_timestamp, request_body).encode('utf-8')

    try:
        slack_signing_secret = bytes(settings.SLACK_SIGNING_SECRET, 'utf-8')
    except AttributeError:
        raise ImproperlyConfigured(
            "`settings.SLACK_SIGNING_SECRET` isn't defined"
        )

    my_signature = 'v0=' + hmac.new(slack_signing_secret, basestring, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(my_signature, slack_signature):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
