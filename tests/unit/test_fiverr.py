"""
Tests for Fiverr Automation Module
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from agentforge.fiverr.quotation import (
    QuotationGenerator,
    Quotation,
    QuotationItem,
    ServiceCategory,
    ComplexityLevel
)
from agentforge.fiverr.message_templates import (
    MessageTemplateManager,
    MessageTemplateType,
    MessageTemplate
)
from agentforge.fiverr.order_tracker import (
    OrderTracker,
    OrderTrackerConfig,
    OrderStatus,
    TrackedOrder,
    TrackingEvent
)
from agentforge.fiverr.pricing_advisor import (
    PricingAdvisor,
    PricingStrategy
)


class TestQuotationGenerator:
    """Tests for QuotationGenerator"""
    
    @pytest.fixture
    def generator(self):
        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(return_value='{"category": "design", "complexity": "moderate", "estimated_hours": 10}')
        mock_memory = MagicMock()
        mock_memory.store_memory = AsyncMock()
        
        return QuotationGenerator(
            llm_client=mock_llm,
            memory_store=mock_memory
        )
    
    def test_service_category_enum(self):
        assert ServiceCategory.DESIGN.value == "design"
        assert ServiceCategory.DEVELOPMENT.value == "development"
        assert ServiceCategory.WRITING.value == "writing"
    
    def test_complexity_level_enum(self):
        assert ComplexityLevel.SIMPLE.value == "simple"
        assert ComplexityLevel.MODERATE.value == "moderate"
        assert ComplexityLevel.COMPLEX.value == "complex"
        assert ComplexityLevel.EXPERT.value == "expert"
    
    def test_calculate_base_price(self, generator):
        price = generator.calculate_base_price(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=10
        )
        assert price > 0
        assert price == 200 * 10
    
    def test_calculate_base_price_simple(self, generator):
        price = generator.calculate_base_price(
            category=ServiceCategory.WRITING,
            complexity=ComplexityLevel.SIMPLE,
            estimated_hours=5
        )
        assert price == 25 * 5
    
    def test_estimate_delivery_days_standard(self, generator):
        days = generator.estimate_delivery_days(
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="standard"
        )
        assert days >= 3
    
    def test_estimate_delivery_days_rush(self, generator):
        days_standard = generator.estimate_delivery_days(
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="standard"
        )
        days_rush = generator.estimate_delivery_days(
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="rush"
        )
        assert days_rush < days_standard
    
    def test_generate_quotation_id(self, generator):
        id1 = generator._generate_quotation_id()
        id2 = generator._generate_quotation_id()
        
        assert id1.startswith("QUO-")
        assert id2.startswith("QUO-")
        assert id1 != id2
    
    def test_generate_terms(self, generator):
        terms = generator._generate_terms(7)
        assert "7" in terms
        assert "Delivery" in terms


class TestMessageTemplateManager:
    """Tests for MessageTemplateManager"""
    
    @pytest.fixture
    def manager(self):
        return MessageTemplateManager()
    
    def test_load_default_templates(self, manager):
        templates = manager.list_templates()
        assert len(templates) > 0
    
    def test_get_template_by_id(self, manager):
        template = manager.get_template("greeting_001")
        assert template is not None
        assert template.name == "Initial Greeting"
    
    def test_get_templates_by_type(self, manager):
        templates = manager.get_templates_by_type(MessageTemplateType.GREETING)
        assert len(templates) > 0
        assert all(t.type == MessageTemplateType.GREETING for t in templates)
    
    def test_render_template(self, manager):
        content = manager.render_template(
            "greeting_001",
            {
                "buyer_name": "John",
                "project_summary": "Logo design project",
                "seller_name": "Jane"
            }
        )
        
        assert content is not None
        assert "John" in content
        assert "Jane" in content
    
    def test_render_template_with_subject(self, manager):
        result = manager.render_template_with_subject(
            "greeting_001",
            {
                "buyer_name": "John",
                "project_summary": "Logo design",
                "seller_name": "Jane"
            }
        )
        
        assert result is not None
        assert "subject" in result
        assert "content" in result
    
    def test_suggest_template(self, manager):
        suggestions = manager.suggest_template("I need a price quote")
        assert len(suggestions) > 0
    
    def test_add_template(self, manager):
        new_template = MessageTemplate(
            id="custom_001",
            name="Custom Template",
            type=MessageTemplateType.CUSTOM,
            content="Hello {name}!",
            variables=["name"]
        )
        
        manager.add_template(new_template)
        
        retrieved = manager.get_template("custom_001")
        assert retrieved is not None
        assert retrieved.name == "Custom Template"
    
    def test_delete_template(self, manager):
        result = manager.delete_template("greeting_001")
        assert result is True
        
        template = manager.get_template("greeting_001")
        assert template.is_active is False


class TestOrderTracker:
    """Tests for OrderTracker"""
    
    @pytest.fixture
    def tracker(self):
        mock_client = MagicMock()
        mock_client.get_orders = AsyncMock(return_value=[])
        
        return OrderTracker(
            fiverr_client=mock_client,
            config=OrderTrackerConfig()
        )
    
    def test_tracker_initialization(self, tracker):
        assert tracker._running is False
        assert len(tracker._tracked_orders) == 0
    
    def test_get_tracking_stats(self, tracker):
        stats = tracker.get_tracking_stats()
        
        assert stats["total_tracked"] == 0
        assert stats["running"] is False
        assert "by_status" in stats


class TestPricingAdvisor:
    """Tests for PricingAdvisor"""
    
    @pytest.fixture
    def advisor(self):
        mock_llm = MagicMock()
        mock_memory = MagicMock()
        
        return PricingAdvisor(
            llm_client=mock_llm,
            memory_store=mock_memory
        )
    
    def test_market_data_exists(self, advisor):
        assert ServiceCategory.DEVELOPMENT in advisor.MARKET_DATA
        assert ServiceCategory.DESIGN in advisor.MARKET_DATA
    
    def test_complexity_multipliers(self, advisor):
        assert advisor.COMPLEXITY_MULTIPLIERS[ComplexityLevel.SIMPLE] == 0.7
        assert advisor.COMPLEXITY_MULTIPLIERS[ComplexityLevel.MODERATE] == 1.0
        assert advisor.COMPLEXITY_MULTIPLIERS[ComplexityLevel.COMPLEX] == 1.5
        assert advisor.COMPLEXITY_MULTIPLIERS[ComplexityLevel.EXPERT] == 2.2
    
    def test_strategy_adjustments(self, advisor):
        assert advisor.STRATEGY_ADJUSTMENTS[PricingStrategy.COMPETITIVE] == 0.9
        assert advisor.STRATEGY_ADJUSTMENTS[PricingStrategy.PREMIUM] == 1.3
        assert advisor.STRATEGY_ADJUSTMENTS[PricingStrategy.VALUE] == 1.0
        assert advisor.STRATEGY_ADJUSTMENTS[PricingStrategy.PENETRATION] == 0.75
    
    @pytest.mark.asyncio
    async def test_analyze_market(self, advisor):
        market_data = await advisor.analyze_market(ServiceCategory.DEVELOPMENT)
        
        assert market_data.category == ServiceCategory.DEVELOPMENT
        assert market_data.min_price > 0
        assert market_data.max_price > market_data.min_price
        assert market_data.avg_price > 0
    
    def test_get_position_label(self, advisor):
        assert advisor._get_position_label(10) == "Budget"
        assert advisor._get_position_label(30) == "Competitive"
        assert advisor._get_position_label(50) == "Market Average"
        assert advisor._get_position_label(70) == "Premium"
        assert advisor._get_position_label(90) == "Luxury"


class TestQuotationModel:
    """Tests for Quotation model"""
    
    def test_quotation_item_creation(self):
        item = QuotationItem(
            description="Logo Design",
            quantity=1,
            unit_price=100.0,
            total=100.0
        )
        
        assert item.description == "Logo Design"
        assert item.quantity == 1
        assert item.unit_price == 100.0
    
    def test_quotation_creation(self):
        quotation = Quotation(
            id="QUO-001",
            buyer_username="test_buyer",
            project_title="Test Project",
            category=ServiceCategory.DESIGN,
            complexity=ComplexityLevel.MODERATE,
            items=[
                QuotationItem(
                    description="Design",
                    quantity=1,
                    unit_price=100.0,
                    total=100.0
                )
            ],
            subtotal=100.0,
            total=100.0,
            delivery_days=7,
            valid_until=datetime.now() + timedelta(days=7)
        )
        
        assert quotation.id == "QUO-001"
        assert quotation.buyer_username == "test_buyer"
        assert len(quotation.items) == 1


class TestTrackingEvent:
    """Tests for TrackingEvent model"""
    
    def test_tracking_event_creation(self):
        event = TrackingEvent(
            order_id="ORD-001",
            event_type="status_change",
            old_status="pending",
            new_status="active"
        )
        
        assert event.order_id == "ORD-001"
        assert event.event_type == "status_change"
        assert event.old_status == "pending"
        assert event.new_status == "active"
