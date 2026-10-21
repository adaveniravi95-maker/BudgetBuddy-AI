from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()


@router.post("/", response_model=schemas.IncomeResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    request: schemas.IncomeCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    income = models.Income(
        user_id=current_user.id,
        amount=request.amount,
        source=request.source,
        description=request.description,
        date=request.date,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


@router.get("/", response_model=schemas.IncomeListResponse)
def list_incomes(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    source: Optional[models.IncomeCategory] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    query = db.query(models.Income).filter(models.Income.user_id == current_user.id)

    if source:
        query = query.filter(models.Income.source == source)
    if start_date:
        query = query.filter(models.Income.date >= start_date)
    if end_date:
        query = query.filter(models.Income.date <= end_date)

    incomes = query.order_by(desc(models.Income.date), desc(models.Income.created_at)).all()
    return schemas.IncomeListResponse(incomes=incomes, total=len(incomes))


@router.get("/{income_id}/", response_model=schemas.IncomeResponse)
def get_income(
    income_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    income = db.query(models.Income).filter(
        models.Income.id == income_id,
        models.Income.user_id == current_user.id,
    ).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    return income


@router.put("/{income_id}/", response_model=schemas.IncomeResponse)
def update_income(
    income_id: int,
    request: schemas.IncomeUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    income = db.query(models.Income).filter(
        models.Income.id == income_id,
        models.Income.user_id == current_user.id,
    ).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(income, field, value)

    db.commit()
    db.refresh(income)
    return income


@router.delete("/{income_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    income = db.query(models.Income).filter(
        models.Income.id == income_id,
        models.Income.user_id == current_user.id,
    ).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")

    db.delete(income)
    db.commit()
    return None
