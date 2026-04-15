from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import Domain
from app.schemas.domain import DomainCreate, DomainRead, DomainUpdate, DomainWithMailboxes


async def create_domain(db: AsyncSession, data: DomainCreate) -> DomainRead:
    domain = Domain(**data.model_dump())
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return DomainRead.model_validate(domain)


async def get_domains(db: AsyncSession) -> list[DomainWithMailboxes]:
    result = await db.execute(
        select(Domain).options(selectinload(Domain.mailboxes)).order_by(Domain.id)
    )
    domains = result.scalars().all()
    return [DomainWithMailboxes.model_validate(d) for d in domains]


async def get_domain(db: AsyncSession, domain_id: int) -> Domain:
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise ValueError("Domain not found")
    return domain


async def update_domain(db: AsyncSession, domain_id: int, data: DomainUpdate) -> DomainRead:
    domain = await get_domain(db, domain_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(domain, key, value)
    await db.commit()
    await db.refresh(domain)
    return DomainRead.model_validate(domain)


async def delete_domain(db: AsyncSession, domain_id: int) -> None:
    domain = await get_domain(db, domain_id)
    await db.delete(domain)
    await db.commit()
