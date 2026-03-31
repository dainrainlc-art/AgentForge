"""
Fiverr Pricing Advisor - AI-powered pricing suggestions
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum

from agentforge.llm import QianfanClient
from agentforge.memory import MemoryStore
from agentforge.fiverr.quotation import ServiceCategory, ComplexityLevel


class PricingStrategy(str, Enum):
    COMPETITIVE = "competitive"
    PREMIUM = "premium"
    VALUE = "value"
    PENETRATION = "penetration"


class MarketData(BaseModel):
    """Market pricing data"""
    category: ServiceCategory
    min_price: float
    max_price: float
    avg_price: float
    median_price: float
    sample_size: int
    last_updated: datetime


class PricingFactor(BaseModel):
    """Pricing factor"""
    name: str
    impact: float
    description: str


class PricingSuggestion(BaseModel):
    """Pricing suggestion"""
    suggested_price: float
    price_range_min: float
    price_range_max: float
    confidence: float
    strategy: PricingStrategy
    factors: List[PricingFactor]
    market_comparison: str
    recommendations: List[str]
    created_at: datetime = Field(default_factory=datetime.now)


class PricingAdvisor:
    """AI-powered pricing advisor"""
    
    MARKET_DATA = {
        ServiceCategory.DESIGN: {
            "min": 25, "max": 500, "avg": 150, "median": 120
        },
        ServiceCategory.DEVELOPMENT: {
            "min": 50, "max": 2000, "avg": 400, "median": 300
        },
        ServiceCategory.WRITING: {
            "min": 10, "max": 300, "avg": 75, "median": 50
        },
        ServiceCategory.MARKETING: {
            "min": 30, "max": 800, "avg": 200, "median": 150
        },
        ServiceCategory.VIDEO: {
            "min": 50, "max": 3000, "avg": 500, "median": 350
        },
        ServiceCategory.MUSIC: {
            "min": 25, "max": 1000, "avg": 200, "median": 150
        },
        ServiceCategory.OTHER: {
            "min": 20, "max": 500, "avg": 100, "median": 80
        },
    }
    
    COMPLEXITY_MULTIPLIERS = {
        ComplexityLevel.SIMPLE: 0.7,
        ComplexityLevel.MODERATE: 1.0,
        ComplexityLevel.COMPLEX: 1.5,
        ComplexityLevel.EXPERT: 2.2,
    }
    
    STRATEGY_ADJUSTMENTS = {
        PricingStrategy.COMPETITIVE: 0.9,
        PricingStrategy.PREMIUM: 1.3,
        PricingStrategy.VALUE: 1.0,
        PricingStrategy.PENETRATION: 0.75,
    }
    
    def __init__(
        self,
        llm_client: Optional[QianfanClient] = None,
        memory_store: Optional[MemoryStore] = None
    ):
        self.llm_client = llm_client or QianfanClient()
        self.memory_store = memory_store or MemoryStore()
        self._price_history: List[Dict[str, Any]] = []
    
    async def analyze_market(
        self,
        category: ServiceCategory,
        keywords: Optional[List[str]] = None
    ) -> MarketData:
        """Analyze market pricing for a category"""
        
        base_data = self.MARKET_DATA.get(category, self.MARKET_DATA[ServiceCategory.OTHER])
        
        market_data = MarketData(
            category=category,
            min_price=base_data["min"],
            max_price=base_data["max"],
            avg_price=base_data["avg"],
            median_price=base_data["median"],
            sample_size=1000,
            last_updated=datetime.now()
        )
        
        return market_data
    
    async def calculate_pricing_factors(
        self,
        category: ServiceCategory,
        complexity: ComplexityLevel,
        estimated_hours: float,
        urgency: str = "standard",
        buyer_history: Optional[Dict[str, Any]] = None,
        project_requirements: Optional[List[str]] = None
    ) -> List[PricingFactor]:
        """Calculate pricing factors"""
        
        factors = []
        
        factors.append(PricingFactor(
            name="Complexity",
            impact=self.COMPLEXITY_MULTIPLIERS[complexity],
            description=f"Project complexity: {complexity.value}"
        ))
        
        urgency_impact = {
            "rush": 1.5,
            "standard": 1.0,
            "relaxed": 0.85,
        }
        factors.append(PricingFactor(
            name="Urgency",
            impact=urgency_impact.get(urgency, 1.0),
            description=f"Delivery urgency: {urgency}"
        ))
        
        hours_factor = min(estimated_hours / 10, 2.0)
        factors.append(PricingFactor(
            name="Scope",
            impact=hours_factor,
            description=f"Estimated {estimated_hours} hours of work"
        ))
        
        if buyer_history:
            repeat_factor = 1.1 if buyer_history.get("is_repeat", False) else 1.0
            factors.append(PricingFactor(
                name="Client Relationship",
                impact=repeat_factor,
                description="Repeat client discount" if repeat_factor < 1 else "New client premium"
            ))
        
        if project_requirements:
            req_count = len(project_requirements)
            req_factor = 1 + (req_count * 0.05)
            factors.append(PricingFactor(
                name="Requirements",
                impact=min(req_factor, 1.5),
                description=f"{req_count} specific requirements"
            ))
        
        return factors
    
    async def suggest_price(
        self,
        category: ServiceCategory,
        complexity: ComplexityLevel,
        estimated_hours: float,
        strategy: PricingStrategy = PricingStrategy.VALUE,
        urgency: str = "standard",
        buyer_history: Optional[Dict[str, Any]] = None,
        project_requirements: Optional[List[str]] = None
    ) -> PricingSuggestion:
        """Generate pricing suggestion"""
        
        logger.info(f"Generating pricing suggestion for {category.value} - {complexity.value}")
        
        market_data = await self.analyze_market(category)
        
        factors = await self.calculate_pricing_factors(
            category=category,
            complexity=complexity,
            estimated_hours=estimated_hours,
            urgency=urgency,
            buyer_history=buyer_history,
            project_requirements=project_requirements
        )
        
        base_price = market_data.median_price
        
        total_impact = 1.0
        for factor in factors:
            total_impact *= factor.impact
        
        strategy_adjustment = self.STRATEGY_ADJUSTMENTS[strategy]
        
        suggested_price = base_price * total_impact * strategy_adjustment
        
        suggested_price = round(suggested_price, 2)
        
        price_range_min = round(suggested_price * 0.85, 2)
        price_range_max = round(suggested_price * 1.15, 2)
        
        market_comparison = self._generate_market_comparison(
            suggested_price, market_data
        )
        
        recommendations = await self._generate_recommendations(
            suggested_price=suggested_price,
            market_data=market_data,
            factors=factors,
            strategy=strategy
        )
        
        confidence = self._calculate_confidence(factors, market_data)
        
        suggestion = PricingSuggestion(
            suggested_price=suggested_price,
            price_range_min=price_range_min,
            price_range_max=price_range_max,
            confidence=confidence,
            strategy=strategy,
            factors=factors,
            market_comparison=market_comparison,
            recommendations=recommendations
        )
        
        self._price_history.append({
            "category": category.value,
            "complexity": complexity.value,
            "suggested_price": suggested_price,
            "strategy": strategy.value,
            "timestamp": datetime.now().isoformat()
        })
        
        return suggestion
    
    def _generate_market_comparison(
        self,
        price: float,
        market_data: MarketData
    ) -> str:
        """Generate market comparison text"""
        
        if price < market_data.min_price:
            return f"Below market minimum (${market_data.min_price})"
        elif price > market_data.max_price:
            return f"Above market maximum (${market_data.max_price})"
        elif price < market_data.median_price * 0.8:
            return "Below market average - competitive pricing"
        elif price > market_data.median_price * 1.2:
            return "Above market average - premium positioning"
        else:
            return "Within market average range"
    
    async def _generate_recommendations(
        self,
        suggested_price: float,
        market_data: MarketData,
        factors: List[PricingFactor],
        strategy: PricingStrategy
    ) -> List[str]:
        """Generate pricing recommendations"""
        
        recommendations = []
        
        if strategy == PricingStrategy.PENETRATION:
            recommendations.append("Consider offering a discount for first-time buyers")
        
        if suggested_price > market_data.avg_price:
            recommendations.append("Justify premium pricing with portfolio samples")
        
        urgency_factor = next(
            (f for f in factors if f.name == "Urgency"), None
        )
        if urgency_factor and urgency_factor.impact > 1.2:
            recommendations.append("Include rush delivery premium in your quote")
        
        complexity_factor = next(
            (f for f in factors if f.name == "Complexity"), None
        )
        if complexity_factor and complexity_factor.impact > 1.5:
            recommendations.append("Break down complex project into milestones")
        
        recommendations.append("Offer package deals for additional services")
        
        return recommendations[:5]
    
    def _calculate_confidence(
        self,
        factors: List[PricingFactor],
        market_data: MarketData
    ) -> float:
        """Calculate confidence score for pricing suggestion"""
        
        base_confidence = 0.7
        
        if market_data.sample_size > 500:
            base_confidence += 0.1
        
        if len(factors) >= 4:
            base_confidence += 0.1
        
        extreme_factors = sum(1 for f in factors if f.impact > 1.5 or f.impact < 0.8)
        base_confidence -= extreme_factors * 0.05
        
        return min(max(base_confidence, 0.5), 0.95)
    
    async def get_price_history(
        self,
        category: Optional[ServiceCategory] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get pricing history"""
        
        if category:
            return [
                h for h in self._price_history
                if h["category"] == category.value
            ][-limit:]
        
        return self._price_history[-limit:]
    
    async def compare_with_competitors(
        self,
        category: ServiceCategory,
        price: float
    ) -> Dict[str, Any]:
        """Compare price with competitors"""
        
        market_data = await self.analyze_market(category)
        
        percentile = 0
        if price <= market_data.min_price:
            percentile = 0
        elif price >= market_data.max_price:
            percentile = 100
        else:
            price_range = market_data.max_price - market_data.min_price
            price_position = price - market_data.min_price
            percentile = (price_position / price_range) * 100
        
        return {
            "your_price": price,
            "market_min": market_data.min_price,
            "market_max": market_data.max_price,
            "market_avg": market_data.avg_price,
            "market_median": market_data.median_price,
            "percentile": round(percentile, 1),
            "position": self._get_position_label(percentile)
        }
    
    def _get_position_label(self, percentile: float) -> str:
        """Get position label based on percentile"""
        if percentile < 20:
            return "Budget"
        elif percentile < 40:
            return "Competitive"
        elif percentile < 60:
            return "Market Average"
        elif percentile < 80:
            return "Premium"
        else:
            return "Luxury"


pricing_advisor = PricingAdvisor()
