from fastapi import APIRouter
from app.database import validate_policy

router = APIRouter(prefix="/api/policy", tags=["Policy Validation"])


@router.post("/validate")
async def validate_policy_endpoint(data: dict):
    source = data.get("source", {})
    destination = data.get("destination", {})
    application = data.get("application", "")
    environment = data.get("environment", "Production")
    return validate_policy(source, destination, application, environment)
