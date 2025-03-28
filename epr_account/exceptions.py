from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # If response exists, modify it to include "status": False
    if response is not None:
        response.data["status"] = False

    return response
    # response = exception_handler(exc, context)

    # if response is not None:
    #     error_detail = response.data

    #     # Extract the first error message if it is a dictionary
    #     if isinstance(error_detail, dict):
    #         # Flatten the nested dictionary error messages
    #         error_messages = []
    #         for key, value in error_detail.items():
    #             if isinstance(value, list):  # Typical DRF ValidationError structure
    #                 error_messages.extend(value)
    #             else:
    #                 error_messages.append(str(value))
            
    #         error_message = error_messages[0] if error_messages else "An unknown error occurred."
    #     else:
    #         error_message = str(exc)

    #     print(error_message)

    #     response.data = {
    #         "status": False,
    #         "error": error_message
    #     }

    # return response