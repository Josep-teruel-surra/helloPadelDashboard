import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.inventory import service
from app.modules.inventory.models import ProductCategory
from app.modules.inventory.schemas import (
    MovementCreate,
    MovementRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)

# Material de empresa: todo el equipo lo consulta, lo da de alta y registra entradas.
# Borrar y ajustar stock a mano queda para admins.
router = APIRouter(tags=["inventory"])


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    _: CurrentUser,
    session: SessionDep,
    include_inactive: bool = False,
    category: ProductCategory | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[ProductRead]:
    products = await service.list_products(
        session, include_inactive=include_inactive, category=category, q=q
    )
    return await service.to_reads(session, products)


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate, user: CurrentUser, session: SessionDep
) -> ProductRead:
    product = await service.create_product(session, user, data)
    return await service.to_read(session, product)


@router.get("/products/{product_id}", response_model=ProductRead)
async def read_product(product_id: uuid.UUID, _: CurrentUser, session: SessionDep) -> ProductRead:
    return await service.to_read(session, await service.get_product(session, product_id))


@router.patch("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID, data: ProductUpdate, _: CurrentUser, session: SessionDep
) -> ProductRead:
    product = await service.get_product(session, product_id)
    return await service.to_read(session, await service.update_product(session, product, data))


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    await service.delete_product(session, user, await service.get_product(session, product_id))


@router.post(
    "/products/{product_id}/variants",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_variant(
    product_id: uuid.UUID, data: VariantCreate, user: CurrentUser, session: SessionDep
) -> ProductRead:
    product = await service.get_product(session, product_id)
    return await service.to_read(session, await service.add_variant(session, user, product, data))


@router.patch("/variants/{variant_id}", response_model=ProductRead)
async def update_variant(
    variant_id: uuid.UUID, data: VariantUpdate, _: CurrentUser, session: SessionDep
) -> ProductRead:
    variant = await service.get_variant(session, variant_id)
    variant = await service.update_variant(session, variant, data)
    return await service.to_read(session, variant.product)


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(variant_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    await service.delete_variant(session, user, await service.get_variant(session, variant_id))


@router.get("/stock/movements", response_model=list[MovementRead])
async def list_movements(
    _: CurrentUser,
    session: SessionDep,
    variant_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[MovementRead]:
    movements = await service.list_movements(
        session, variant_id=variant_id, product_id=product_id, limit=limit
    )
    return await service.movement_reads(session, movements)


@router.post("/stock/movements", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
async def create_movement(
    data: MovementCreate, user: CurrentUser, session: SessionDep
) -> MovementRead:
    return service.movement_read(await service.create_movement(session, user, data))
