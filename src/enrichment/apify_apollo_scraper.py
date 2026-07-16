"""Read-only Apify Apollo organization scraper client."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests


DEFAULT_ACTOR_ID = "pipelinelabs/lead-scraper-apollo-zoominfo-lusha-ppe"


@dataclass(frozen=True)
class CompanyProspect:
    name: str
    domain: str | None
    industry: str | None
    country: str | None
    city: str | None
    raw: dict[str, Any]
    contact_name: str | None = None
    contact_title: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    linkedin_url: str | None = None

    def as_llm_context(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "industry": self.industry,
            "country": self.country,
            "city": self.city,
            "contact_name": self.contact_name,
            "contact_title": self.contact_title,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "linkedin_url": self.linkedin_url,
        }


def hogar_colombia_input() -> dict[str, Any]:
    """Input confirmed from Pipeline Labs actor docs: contact filters + company filters."""

    return {
        "totalResults": 3,
        "hasEmail": True,
        "emailStatusIncludes": ["verified"],
        "hasPhone": True,
        "personLocationCountryIncludes": ["Colombia"],
        "companyLocationCountryIncludes": ["Colombia"],
        "companyIndustryIncludes": ["Retail", "Furniture", "Consumer Goods"],
        "personTitleIncludes": ["Founder", "CEO", "Director", "Head of Ecommerce", "Ecommerce Manager"],
        "roleMatchMode": "any",
        "companyKeywordIncludes": ["hogar", "muebles", "decoracion", "home"],
        "companyKeywordMode": "broad",
        "resetProgress": False,
        "dontSaveProgress": True,
        "countOnly": False,
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
    prospects = []
    for item in items:
        prospect = normalize_company(item)
        if prospect.name and (prospect.contact_email or prospect.contact_phone):
            prospects.append(prospect)
        if len(prospects) >= max_results:
            break
    return prospects


def normalize_company(item: dict[str, Any]) -> CompanyProspect:
    organization = item.get("organization") if isinstance(item.get("organization"), dict) else {}
    company = item.get("company") if isinstance(item.get("company"), dict) else {}
    name = first_present(organization, company, item, keys=("companyName", "company_name", "organization_name", "name"))
    domain = first_present(organization, company, item, keys=("companyDomain", "domain", "website_url", "website", "primary_domain"))
    industry = first_present(organization, company, item, keys=("companyIndustry", "industry", "industry_name", "industries"))
    country = first_present(organization, company, item, keys=("companyCountry", "country", "country_name", "organization_country"))
    city = first_present(organization, company, item, keys=("companyCity", "city", "organization_city"))
    contact_name = first_present(item, keys=("name", "personName", "fullName", "person_name"))
    contact_title = first_present(item, keys=("title", "personTitle", "jobTitle", "person_title"))
    contact_email = first_present(item, keys=("email", "workEmail", "businessEmail", "personEmail"))
    contact_phone = first_present(item, keys=("phone", "mobilePhone", "phoneNumber", "personPhone"))
    linkedin_url = first_present(item, keys=("linkedinUrl", "linkedin_url", "personLinkedinUrl"))
    if isinstance(industry, list):
        industry = ", ".join(str(value) for value in industry[:3])
    return CompanyProspect(
        name=str(name or "").strip(),
        domain=str(domain).strip() if domain else None,
        industry=str(industry).strip() if industry else None,
        country=str(country).strip() if country else None,
        city=str(city).strip() if city else None,
        contact_name=str(contact_name).strip() if contact_name else None,
        contact_title=str(contact_title).strip() if contact_title else None,
        contact_email=str(contact_email).strip() if contact_email else None,
        contact_phone=str(contact_phone).strip() if contact_phone else None,
        linkedin_url=str(linkedin_url).strip() if linkedin_url else None,
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
