from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ValidationIssue(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    slide_number: int = Field(
        ...,
        description="Numéro de la slide concernée"
    )

    field: str = Field(
        ...,
        description="Champ ayant échoué à la validation"
    )

    reason: str = Field(
        ...,
        description="Raison de l'échec"
    )


# =========================
# REQUEST SCHEMA
# =========================

class PresentationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "topic": "Comment l'intelligence artificielle transforme le marketing digital",
                "target": "Responsables marketing de PME et startups",
                "objective": "Générer des leads",
                "technical_level": "Intermédiaire",

                "business_name": "TechStart AI",
                "business_description": "Plateforme SaaS d'automatisation marketing basée sur l'intelligence artificielle.",
                "industry": "SaaS / Marketing Technology",
                "target_audience": "Responsables marketing, startups et PME",
                "additional_context": "Priorité à l'acquisition rapide et à l'amélioration du ROI marketing."
            }
        }
    )

    # Presentation variables

    topic: str = Field(
        ...,
        min_length=3,
        description="Sujet principal de la présentation"
    )

    target: str = Field(
        ...,
        min_length=2,
        description="Cible de la présentation"
    )

    objective: str = Field(
        ...,
        min_length=2,
        description="Objectif principal de la présentation (engagement, leads, notoriété...)"
    )

    technical_level: str = Field(
        ...,
        min_length=2,
        description="Niveau de technicité attendu (Simple, Intermédiaire, Expert)"
    )


    # Company context

    business_name: str = Field(
        ...,
        min_length=2,
        description="Nom de l'entreprise"
    )

    business_description: str = Field(
        ...,
        min_length=10,
        description="Description de l'entreprise"
    )

    industry: str = Field(
        ...,
        min_length=2,
        description="Secteur d'activité"
    )

    target_audience: str = Field(
        ...,
        min_length=2,
        description="Audience cible de l'entreprise"
    )

    additional_context: Optional[str] = Field(
        default=None,
        description="Informations complémentaires sur l'entreprise ou ses objectifs"
    )


# =========================
# RESPONSE SCHEMA
# =========================

class Slide(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    slide_number: int = Field(
        ...,
        description="Numéro de la slide"
    )

    slide_role: str = Field(
        ...,
        description="Rôle de la slide dans la structure de la présentation"
    )

    title: str = Field(
        ...,
        description="Titre principal de la slide"
    )

    bullet_points: List[str] = Field(
        ...,
        description="Points clés affichés sur la slide"
    )

    visual_suggestion: str = Field(
        ...,
        description="Suggestion visuelle pour illustrer la slide (image, icône, schéma...)"
    )


class PresentationResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    presentation_title: str = Field(
        ...,
        description="Titre global de la présentation"
    )

    presentation_summary: str = Field(
        ...,
        description="Résumé stratégique de la présentation"
    )

    target: str = Field(
        ...,
        description="Audience visée par la présentation"
    )

    objective: str = Field(
        ...,
        description="Objectif principal de la présentation"
    )

    slides: List[Slide] = Field(
        ...,
        description="Liste complète des slides générées"
    )

    validation_warnings: List[ValidationIssue] = Field(
        default_factory=list,
        description="Avertissements de validation conservés après les tentatives de correction"
    )