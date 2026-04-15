import json

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.campaign import Campaign, CampaignStatus
from app.models.text_variation import TextVariation
from app.schemas.text_variation import VariationRead, VariationUpdate


async def generate_variations(db: AsyncSession, campaign_id: int, count: int = 30):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError("Campaign not found")

    campaign.status = CampaignStatus.GENERATING
    await db.commit()

    client = OpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
    )

    first_paragraph = campaign.original_body.split("\n\n")[0] if "\n\n" in campaign.original_body else campaign.original_body[:300]

    prompt = f"""Сгенерируй {count} вариаций темы письма и первого абзаца.
Сохрани смысл, тон и примерную длину. Измени формулировки, порядок слов, используй синонимы.
Не добавляй ничего нового. Каждая вариация должна быть уникальной.

Оригинальная тема: {campaign.original_subject}
Оригинальный первый абзац: {first_paragraph}

Верни JSON-массив из {count} объектов:
[{{"subject": "...", "iceberg": "..."}}]

Только JSON, без markdown-обёрток и пояснений."""

    response = client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    variations_data = json.loads(text)

    for item in variations_data:
        variation = TextVariation(
            campaign_id=campaign_id,
            subject_variant=item["subject"],
            iceberg_variant=item["iceberg"],
        )
        db.add(variation)

    campaign.status = CampaignStatus.READY
    await db.commit()


async def get_variations(db: AsyncSession, campaign_id: int) -> list[VariationRead]:
    result = await db.execute(
        select(TextVariation)
        .where(TextVariation.campaign_id == campaign_id)
        .order_by(TextVariation.id)
    )
    return [VariationRead.model_validate(v) for v in result.scalars().all()]


async def update_variation(db: AsyncSession, variation_id: int, data: VariationUpdate) -> VariationRead:
    result = await db.execute(select(TextVariation).where(TextVariation.id == variation_id))
    variation = result.scalar_one_or_none()
    if not variation:
        raise ValueError("Variation not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(variation, key, value)
    await db.commit()
    await db.refresh(variation)
    return VariationRead.model_validate(variation)


async def delete_variation(db: AsyncSession, variation_id: int) -> None:
    result = await db.execute(select(TextVariation).where(TextVariation.id == variation_id))
    variation = result.scalar_one_or_none()
    if not variation:
        raise ValueError("Variation not found")
    await db.delete(variation)
    await db.commit()
