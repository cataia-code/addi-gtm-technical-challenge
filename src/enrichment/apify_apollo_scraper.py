"""Read-only Apify Apollo organization scraper client."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests


DEFAULT_ACTOR_ID = "coladeu/apollo-organizations-scraper"


@dataclass(frozen=True)
class CompanyProspect:
    name: str
    domain: str | None
    industry: str | None
    country: str | None
    city: str | None
    raw: dict[str, Any]

    def as_llm_context(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "industry": self.industry,
            "country": self.country,
            "city": self.city,
        }


def hogar_colombia_input() -> dict[str, Any]:
    """Input confirmed from Apify actor docs: org filters + page controls."""

    return {
        "page": 1,
        "number_of_pages_to_scrape": 1,
        "organization_locations": ["Colombia"],
        "organization_industries": ["retail", "furniture", "home decor", "consumer goods"],
    }


def run_apollo_organizations_scraper(
    run_input: dict[str, Any],
    *,
    actor_id: str = DEFAULT_ACTOR_ID,
    api_token: str | None = None,
    timeout: int = 180,
    max_results: int = 3,
) -> list[CompanyProspect]:
    token = api_token or os.environ.get("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN is required")

    encoded_actor_id = quote(actor_id, safe="")
    url = f"https://api.apify.com/v2/acts/{encoded_actor_id}/run-sync-get-dataset-items"
    response = requests.post(url, params={"token": token}, json=run_input, timeout=timeout)
    response.raise_for_status()
    items = response.json()
    return [normalize_company(item) for item in items[:max_results] if normalize_company(item).name]


def normalize_company(item: dict[str, Any]) -> CompanyProspect:
    organization = item.get("organization") if isinstance(item.get("organization"), dict) else {}
    name = first_present(item, organization, keys=("name", "organization_name", "company_name"))
    domain = first_present(item, organization, keys=("domain", "website_url", "website", "primary_domain"))
    industry = first_present(item, organization, keys=("industry", "industry_name", "industries"))
    country = first_present(item, organization, keys=("country", "country_name", "organization_country"))
    city = first_present(item, organization, keys=("city", "organization_city"))
    if isinstance(industry, list):
        industry = ", ".join(str(value) for value in industry[:3])
    return CompanyProspect(
        name=str(name or "").strip(),
        domain=str(domain).strip() if domain else None,
        industry=str(industry).strip() if industry else None,
        country=str(country).strip() if country else None,
        city=str(city).strip() if city else None,
        raw=item,
    )


def first_present(*dicts: dict[str, Any], keys: tuple[str, ...]):
    for data in dicts:
        if not isinstance(data, dict):
            continue
        for key in keys:
            value = data.get(key)
            if value not in (None, "", []):
                return value
    return None
