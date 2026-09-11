"""
Algorithmic Triage Engine — evaluates vital signs against Admin-configured
TriageCriteria rules to auto-suggest acuity level and department routing.

The clinician's judgment is always final — suggestions can be overridden.
"""
import logging

logger = logging.getLogger('clinical')


def evaluate_vitals(vitals_dict):
    """
    Evaluate vital signs against active TriageCriteria rules.

    Args:
        vitals_dict: dict with keys like 'temperature', 'heart_rate', etc.
            Values can be int, float, or string-numeric.

    Returns:
        dict with:
            'suggested_acuity': int (1-5)
            'suggested_department': str (ER, OPD, IPD, OBGYN)
            'matched_rules': list of {name, vital_sign, operator, threshold, matched_value, suggested_acuity, suggested_department}
            'reason': str (human-readable summary)
    """
    from clinical.models import TriageCriteria

    criteria = TriageCriteria.objects.filter(is_active=True).order_by('priority', 'vital_sign')

    matched_rules = []
    highest_acuity = 5
    best_department = 'OPD'

    department_priority = {'ER': 1, 'OBGYN': 2, 'IPD': 3, 'OPD': 4}

    for rule in criteria:
        raw_value = vitals_dict.get(rule.vital_sign)
        if raw_value is None:
            continue

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        matched = False
        threshold = float(rule.threshold_low)

        if rule.operator == 'lt':
            matched = value < threshold
        elif rule.operator == 'lte':
            matched = value <= threshold
        elif rule.operator == 'gt':
            matched = value > threshold
        elif rule.operator == 'gte':
            matched = value >= threshold
        elif rule.operator == 'eq':
            matched = abs(value - threshold) < 0.01
        elif rule.operator == 'between':
            high = float(rule.threshold_high) if rule.threshold_high else threshold
            matched = threshold <= value <= high

        if matched:
            matched_rules.append({
                'name': rule.name,
                'vital_sign': rule.vital_sign,
                'operator': rule.get_operator_display(),
                'threshold': str(rule.threshold_low),
                'matched_value': str(value),
                'suggested_acuity': rule.suggested_acuity,
                'suggested_department': rule.suggested_department,
            })

            if rule.suggested_acuity < highest_acuity:
                highest_acuity = rule.suggested_acuity

            if department_priority.get(rule.suggested_department, 99) < department_priority.get(best_department, 99):
                best_department = rule.suggested_department

    if not matched_rules:
        return {
            'suggested_acuity': 5,
            'suggested_department': 'OPD',
            'matched_rules': [],
            'reason': 'No criteria matched — defaulting to Non-Urgent / OPD',
        }

    rule_names = [r['name'] for r in matched_rules]
    return {
        'suggested_acuity': highest_acuity,
        'suggested_department': best_department,
        'matched_rules': matched_rules,
        'reason': f"Matched: {', '.join(rule_names)}",
    }


ACUITY_LABELS = {
    1: 'Resuscitation (Immediate)',
    2: 'Emergent (High)',
    3: 'Urgent (Medium)',
    4: 'Less Urgent (Low)',
    5: 'Non-Urgent (Lowest)',
}


def get_acuity_label(level):
    """Return human-readable label for acuity level."""
    return ACUITY_LABELS.get(level, f'Level {level}')
