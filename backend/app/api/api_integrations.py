"""
API Integrations Router
CRUD endpoints for managing API integrations
File: backend/app/api/api_integrations.py
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from datetime import datetime
import json
import uuid
import httpx

from app.api.auth import get_current_user

router = APIRouter()

DATA_FILE = Path("./data/api_integrations.json")


# ============================================
# MODELS
# ============================================

class APIIntegrationCreate(BaseModel):
    name: str
    method: str = "GET"
    url: str
    category: str = "general"
    trigger_keywords: Union[List[str], str] = []
    params: List[Dict[str, Any]] = []
    headers: Union[Dict[str, str], List[Dict[str, str]]] = {}
    body_template: str = ""
    response_template: str = ""
    is_active: bool = True

    @field_validator('trigger_keywords', mode='before')
    @classmethod
    def parse_keywords(cls, v):
        if isinstance(v, str):
            return [k.strip() for k in v.split(',') if k.strip()]
        return v

    @field_validator('headers', mode='before')
    @classmethod
    def parse_headers(cls, v):
        if isinstance(v, list):
            return {item['key']: item.get('value', '') for item in v if item.get('key')}
        return v or {}


class APIIntegrationUpdate(BaseModel):
    name: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    trigger_keywords: Optional[Union[List[str], str]] = None
    params: Optional[List[Dict[str, Any]]] = None
    headers: Optional[Union[Dict[str, str], List[Dict[str, str]]]] = None
    body_template: Optional[str] = None
    response_template: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('trigger_keywords', mode='before')
    @classmethod
    def parse_keywords(cls, v):
        if isinstance(v, str):
            return [k.strip() for k in v.split(',') if k.strip()]
        return v

    @field_validator('headers', mode='before')
    @classmethod
    def parse_headers(cls, v):
        if isinstance(v, list):
            return {item['key']: item.get('value', '') for item in v if item.get('key')}
        return v


# ============================================
# HELPERS
# ============================================

def load_integrations() -> List[Dict]:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except:
            return []
    return []


def save_integrations(integrations: List[Dict]):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(integrations, f, indent=2, ensure_ascii=False)


# ============================================
# ENDPOINTS
# ============================================

@router.get("/")
async def list_integrations(current_user: Dict = Depends(get_current_user)) -> List[Dict]:
    return load_integrations()


@router.get("/{integration_id}")
async def get_integration(integration_id: str, current_user: Dict = Depends(get_current_user)) -> Dict:
    for item in load_integrations():
        if item.get("id") == integration_id:
            return item
    raise HTTPException(status_code=404, detail="Not found")


@router.post("/")
async def create_integration(data: APIIntegrationCreate, current_user: Dict = Depends(get_current_user)) -> Dict:
    integrations = load_integrations()

    new_item = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "method": data.method.upper(),
        "url": data.url,
        "category": data.category,
        "trigger_keywords": data.trigger_keywords,
        "params": data.params,
        "headers": data.headers,
        "body_template": data.body_template,
        "response_template": data.response_template,
        "is_active": data.is_active,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    integrations.append(new_item)
    save_integrations(integrations)
    print(f"✅ Created: {data.name}")
    return new_item


@router.put("/{integration_id}")
async def update_integration(integration_id: str, data: APIIntegrationUpdate, current_user: Dict = Depends(get_current_user)) -> Dict:
    integrations = load_integrations()

    for i, item in enumerate(integrations):
        if item.get("id") == integration_id:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    item[key] = value
            item["updated_at"] = datetime.now().isoformat()
            integrations[i] = item
            save_integrations(integrations)
            return item

    raise HTTPException(status_code=404, detail="Not found")


@router.delete("/{integration_id}")
async def delete_integration(integration_id: str, current_user: Dict = Depends(get_current_user)) -> Dict:
    integrations = load_integrations()

    for i, item in enumerate(integrations):
        if item.get("id") == integration_id:
            deleted = integrations.pop(i)
            save_integrations(integrations)
            return {"success": True}

    raise HTTPException(status_code=404, detail="Not found")


@router.post("/{integration_id}/toggle")
async def toggle_integration(integration_id: str, current_user: Dict = Depends(get_current_user)) -> Dict:
    integrations = load_integrations()

    for i, item in enumerate(integrations):
        if item.get("id") == integration_id:
            item["is_active"] = not item.get("is_active", True)
            item["updated_at"] = datetime.now().isoformat()
            integrations[i] = item
            save_integrations(integrations)
            return {"success": True, "is_active": item["is_active"]}

    raise HTTPException(status_code=404, detail="Not found")


@router.post("/{integration_id}/test")
async def test_integration(integration_id: str, current_user: Dict = Depends(get_current_user)) -> Dict:
    integrations = load_integrations()

    api = None
    for item in integrations:
        if item.get("id") == integration_id:
            api = item
            break

    if not api:
        raise HTTPException(status_code=404, detail="Not found")

    # Test with sample param
    url = api.get("url", "").replace("{no_pel}", "07600026")

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.request(
                method=api.get("method", "GET"),
                url=url,
                headers=api.get("headers", {})
            )
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "url": url,
                "preview": response.text[:300] if response.text else None
            }
    except Exception as e:
        return {"success": False, "error": str(e)}