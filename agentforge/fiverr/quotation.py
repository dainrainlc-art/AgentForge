"""
Fiverr Quotation System - Auto-generate professional quotes
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum

from agentforge.llm import QianfanClient
from agentforge.memory import MemoryStore


class ServiceCategory(str, Enum):
    DESIGN = "design"
    DEVELOPMENT = "development"
    WRITING = "writing"
    MARKETING = "marketing"
    VIDEO = "video"
    MUSIC = "music"
    OTHER = "other"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class QuotationItem(BaseModel):
    """Individual quotation item"""
    description: str
    quantity: int = 1
    unit_price: float
    total: float
    notes: Optional[str] = None


class Quotation(BaseModel):
    """Complete quotation model"""
    id: str
    order_id: Optional[str] = None
    buyer_username: str
    project_title: str
    category: ServiceCategory
    complexity: ComplexityLevel
    items: List[QuotationItem]
    subtotal: float
    discount: float = 0.0
    tax: float = 0.0
    total: float
    delivery_days: int
    revision_count: int = 2
    valid_until: datetime
    created_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
    terms: Optional[str] = None


class QuotationGenerator:
    """AI-powered quotation generator"""
    
    BASE_RATES = {
        ServiceCategory.DESIGN: {"simple": 50, "moderate": 100, "complex": 200, "expert": 400},
        ServiceCategory.DEVELOPMENT: {"simple": 100, "moderate": 200, "complex": 400, "expert": 800},
        ServiceCategory.WRITING: {"simple": 25, "moderate": 50, "complex": 100, "expert": 200},
        ServiceCategory.MARKETING: {"simple": 75, "moderate": 150, "complex": 300, "expert": 600},
        ServiceCategory.VIDEO: {"simple": 100, "moderate": 250, "complex": 500, "expert": 1000},
        ServiceCategory.MUSIC: {"simple": 50, "moderate": 100, "complex": 200, "expert": 400},
        ServiceCategory.OTHER: {"simple": 50, "moderate": 100, "complex": 200, "expert": 400},
    }
    
    DELIVERY_MULTIPLIERS = {
        "rush": 1.5,
        "standard": 1.0,
        "relaxed": 0.85,
    }
    
    def __init__(
        self,
        llm_client: Optional[QianfanClient] = None,
        memory_store: Optional[MemoryStore] = None
    ):
        self.llm_client = llm_client or QianfanClient()
        self.memory_store = memory_store or MemoryStore()
        self._quotation_counter = 0
    
    def _generate_quotation_id(self) -> str:
        self._quotation_counter += 1
        return f"QUO-{datetime.now().strftime('%Y%m%d')}-{self._quotation_counter:04d}"
    
    async def analyze_request(
        self,
        request_text: str,
        buyer_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze project request using AI"""
        
        prompt = f"""Analyze this Fiverr project request and extract key information:

Request: {request_text}

Please provide a JSON response with:
1. "category": one of design, development, writing, marketing, video, music, other
2. "complexity": one of simple, moderate, complex, expert
3. "estimated_hours": estimated work hours
4. "key_deliverables": list of main deliverables
5. "potential_challenges": list of potential challenges
6. "suggested_timeline": suggested delivery timeline in days

Respond only with valid JSON."""

        try:
            response = await self.llm_client.chat(message=prompt)
            
            import json
            analysis = json.loads(response)
            
            category_str = analysis.get("category", "other").lower()
            complexity_str = analysis.get("complexity", "moderate").lower()
            
            try:
                analysis["category"] = ServiceCategory(category_str)
            except ValueError:
                analysis["category"] = ServiceCategory.OTHER
            
            try:
                analysis["complexity"] = ComplexityLevel(complexity_str)
            except ValueError:
                analysis["complexity"] = ComplexityLevel.MODERATE
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze request: {e}")
            return {
                "category": ServiceCategory.OTHER,
                "complexity": ComplexityLevel.MODERATE,
                "estimated_hours": 10,
                "key_deliverables": ["Project deliverable"],
                "potential_challenges": [],
                "suggested_timeline": 7
            }
    
    def calculate_base_price(
        self,
        category: ServiceCategory,
        complexity: ComplexityLevel,
        estimated_hours: float = 10
    ) -> float:
        """Calculate base price for the project"""
        
        base_rate = self.BASE_RATES.get(category, self.BASE_RATES[ServiceCategory.OTHER])
        hourly_rate = base_rate.get(complexity.value, base_rate["moderate"])
        
        return hourly_rate * estimated_hours
    
    def estimate_delivery_days(
        self,
        complexity: ComplexityLevel,
        estimated_hours: float,
        urgency: str = "standard"
    ) -> int:
        """Estimate delivery timeline"""
        
        base_days = {
            ComplexityLevel.SIMPLE: max(1, int(estimated_hours / 8)),
            ComplexityLevel.MODERATE: max(3, int(estimated_hours / 6)),
            ComplexityLevel.COMPLEX: max(5, int(estimated_hours / 4)),
            ComplexityLevel.EXPERT: max(7, int(estimated_hours / 3)),
        }
        
        days = base_days.get(complexity, 7)
        
        if urgency == "rush":
            days = max(1, int(days * 0.6))
        elif urgency == "relaxed":
            days = int(days * 1.5)
        
        return days
    
    async def generate_quotation(
        self,
        request_text: str,
        buyer_username: str,
        project_title: str,
        urgency: str = "standard",
        discount_percent: float = 0.0,
        custom_requirements: Optional[List[str]] = None
    ) -> Quotation:
        """Generate complete quotation"""
        
        logger.info(f"Generating quotation for buyer: {buyer_username}")
        
        analysis = await self.analyze_request(request_text)
        
        category = analysis["category"]
        complexity = analysis["complexity"]
        estimated_hours = analysis.get("estimated_hours", 10)
        deliverables = analysis.get("key_deliverables", ["Project deliverable"])
        
        base_price = self.calculate_base_price(category, complexity, estimated_hours)
        
        urgency_multiplier = self.DELIVERY_MULTIPLIERS.get(urgency, 1.0)
        adjusted_price = base_price * urgency_multiplier
        
        delivery_days = self.estimate_delivery_days(complexity, estimated_hours, urgency)
        
        items = []
        for i, deliverable in enumerate(deliverables):
            item_price = adjusted_price / len(deliverables)
            items.append(QuotationItem(
                description=deliverable,
                quantity=1,
                unit_price=round(item_price, 2),
                total=round(item_price, 2)
            ))
        
        if custom_requirements:
            for req in custom_requirements:
                items.append(QuotationItem(
                    description=f"Custom: {req}",
                    quantity=1,
                    unit_price=50.0,
                    total=50.0
                ))
        
        subtotal = sum(item.total for item in items)
        discount = subtotal * (discount_percent / 100)
        total = subtotal - discount
        
        valid_until = datetime.now()
        from datetime import timedelta
        valid_until = valid_until + timedelta(days=7)
        
        quotation = Quotation(
            id=self._generate_quotation_id(),
            buyer_username=buyer_username,
            project_title=project_title,
            category=category,
            complexity=complexity,
            items=items,
            subtotal=round(subtotal, 2),
            discount=round(discount, 2),
            total=round(total, 2),
            delivery_days=delivery_days,
            valid_until=valid_until,
            terms=self._generate_terms(delivery_days)
        )
        
        await self._save_quotation(quotation)
        
        logger.info(f"Generated quotation {quotation.id}: ${quotation.total}")
        
        return quotation
    
    def _generate_terms(self, delivery_days: int) -> str:
        """Generate standard terms"""
        return f"""Terms & Conditions:
1. Delivery within {delivery_days} business days after order confirmation
2. Includes 2 free revisions
3. 50% payment upfront, 50% upon delivery
4. Source files included upon final payment
5. 30-day support after delivery"""
    
    async def _save_quotation(self, quotation: Quotation) -> None:
        """Save quotation to memory"""
        if self.memory_store:
            await self.memory_store.store_memory(
                content=f"Quotation {quotation.id} for {quotation.buyer_username}: ${quotation.total}",
                memory_type="quotation",
                metadata=quotation.model_dump()
            )
    
    async def get_quotation_history(
        self,
        buyer_username: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get quotation history"""
        if self.memory_store:
            memories = await self.memory_store.search_memories(
                query=f"quotation {buyer_username or ''}",
                limit=limit
            )
            return [m for m in memories if m.get("memory_type") == "quotation"]
        return []


quotation_generator = QuotationGenerator()
