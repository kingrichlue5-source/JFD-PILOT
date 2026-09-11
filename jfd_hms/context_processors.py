from users_auth.models import HospitalSetting


def hospital_settings(request):
    setting = HospitalSetting.get_settings()
    return {
        'hospital_setting': setting,
        'hospital_name': setting.hospital_name,
        'hospital_short_name': setting.short_name,
        'hospital_tagline': setting.tagline,
        'hospital_logo_url': setting.logo.url if setting.logo else None,
        'registration_fee': setting.registration_fee,
        'followup_window_days': setting.followup_window_days,
    }
