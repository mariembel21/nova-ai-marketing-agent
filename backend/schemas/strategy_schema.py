from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrategyRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "business_name": "TechStart AI",
                "business_description": "Plateforme d'automatisation marketing alimentée par l'IA.",
                "product_service": "Logiciel d'automatisation marketing",
                "industry": "SaaS / Marketing Technology",
                "target_audience": "Responsables marketing de PME et ETI",
                "additional_context": "Priorité au ROI et à une exécution rapide.",
            }
        },
    )

    business_name: str = Field(..., min_length=2, description="Nom de l'entreprise")
    business_description: str = Field(..., min_length=10, description="Description de l'entreprise")
    product_service: str = Field(..., min_length=2, description="Produit ou service à promouvoir")
    industry: str = Field(..., min_length=2, description="Secteur d'activité")
    target_audience: str = Field(..., min_length=2, description="Audience cible")
    additional_context: Optional[str] = Field(default=None, description="Contexte complémentaire")

class ObjectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objection: str = Field(..., description="Objection client")
    response: str = Field(..., description="Réponse à l'objection")


class StrategicPositioning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    market_analysis: str = Field(..., description="Analyse du marché")
    main_pain_point: str = Field(..., description="Problème principal résolu")
    value_proposition: str = Field(..., description="Proposition de valeur")
    marketing_angle: str = Field(..., description="Angle marketing dominant")
    personas: List[str] = Field(..., description="Personas cibles")


class OfferAndMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offer: str = Field(..., description="Offre proposée")
    headline: str = Field(..., description="Promesse principale")
    key_messages: List[str] = Field(..., description="Messages clés de vente")
    objections: List[ObjectionResponse] = Field(..., description="Objections et réponses")
    proof_elements: List[str] = Field(..., description="Éléments de preuve")


class AcquisitionChannel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str = Field(..., description="Canal d'acquisition")
    why: str = Field(..., description="Pourquoi ce canal est pertinent")
    content: str = Field(..., description="Type de contenu à produire")
    frequency: str = Field(..., description="Fréquence recommandée")


class ConversionFunnel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    funnel: str = Field(..., description="Tunnel de conversion complet")
    lead_magnet: str = Field(..., description="Lead magnet recommandé")
    email_sequence: str = Field(..., description="Séquence email")
    cta: List[str] = Field(..., description="Appels à l'action")
    conversion_optimization: str = Field(..., description="Optimisations de conversion")


class ActionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, serialize_by_alias=True)

    thirty_days: List[str] = Field(..., alias="30_days", description="Plan à 30 jours")
    sixty_days: List[str] = Field(..., alias="60_days", description="Plan à 60 jours")
    ninety_days: List[str] = Field(..., alias="90_days", description="Plan à 90 jours")


class KPIs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acquisition: List[str] = Field(..., description="KPIs d'acquisition")
    conversion: List[str] = Field(..., description="KPIs de conversion")
    revenue: List[str] = Field(..., description="KPIs de chiffre d'affaires")
    benchmarks: List[str] = Field(..., description="Benchmarks cibles")
    optimization_loops: List[str] = Field(..., description="Boucles d'optimisation")


class StrategyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, serialize_by_alias=True)

    strategy_summary: str = Field(..., description="Résumé stratégique")
    strategic_positioning: StrategicPositioning = Field(..., description="Positionnement stratégique")
    offer_and_message: OfferAndMessage = Field(..., description="Offre et message")
    acquisition_strategy: List[AcquisitionChannel] = Field(..., description="Stratégie d'acquisition")
    conversion_funnel: ConversionFunnel = Field(..., description="Tunnel de conversion")
    action_plan: ActionPlan = Field(..., description="Plan d'action")
    kpis: KPIs = Field(..., description="Indicateurs de performance")
    differentiating_ideas: List[str] = Field(..., description="Idées différenciantes")


class StrategyRevisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_request: StrategyRequest = Field(..., description="Requête d'origine")
    previous_strategy: StrategyResponse = Field(..., description="Stratégie précédente")
    client_feedback: str = Field(..., min_length=1, description="Retour client à appliquer")
