import logging
from datetime import date
from .models import Committee

logger = logging.getLogger(__name__)

class AutoDeactivateCommitteeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = date.today()
        expired_committees = Committee.objects.filter(end_date__lt=today, is_active=True)
        
        # Log the deactivation
        if expired_committees.exists():
            logger.info(f"Deactivating {expired_committees.count()} expired committees.")
            expired_committees.update(is_active=False)
        
        response = self.get_response(request)
        return response
