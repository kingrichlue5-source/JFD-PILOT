from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from .engine import FORMAT_HANDLERS
from .providers import PROVIDERS


@require_GET
@login_required
def export_data(request, data_type):
    fmt = request.GET.get('format', 'csv').lower()

    if data_type not in PROVIDERS:
        return JsonResponse({'error': f'Unknown data type: {data_type}. Available: {", ".join(PROVIDERS.keys())}'}, status=400)

    if fmt not in FORMAT_HANDLERS:
        return JsonResponse({'error': f'Unknown format: {fmt}. Available: {", ".join(FORMAT_HANDLERS.keys())}'}, status=400)

    headers, rows, title = PROVIDERS[data_type]()
    return FORMAT_HANDLERS[fmt](headers, rows, title)
