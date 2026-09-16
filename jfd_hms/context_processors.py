def hospital_settings(request):
    try:
        from users_auth.models import HospitalSetting
        setting = HospitalSetting.get_settings()
        logo_url = None
        try:
            if setting.logo:
                logo_url = setting.logo.url
        except Exception:
            logo_url = None
        return {
            'hospital_setting': setting,
            'hospital_name': setting.hospital_name,
            'hospital_short_name': setting.short_name,
            'hospital_tagline': setting.tagline,
            'hospital_logo_url': logo_url,
            'registration_fee': setting.registration_fee,
            'followup_window_days': setting.followup_window_days,
        }
    except Exception:
        return {
            'hospital_name': 'JFD Hospital',
            'hospital_short_name': 'JFD',
            'hospital_tagline': 'Hospital Management Information System',
            'hospital_logo_url': None,
            'registration_fee': 5.00,
            'followup_window_days': 30,
        }
