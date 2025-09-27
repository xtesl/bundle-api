from typing import Any, List, Sequence, TypeVar, Union, Optional, Type

from sqlmodel import select, SQLModel, func
from sqlalchemy.orm.attributes import InstrumentedAttribute
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession



from src.models.data import PaginationResponse
from src.utils.helpers import gen_offset_pagination_metadata


async def get_object_or_404_v2(
    session: AsyncSession,
    where_clauses: Sequence[Any],
    model: Type[SQLModel],
    fields: Optional[List[Any]] = None,
    res: bool = True,
) -> Any:
    """
    Fetch an object or selected fields with flexible filters. Raises 404 if not found.

    Args:
        session (AsyncSession): SQLModel async session.
        where_clauses (Sequence[Any]): List of SQLModel filter expressions.
        model (Type[SQLModel]): The SQLModel class to query.
        fields (Optional[List[Any]]): List of fields to select.
        res (bool): Whether to raise HTTPException if not found.

    Returns:
        Union[dict, SQLModel]: A dictionary if specific fields were selected, else a full model instance.
    """
    stmt = select(*fields) if fields else select(model)
    stmt = stmt.where(*where_clauses)

    result = await session.exec(stmt)
    row = result.first()

    if row is None:
        if res:
            raise HTTPException(
                status_code=404,
                detail=f"{model.__name__} object not found."
            )
        return None

    if fields:
        field_names = [f.key for f in fields]
        return dict(zip(field_names, row))

    return row

async def get_object_or_404(
    session: AsyncSession,  
    where_attr: InstrumentedAttribute,
    where_value: Any,
    fields: List[Any] | None = None,
    res: bool = True
) -> Any:
    model_class = where_attr.class_

    if fields:
        statement = select(*fields).where(where_attr == where_value)
        result = await session.exec(statement)
        row = result.first()
        
        if row is None and res:
            raise HTTPException(
                status_code=404,
                detail=f"{model_class.__name__} object not found."
            )
        
        if row:
            field_names = [f.key for f in fields]
            return dict(zip(field_names, row))
        return None
    else:
        statement = select(model_class).where(where_attr == where_value)
        result = await session.exec(statement) 
        obj = result.first()  
        
        if obj is None and res:
            raise HTTPException(
                status_code=404,
                detail=f"{model_class.__name__} object not found."
            )
        
        return obj

async def get_objects_v2(
    session: AsyncSession,
    where_clauses: Optional[Sequence[Any]] = None,
    model: Type[SQLModel] = None,
    fields: Optional[List[Any]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: Optional[Sequence[Any]] = None,
    options: Optional[Sequence[Any]] = None,  # for eager loading
    raise_404: bool = False,
) -> List[Union[SQLModel, dict]]:
    if model is None:
        raise ValueError("You must provide a model to query.")

    stmt = select(*fields) if fields else select(model)

    if where_clauses:
        stmt = stmt.where(*where_clauses)
    if order_by:
        stmt = stmt.order_by(*order_by)
    if options:
        stmt = stmt.options(*options)
    if limit:
        stmt = stmt.limit(limit)
    if offset:
        stmt = stmt.offset(offset)

    result = await session.execute(stmt)

    if fields:
        rows = result.all()
    else:
        rows = result.scalars().all()

    if not rows and raise_404:
        raise HTTPException(
            status_code=404,
            detail=f"No {model.__name__} records found."
        )

    if fields:
        field_names = [f.key for f in fields]
        return [dict(zip(field_names, row)) for row in rows]

    return rows



T = TypeVar("T")

async def get_objects(
    session: AsyncSession,
    model: type[SQLModel],
    offset: int = 0,
    limit: int = 0,
    location: str | None = None,
    filter_by: tuple[InstrumentedAttribute, Any] | None = None,
    fields: list[Any] | None = None,
) -> Union[Sequence[SQLModel], PaginationResponse]:
    """
    Retrieve a list of objects with optional filtering, field selection, and offset-based pagination.

    - `model`: SQLModel class to query.
    - `offset`, `limit`: used for pagination.
    - `location`: optional endpoint location (used in pagination metadata).
    - `filter_by`: tuple of (model_field, value) to filter by a specific field.
    - `fields`: list of model fields to return (projection).
    """

    serializable = True

    # SELECT clause
    if fields:
        select_stmt = select(*fields)
        serializable = False  # Tuples returned, needs manual serialization
    else:
        select_stmt = select(model)

    # WHERE clause
    if filter_by:
        field, value = filter_by
        select_stmt = select_stmt.where(field == value)

    # COUNT for pagination
    total = None
    if limit > 0 and location:
        count_stmt = select(func.count()).select_from(model)
        if filter_by:
            count_stmt = count_stmt.where(field == value)

        total_result = await session.exec(count_stmt)
        total = total_result.one()

        select_stmt = select_stmt.offset(offset).limit(limit)

    # Execute final query
    result = await session.exec(select_stmt)
    data = result.all()

    # Serialize manually if fields were specified
    if not serializable:
        field_names = [f.key for f in fields]
        data = [dict(zip(field_names, row)) for row in data]

    # Return paginated response
    if total is not None:
        metadata = gen_offset_pagination_metadata(offset, limit, total, location)
        return PaginationResponse(data=data, pagination=metadata)

    return data

async def save(
    session: AsyncSession,
    data: Union[SQLModel, List[SQLModel]],
    refresh: bool = False
) -> Union[SQLModel, List[SQLModel], None]:
    """
    Save one or more SQLModel instances asynchronously.

    Parameters:
    - session: Active AsyncSession instance.
    - data: A single model or a list of models.
    - refresh: If True, will refresh and return the saved data.

    Returns:
    - Refreshed data if `refresh` is True, otherwise None.
    """
    is_bulk = isinstance(data, list)

    if is_bulk:
        session.add_all(data)
    else:
        session.add(data)

    await session.commit()

    if not refresh:
        return None

    if is_bulk:
        model_cls = type(data[0])
        pks = [getattr(item, "pk", None) for item in data if getattr(item, "pk", None) is not None]

        if not pks:
            return []

        result = await session.exec(select(model_cls).where(model_cls.pk.in_(pks)))
        return result.all()

    await session.refresh(data)
    return data


async def update_object(
    session: AsyncSession,
    data: dict,
    obj: SQLModel
) -> Optional[SQLModel]:
    """
    Update fields of an existing SQLModel object asynchronously.

    Parameters:
    - session: AsyncSession instance.
    - data: Dictionary of attributes to update.
    - obj: The SQLModel instance to update.

    Returns:
    - The refreshed updated object, or None if update fails.
    """
    try:
        for key, value in data.items():
            setattr(obj, key, value)
        updated_obj = await save(session, obj, refresh=True)
        return updated_obj
    except AttributeError:
        # Could log the error here if needed
        return None


async def delete(
    session: AsyncSession,
    data: Union[SQLModel, List[SQLModel]]
) -> None:
    """
    Delete a single instance or a list of instances asynchronously.

    This method loops through each object for deletion to respect ORM events.
    NOTE: On bulk deletion, consider using `session.exec()` for performance.
    """
    if isinstance(data, list):
        for item in data:
            await session.delete(item)
    else:
        await session.delete(data)
    
    await session.commit()

async def count_items(
    session: AsyncSession,
    model: Optional[SQLModel] = None,
    where_attr: Optional[InstrumentedAttribute] = None,
    where_value: Optional[Any] = None,
) -> int:
    """
    Counts the number of records in the database.
    - If `where_attr` and `where_value` are provided, count with filter.
    - Otherwise, count all records of the model.
    """
    if where_attr is not None and where_value is not None:
        model_class = where_attr.class_
        count_stmt = select(func.count()).select_from(model_class).where(where_attr == where_value)
    elif model is not None:
        count_stmt = select(func.count()).select_from(model)
    else:
        raise ValueError("Either model or where_attr and where_value must be provided")

    result = await session.exec(count_stmt)
    return result.one()

