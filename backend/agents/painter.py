"""
Painter agent implementation with specialized tools using Strands Agents framework.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from backend.config import settings


# Tool Input Models
class PaintInteriorWallsInput(BaseModel):
    """Input for painting interior walls."""

    area_sq_ft: float = Field(description="Area to paint in square feet")
    coat_count: int = Field(description="Number of coats")
    color: str = Field(description="Paint color")


class PaintExteriorInput(BaseModel):
    """Input for painting exterior."""

    area_sq_ft: float = Field(description="Area to paint in square feet")
    surface_type: str = Field(description="Surface type (wood, vinyl, stucco, brick)")


class PrimeSurfacesInput(BaseModel):
    """Input for priming surfaces."""

    area_sq_ft: float = Field(description="Area to prime in square feet")
    surface_type: str = Field(description="Type of surface")


class RemoveOldPaintInput(BaseModel):
    """Input for removing old paint."""

    area_sq_ft: float = Field(description="Area to strip in square feet")
    method: str = Field(description="Removal method (scraping, chemical stripper, heat gun)")


class RefinishCabinetsInput(BaseModel):
    """Input for refinishing cabinets."""

    cabinet_count: int = Field(description="Number of cabinets to refinish")
    finish_type: str = Field(description="Finish type (paint, stain, varnish)")


class ApplyWallpaperInput(BaseModel):
    """Input for applying wallpaper."""

    area_sq_ft: float = Field(description="Area to cover in square feet")
    wallpaper_type: str = Field(description="Type of wallpaper")


# Tool Implementations
@tool
def paint_interior_walls(input: PaintInteriorWallsInput) -> dict:
    """Paint interior walls and ceilings."""
    gallons_needed = (input.area_sq_ft * input.coat_count) / 350
    return {
        "status": "completed",
        "area_painted": input.area_sq_ft,
        "coats_applied": input.coat_count,
        "color": input.color,
        "paint_used_gallons": round(gallons_needed, 1),
        "materials_used": [
            f"{round(gallons_needed, 1)} gallons {input.color} paint",
            "roller and brushes",
            "painter's tape",
        ],
        "details": f"Painted {input.area_sq_ft} sq ft interior walls with {input.coat_count} coats of {input.color}",
    }


@tool
def paint_exterior(input: PaintExteriorInput) -> dict:
    """Paint exterior siding."""
    gallons_needed = input.area_sq_ft / 300
    return {
        "status": "completed",
        "area_painted": input.area_sq_ft,
        "surface_type": input.surface_type,
        "paint_used_gallons": round(gallons_needed, 1),
        "materials_used": [
            f"{round(gallons_needed, 1)} gallons exterior paint",
            "primer (if needed)",
            "application tools",
        ],
        "details": f"Painted {input.area_sq_ft} sq ft {input.surface_type} exterior",
    }


@tool
def prime_surfaces(input: PrimeSurfacesInput) -> dict:
    """Prime surfaces before painting."""
    gallons_needed = input.area_sq_ft / 400
    return {
        "status": "completed",
        "area_primed": input.area_sq_ft,
        "surface_type": input.surface_type,
        "primer_used_gallons": round(gallons_needed, 1),
        "materials_used": [f"{round(gallons_needed, 1)} gallons primer"],
        "details": f"Primed {input.area_sq_ft} sq ft of {input.surface_type}",
    }


@tool
def remove_old_paint(input: RemoveOldPaintInput) -> dict:
    """Remove old paint from surfaces."""
    return {
        "status": "completed",
        "area_stripped": input.area_sq_ft,
        "method": input.method,
        "materials_used": [f"{input.method} tools/chemicals"],
        "details": f"Removed old paint from {input.area_sq_ft} sq ft using {input.method}",
    }


@tool
def refinish_cabinets(input: RefinishCabinetsInput) -> dict:
    """Refinish cabinets with paint or stain."""
    return {
        "status": "completed",
        "cabinets_refinished": input.cabinet_count,
        "finish_type": input.finish_type,
        "materials_used": [
            f"{input.finish_type} finish",
            "sandpaper",
            "application tools",
        ],
        "details": f"Refinished {input.cabinet_count} cabinets with {input.finish_type}",
    }


@tool
def apply_wallpaper(input: ApplyWallpaperInput) -> dict:
    """Apply wallpaper to walls."""
    rolls_needed = input.area_sq_ft / 28
    return {
        "status": "completed",
        "area_covered": input.area_sq_ft,
        "wallpaper_type": input.wallpaper_type,
        "rolls_used": round(rolls_needed),
        "materials_used": [
            f"{round(rolls_needed)} rolls {input.wallpaper_type} wallpaper",
            "wallpaper paste",
            "application tools",
        ],
        "details": f"Applied {input.area_sq_ft} sq ft of {input.wallpaper_type} wallpaper",
    }


def create_painter_agent() -> Agent:
    """Create and configure the Painter agent with AWS Bedrock."""
    import boto3

    # Create boto3 session with AWS credentials
    session_kwargs = {
        "region_name": settings.aws_region,
    }

    if settings.aws_profile:
        session_kwargs["profile_name"] = settings.aws_profile
    elif settings.aws_access_key_id and settings.aws_secret_access_key:
        session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            session_kwargs["aws_session_token"] = settings.aws_session_token

    boto_session = boto3.Session(**session_kwargs)

    # Configure Bedrock model
    model = BedrockModel(
        model_id=settings.default_model,
        boto_session=boto_session,
    )

    system_prompt = """You are an expert Painter agent specializing in interior and exterior painting.

Your responsibilities include:
- Painting interior walls and ceilings
- Painting exterior siding
- Priming surfaces
- Removing old paint
- Refinishing cabinets
- Applying wallpaper

Ensure proper surface preparation, even coats, and clean lines."""

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            paint_interior_walls,
            paint_exterior,
            prime_surfaces,
            remove_old_paint,
            refinish_cabinets,
            apply_wallpaper,
        ],
    )

    return agent
