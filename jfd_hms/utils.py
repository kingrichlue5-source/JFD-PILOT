import logging
from django.db import transaction, IntegrityError

logger = logging.getLogger(__name__)


def generate_sequence_number(prefix, model, field_name, max_retries=5):
    """Generate a unique sequential number with retry logic for concurrency safety.

    Works on both SQLite and PostgreSQL. Uses transaction.atomic() with
    IntegrityError retry to handle concurrent sequence generation.

    Args:
        prefix: The prefix string (e.g. 'VIS-20260101-')
        model: The Django model class to query
        field_name: The CharField name that stores the sequence number
        max_retries: Number of retries on IntegrityError (default 5)

    Returns:
        The generated sequence number string (e.g. 'VIS-20260101-00001')
    """
    from django.db.models import Max

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                last_value = model.objects.select_for_update().filter(
                    **{f'{field_name}__startswith': prefix}
                ).aggregate(max_val=Max(field_name))['max_val']

                if last_value:
                    try:
                        seq = int(last_value.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1

                return f"{prefix}{seq:05d}"
        except IntegrityError:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Sequence generation conflict for {model.__name__}.{field_name} "
                    f"with prefix {prefix}, retrying (attempt {attempt + 1}/{max_retries})"
                )
                continue
            raise

    raise RuntimeError(
        f"Failed to generate unique sequence number for "
        f"{model.__name__}.{field_name} after {max_retries} attempts"
    )
