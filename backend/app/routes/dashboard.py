from fastapi import APIRouter

import app.store as store

from app.extraction.comparison_engine import (
    compare_companies
)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data():

    companies = list(
        store.uploaded_companies
    )

    analyst_insights = ""

    # Generate dynamic comparison insight
    if len(companies) >= 2:

        analyst_insights = compare_companies(

            companies[0],

            companies[1]

        )

    return {

        "companies": companies,

        "financial_data":
        store.structured_financial_data,

        "analyst_insights":
        analyst_insights
    }