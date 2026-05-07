from __future__ import annotations

from django.conf import settings


def _tel_href(raw: str) -> str:
    digits = ''.join(c for c in raw if c.isdigit() or c == '+')
    if not digits:
        return ''
    if digits.startswith('+'):
        return f'tel:{digits}'
    if len(digits) == 10:
        return f'tel:+1{digits}'
    if len(digits) == 11 and digits.startswith('1'):
        return f'tel:+{digits}'
    return f'tel:{digits}'


def public_contact(request):
    phone = getattr(settings, 'CONTACT_PUBLIC_PHONE', '') or ''
    email = getattr(settings, 'CONTACT_PUBLIC_EMAIL', '') or ''
    return {
        'contact_public_phone': phone,
        'contact_public_email': email,
        'contact_tel_href': _tel_href(phone),
        'contact_address_line1': getattr(settings, 'CONTACT_PUBLIC_ADDRESS_LINE1', '') or '',
        'contact_address_line2': getattr(settings, 'CONTACT_PUBLIC_ADDRESS_LINE2', '') or '',
        'contact_maps_url': getattr(settings, 'CONTACT_PUBLIC_MAPS_URL', '') or '',
        'contact_social_facebook_url': getattr(settings, 'CONTACT_SOCIAL_FACEBOOK_URL', '') or '',
        'contact_social_youtube_url': getattr(settings, 'CONTACT_SOCIAL_YOUTUBE_URL', '') or '',
        'contact_social_x_url': getattr(settings, 'CONTACT_SOCIAL_X_URL', '') or '',
    }
