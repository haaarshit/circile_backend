from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # If response exists, modify it to include "status": False
    if response is not None:
        response.data["status"] = False

    return response
