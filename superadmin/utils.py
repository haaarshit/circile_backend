from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

class ResponseWrapperMixin:
    """
    Mixin to wrap all responses in {"status": true, "data": ...} for success
    and {"status": false, "error": ...} for failure.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        # Call the parent method to get the initial response
        response = super().finalize_response(request, response, *args, **kwargs)

        # Check if the response is already rendered (e.g., not an exception)
        if hasattr(response, 'data') and response.status_code < 400:  # Success cases
            wrapped_data = {"status": True, "data": response.data}
            response.data = wrapped_data
        elif response.status_code >= 400:  # Error cases
            # Handle DRF exceptions (e.g., ValidationError) or other errors
            error_data = response.data if hasattr(response, 'data') else str(response)
            wrapped_data = {"status": False, "error": error_data}
            response.data = wrapped_data

        return response