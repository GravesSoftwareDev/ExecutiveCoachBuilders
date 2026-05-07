from __future__ import annotations

from django.db import transaction

from .models import Lead, LeadMessage


@transaction.atomic
def ingest_inbound_form(cleaned_data: dict) -> Lead:
    lead = Lead.objects.create(**cleaned_data)
    LeadMessage.objects.create(
        lead=lead,
        direction=LeadMessage.Direction.IN,
        channel=LeadMessage.Channel.FORM,
        status=LeadMessage.Status.RECEIVED,
        subject='Website contact form',
        body=lead.message,
        from_email=lead.email,
        metadata={
            'source': lead.source,
            'source_url': lead.source_url,
            'phone_number': lead.phone_number,
            'company': lead.company,
            'budget': lead.budget,
            'interest': lead.interest,
            'passenger_count': lead.passenger_count,
            'timeline': lead.timeline,
            'use_case': lead.use_case,
        },
    )
    return lead
