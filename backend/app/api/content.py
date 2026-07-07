import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.brand import Brand
from app.models.competitor import Competitor
from app.models.persona import Persona
from app.schemas.content import ContentGenerateIn, ContentGenerateOut
from app.services.llm import LLMNotConfigured, generate_content

router = APIRouter(tags=["content"])


@router.post(
    "/brands/{brand_id}/content/generate", response_model=ContentGenerateOut
)
async def generate_brand_content(
    brand_id: uuid.UUID,
    payload: ContentGenerateIn,
    db: AsyncSession = Depends(get_db),
):
    """Generate marketing content grounded in the brand brain (stages 1-3) and the
    chosen platform's guidelines. Returns a ready-to-edit script."""
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand not found")

    personas_res = await db.execute(
        select(Persona)
        .where(Persona.brand_id == brand_id)
        .order_by(Persona.position, Persona.created_at)
    )
    personas = list(personas_res.scalars().all())

    comps_res = await db.execute(
        select(Competitor)
        .where(
            Competitor.brand_id == brand_id,
            Competitor.status == "considered",
        )
        .order_by(Competitor.is_primary.desc(), Competitor.position)
    )
    competitors = [
        {
            "name": c.name,
            "is_primary": c.is_primary,
            "moats": (c.analysis or {}).get("moats") if c.analysis else None,
        }
        for c in comps_res.scalars().all()
    ]

    try:
        script = await generate_content(
            brand_name=brand.name,
            vision=brand.vision,
            goal=brand.goal,
            moat=brand.moat,
            personas=personas,
            competitors=competitors,
            form=payload.form,
            content_format=payload.content_format,
            platform=payload.platform,
        )
    except LLMNotConfigured as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:  # noqa: BLE001 — surface provider errors cleanly
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"Content generation failed: {e}"
        )

    return ContentGenerateOut(script=script)
