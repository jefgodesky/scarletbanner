from rest_framework import exceptions, status, views


def exception_handler(exc: Exception, context):
    response = views.exception_handler(exc, context)

    if isinstance(exc, (exceptions.AuthenticationFailed, exceptions.NotAuthenticated)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        response["WWW-Authenticate"] = "Bearer"

    return response
