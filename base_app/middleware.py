from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from club.models import Club

class RedirectToClubMiddleware(MiddlewareMixin):
    """Middleware to handle club registration redirection"""

    def process_request(self, request):
        excluded_paths = [
            "/club/club-register/", "/accounts/login/", "/accounts/logout/", "/admin/", "/admin/login/"
        ]

        current_path = request.path

        # ✅ Allow access to admin panel & login page
        if any(current_path.startswith(path) for path in excluded_paths):
            return None  

        # ✅ If no club exists, redirect to club registration
        if not Club.objects.exists():
            messages.info(request, "Please register your club to get started.")
            return redirect("/club/club-register/")

        # # ✅ If the user is not logged in, redirect to login
        # if not request.user.is_authenticated:
        #     return redirect("/accounts/login/")

        return None
