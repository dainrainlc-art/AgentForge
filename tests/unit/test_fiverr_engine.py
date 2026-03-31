"""
AgentForge Fiverr 业务引擎单元测试
测试 Fiverr 运营自动化相关的所有业务逻辑
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any

from agentforge.fiverr.order_tracker import (
    OrderTracker,
    OrderTrackerConfig,
    OrderStatus,
    TrackedOrder,
    TrackingEvent,
)
from agentforge.fiverr.delivery import (
    DeliveryAutomation,
    DeliveryPackager,
    DeliveryValidator,
    DeliveryPackage,
    DeliveryTemplate,
    DeliverableFile,
    DeliveryFormat,
    DeliverableType,
    DeliveryStatus,
)
from agentforge.fiverr.quotation import (
    QuotationGenerator,
    Quotation,
    QuotationItem,
    ServiceCategory,
    ComplexityLevel,
)
from agentforge.fiverr.pricing_advisor import (
    PricingAdvisor,
    PricingStrategy,
    PricingFactor,
    MarketData,
)
from agentforge.fiverr.message_templates import (
    MessageTemplateManager,
    MessageTemplateType,
    MessageTemplate,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_fiverr_client():
    """Mock Fiverr API 客户端"""
    client = MagicMock()
    client.get_orders = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_llm_client():
    """Mock LLM 客户端"""
    llm = MagicMock()
    llm.chat = AsyncMock(return_value='{"category": "design", "complexity": "moderate", "estimated_hours": 10}')
    llm.chat_with_failover = AsyncMock(return_value="# Test README\n\nThis is a test.")
    llm.generate = AsyncMock(return_value=MagicMock(content="Generated response"))
    return llm


@pytest.fixture
def mock_memory_store():
    """Mock 内存存储"""
    memory = MagicMock()
    memory.store_memory = AsyncMock()
    memory.search_memories = AsyncMock(return_value=[])
    return memory


@pytest.fixture
def order_tracker_config():
    """订单跟踪器配置"""
    return OrderTrackerConfig(
        check_interval_seconds=60,
        late_threshold_hours=24,
        reminder_before_due_hours=12,
        enable_notifications=True,
        track_status_changes=True,
    )


@pytest.fixture
def sample_fiverr_order():
    """示例 Fiverr 订单"""
    from integrations.external.fiverr_client import FiverrOrder
    
    return FiverrOrder(
        id="ORD-001",
        buyer_username="test_buyer",
        seller_username="test_seller",
        title="Test Order",
        description="Test order description",
        price=100.0,
        status="active",
        created_at=datetime.now() - timedelta(days=1),
        updated_at=datetime.now(),
        delivery_date=datetime.now() + timedelta(days=6),
    )


@pytest.fixture
def delivery_template():
    """示例交付模板"""
    return DeliveryTemplate(
        id="web_dev_template",
        name="Web Development Template",
        service_type="web",
        required_files=["index.html", "style.css", "script.js"],
        optional_files=["README.md", "package.json"],
        folder_structure={
            "src": {"js": {}, "css": {}},
            "docs": {},
        },
        readme_template="web_project_readme",
    )


# ============================================================================
# Order Tracker Tests
# ============================================================================


class TestOrderTracker:
    """OrderTracker 单元测试"""

    @pytest.fixture
    def tracker(self, mock_fiverr_client, order_tracker_config):
        """创建订单跟踪器实例"""
        return OrderTracker(
            fiverr_client=mock_fiverr_client,
            config=order_tracker_config,
        )

    def test_tracker_initialization(self, tracker):
        """测试跟踪器初始化"""
        assert tracker._running is False
        assert len(tracker._tracked_orders) == 0
        assert tracker.config.check_interval_seconds == 60

    def test_start_tracking(self, tracker):
        """测试启动跟踪"""
        assert tracker._running is False

    def test_stop_tracking_when_not_running(self, tracker):
        """测试停止未运行的跟踪器"""
        tracker._running = False
        tracker._tracker_task = None

    def test_add_order_to_track(self, tracker, sample_fiverr_order):
        """测试添加订单到跟踪列表"""
        tracker.add_order_to_track(sample_fiverr_order)
        
        tracked = tracker.get_tracked_order(sample_fiverr_order.id)
        assert tracked is not None
        assert tracked.order.id == sample_fiverr_order.id
        assert tracked.order.buyer_username == "test_buyer"

    def test_remove_order_from_track(self, tracker, sample_fiverr_order):
        """测试从跟踪列表移除订单"""
        tracker.add_order_to_track(sample_fiverr_order)
        result = tracker.remove_order_from_track(sample_fiverr_order.id)
        
        assert result is True
        assert tracker.get_tracked_order(sample_fiverr_order.id) is None

    def test_remove_non_existent_order(self, tracker):
        """测试移除不存在的订单"""
        result = tracker.remove_order_from_track("NON_EXISTENT")
        assert result is False

    def test_get_orders_by_status(self, tracker, sample_fiverr_order):
        """测试按状态获取订单"""
        tracker.add_order_to_track(sample_fiverr_order)
        
        active_orders = tracker.get_orders_by_status(OrderStatus.ACTIVE)
        assert len(active_orders) == 1

    def test_get_late_orders(self, tracker):
        """测试获取逾期订单"""
        from integrations.external.fiverr_client import FiverrOrder
        
        late_order = FiverrOrder(
            id="LATE-001",
            buyer_username="late_buyer",
            seller_username="seller",
            title="Late Order",
            description="This order is late",
            price=150.0,
            status="active",
            created_at=datetime.now() - timedelta(days=10),
            updated_at=datetime.now() - timedelta(days=1),
            delivery_date=datetime.now() - timedelta(days=1),
        )
        
        tracker.add_order_to_track(late_order)
        late_orders = tracker.get_late_orders()
        
        assert len(late_orders) == 1
        assert late_orders[0].order.id == "LATE-001"

    def test_get_tracking_stats(self, tracker, sample_fiverr_order):
        """测试获取跟踪统计"""
        tracker.add_order_to_track(sample_fiverr_order)
        
        stats = tracker.get_tracking_stats()
        
        assert stats["total_tracked"] == 1
        assert stats["running"] is False
        assert "by_status" in stats
        assert "late_orders" in stats

    def test_order_history(self, tracker, sample_fiverr_order):
        """测试订单历史记录"""
        tracker.add_order_to_track(sample_fiverr_order)
        
        history = tracker.get_order_history(sample_fiverr_order.id)
        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_all_tracked_orders(self, tracker, sample_fiverr_order):
        """测试获取所有跟踪订单"""
        tracker.add_order_to_track(sample_fiverr_order)
        
        orders = tracker.get_all_tracked_orders()
        assert len(orders) == 1
        assert orders[0].order.id == sample_fiverr_order.id

    @pytest.mark.asyncio
    async def test_handle_status_change(self, tracker, sample_fiverr_order):
        """测试处理状态变更"""
        tracker.add_order_to_track(sample_fiverr_order)
        tracked = tracker.get_tracked_order(sample_fiverr_order.id)
        
        with patch("agentforge.fiverr.order_tracker.event_bus") as mock_event_bus, \
             patch("agentforge.fiverr.order_tracker.notification_service") as mock_notification:
            mock_event_bus.publish = AsyncMock()
            mock_notification.send_notification = AsyncMock()
            
            await tracker._handle_status_change(tracked, "pending", "active")
            
            assert len(tracked.status_history) == 1
            assert tracked.status_history[0].event_type == "status_change"
            assert tracked.status_history[0].old_status == "pending"
            assert tracked.status_history[0].new_status == "active"

    def test_estimate_due_date(self, tracker, sample_fiverr_order):
        """测试预估到期日"""
        due_date = tracker._estimate_due_date(sample_fiverr_order)
        
        assert due_date is not None
        assert due_date > sample_fiverr_order.created_at

    def test_estimate_due_date_completed_order(self, tracker):
        """测试已完成订单的到期日"""
        from integrations.external.fiverr_client import FiverrOrder
        
        completed_order = FiverrOrder(
            id="COMPLETED-001",
            buyer_username="buyer",
            seller_username="seller",
            title="Completed",
            description="Done",
            price=100.0,
            status="completed",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            delivery_date=datetime.now(),
        )
        
        due_date = tracker._estimate_due_date(completed_order)
        assert due_date is None

    def test_tracking_event_creation(self):
        """测试跟踪事件创建"""
        event = TrackingEvent(
            order_id="ORD-001",
            event_type="status_change",
            old_status="pending",
            new_status="active",
            notes="Status updated automatically",
        )
        
        assert event.order_id == "ORD-001"
        assert event.event_type == "status_change"
        assert event.old_status == "pending"
        assert event.new_status == "active"
        assert event.notes == "Status updated automatically"

    def test_order_status_enum(self):
        """测试订单状态枚举"""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.ACTIVE.value == "active"
        assert OrderStatus.LATE.value == "late"
        assert OrderStatus.DELIVERED.value == "delivered"
        assert OrderStatus.COMPLETED.value == "completed"
        assert OrderStatus.CANCELLED.value == "cancelled"
        assert OrderStatus.DISPUTED.value == "disputed"


# ============================================================================
# Delivery Automation Tests
# ============================================================================


class TestDeliveryAutomation:
    """DeliveryAutomation 单元测试"""

    @pytest.fixture
    def automation(self):
        """创建交付自动化实例"""
        return DeliveryAutomation()

    def test_automation_initialization(self, automation):
        """测试自动化初始化"""
        assert automation.packager is not None
        assert automation.validator is not None
        assert len(automation._templates) > 0

    def test_get_template(self, automation):
        """测试获取模板"""
        template = automation.get_template("web_development")
        assert template is not None
        assert template.id == "web_development"

    def test_get_non_existent_template(self, automation):
        """测试获取不存在的模板"""
        template = automation.get_template("non_existent")
        assert template is None

    def test_add_template(self, automation):
        """测试添加模板"""
        new_template = DeliveryTemplate(
            id="custom_template",
            name="Custom Template",
            service_type="custom",
            required_files=["file1.txt"],
            optional_files=[],
            folder_structure={},
            readme_template="custom",
        )
        
        automation.add_template(new_template)
        retrieved = automation.get_template("custom_template")
        
        assert retrieved is not None
        assert retrieved.name == "Custom Template"

    def test_list_templates(self, automation):
        """测试列出模板"""
        templates = automation.list_templates()
        assert len(templates) > 0
        assert all("id" in t and "name" in t for t in templates)

    @pytest.mark.asyncio
    async def test_validate_delivery(self, automation, tmp_path):
        """测试交付验证"""
        file1 = tmp_path / "test.txt"
        file1.write_text("test content")
        
        validation = await automation.validate_delivery(
            files=[str(file1)],
            service_type="web_development",
        )
        
        assert "valid" in validation
        assert "missing_required" in validation
        assert "warnings" in validation

    def test_delivery_format_enum(self):
        """测试交付格式枚举"""
        assert DeliveryFormat.ZIP.value == "zip"
        assert DeliveryFormat.RAR.value == "rar"
        assert DeliveryFormat.TAR_GZ.value == "tar.gz"
        assert DeliveryFormat.FOLDER.value == "folder"

    def test_deliverable_type_enum(self):
        """测试可交付类型枚举"""
        assert DeliverableType.SOURCE_CODE.value == "source_code"
        assert DeliverableType.DOCUMENTATION.value == "documentation"
        assert DeliverableType.DESIGN_ASSETS.value == "design_assets"


class TestDeliveryPackager:
    """DeliveryPackager 单元测试"""

    @pytest.fixture
    def packager(self, tmp_path):
        """创建打包器实例"""
        output_dir = tmp_path / "deliveries"
        output_dir.mkdir()
        return DeliveryPackager(output_dir=str(output_dir))

    @pytest.mark.asyncio
    async def test_create_package(self, packager, tmp_path):
        """测试创建交付包"""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content 1")
        
        package = await packager.create_package(
            order_id="ORD-001",
            files=[str(file1)],
            package_name="test_package",
            delivery_format=DeliveryFormat.ZIP,
            include_readme=False,
        )
        
        assert package.id.startswith("pkg_")
        assert package.order_id == "ORD-001"
        assert package.name == "test_package"
        assert len(package.files) == 1

    @pytest.mark.asyncio
    async def test_create_package_with_missing_files(self, packager):
        """测试创建包含不存在文件的包"""
        template = DeliveryTemplate(
            id="test_template",
            name="Test Template",
            service_type="test",
            required_files=["required_file.txt"],
            optional_files=[],
            folder_structure={},
            readme_template="test",
        )
        
        package = await packager.create_package(
            order_id="ORD-002",
            files=["/non/existent/file.txt"],
            include_readme=False,
            template=template,
        )
        
        assert package.status == DeliveryStatus.FAILED
        assert "validation_errors" in package.metadata

    @pytest.mark.asyncio
    async def test_create_package_with_template(
        self, packager, tmp_path, delivery_template
    ):
        """测试使用模板创建包"""
        file1 = tmp_path / "index.html"
        file1.write_text("<html></html>")
        
        package = await packager.create_package(
            order_id="ORD-003",
            files=[str(file1)],
            template=delivery_template,
            include_readme=False,
        )
        
        assert package.order_id == "ORD-003"

    def test_get_package_info(self, packager, tmp_path):
        """测试获取包信息"""
        test_file = tmp_path / "test.zip"
        test_file.write_text("test")
        
        info = packager.get_package_info(str(test_file))
        
        assert "path" in info
        assert "size" in info
        assert "format" in info

    def test_get_non_existent_package_info(self, packager):
        """测试获取不存在的包信息"""
        info = packager.get_package_info("/non/existent.zip")
        assert "error" in info
        assert info["error"] == "Package not found"


class TestDeliveryValidator:
    """DeliveryValidator 单元测试"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return DeliveryValidator()

    def test_validate_files(self, validator, tmp_path):
        """测试文件验证"""
        file1 = tmp_path / "test.txt"
        file1.write_text("content")
        
        deliverable = DeliverableFile(
            path=str(file1),
            size=7,
            file_type=".txt",
            category=DeliverableType.DOCUMENTATION,
        )
        
        result = validator.validate_files([deliverable])
        
        assert result["valid"] is True
        assert len(result["missing_required"]) == 0
        assert len(result["invalid_files"]) == 0

    def test_validate_files_with_template(self, validator, tmp_path):
        """测试使用模板验证文件"""
        file1 = tmp_path / "index.html"
        file1.write_text("<html></html>")
        
        deliverable = DeliverableFile(
            path=str(file1),
            size=13,
            file_type=".html",
            category=DeliverableType.SOURCE_CODE,
        )
        
        template = DeliveryTemplate(
            id="test",
            name="Test",
            service_type="test",
            required_files=[str(file1)],  # 使用完整路径
            optional_files=[],
            folder_structure={},
            readme_template="test",
        )
        
        result = validator.validate_files([deliverable], template)
        
        assert result["valid"] is True

    def test_validate_missing_required_files(self, validator, tmp_path):
        """测试验证缺失必需文件"""
        template = DeliveryTemplate(
            id="test",
            name="Test",
            service_type="test",
            required_files=["required.txt"],
            optional_files=[],
            folder_structure={},
            readme_template="test",
        )
        
        result = validator.validate_files([], template)
        
        assert result["valid"] is False
        assert len(result["missing_required"]) > 0

    def test_validate_empty_file(self, validator, tmp_path):
        """测试验证空文件"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        deliverable = DeliverableFile(
            path=str(empty_file),
            size=0,
            file_type=".txt",
            category=DeliverableType.DOCUMENTATION,
        )
        
        result = validator.validate_files([deliverable])
        
        assert len(result["warnings"]) > 0
        assert any("Empty file" in w for w in result["warnings"])

    def test_categorize_file_source_code(self, validator):
        """测试文件分类 - 源代码"""
        assert validator.categorize_file("test.py") == DeliverableType.SOURCE_CODE
        assert validator.categorize_file("script.js") == DeliverableType.SOURCE_CODE
        assert validator.categorize_file("app.ts") == DeliverableType.SOURCE_CODE

    def test_categorize_file_documentation(self, validator):
        """测试文件分类 - 文档"""
        assert validator.categorize_file("readme.md") == DeliverableType.DOCUMENTATION
        assert validator.categorize_file("doc.txt") == DeliverableType.DOCUMENTATION
        assert validator.categorize_file("report.pdf") == DeliverableType.DOCUMENTATION

    def test_categorize_file_images(self, validator):
        """测试文件分类 - 图片"""
        assert validator.categorize_file("image.png") == DeliverableType.IMAGES
        assert validator.categorize_file("photo.jpg") == DeliverableType.IMAGES
        assert validator.categorize_file("graphic.gif") == DeliverableType.IMAGES

    def test_categorize_file_video(self, validator):
        """测试文件分类 - 视频"""
        assert validator.categorize_file("video.mp4") == DeliverableType.VIDEO
        assert validator.categorize_file("movie.mov") == DeliverableType.VIDEO

    def test_categorize_file_audio(self, validator):
        """测试文件分类 - 音频"""
        assert validator.categorize_file("song.mp3") == DeliverableType.AUDIO
        assert validator.categorize_file("track.wav") == DeliverableType.AUDIO

    def test_categorize_file_data(self, validator):
        """测试文件分类 - 数据文件"""
        assert validator.categorize_file("data.json") == DeliverableType.DATA_FILES
        assert validator.categorize_file("report.csv") == DeliverableType.DATA_FILES

    def test_categorize_file_config(self, validator):
        """测试文件分类 - 配置文件"""
        assert validator.categorize_file("app.ini") == DeliverableType.CONFIGURATION
        assert validator.categorize_file("config.ini") == DeliverableType.CONFIGURATION
        assert validator.categorize_file("settings.conf") == DeliverableType.CONFIGURATION
        assert validator.categorize_file("application.toml") == DeliverableType.CONFIGURATION

    def test_categorize_file_mixed(self, validator):
        """测试文件分类 - 混合类型"""
        assert validator.categorize_file("unknown.xyz") == DeliverableType.MIXED

    def test_format_size(self, validator):
        """测试文件大小格式化"""
        assert validator._format_size(500) == "500.0 B"
        assert validator._format_size(1024) == "1.0 KB"
        assert validator._format_size(1048576) == "1.0 MB"
        assert validator._format_size(1073741824) == "1.0 GB"


# ============================================================================
# Quotation Generator Tests
# ============================================================================


class TestQuotationGenerator:
    """QuotationGenerator 单元测试"""

    @pytest.fixture
    def generator(self, mock_llm_client, mock_memory_store):
        """创建报价生成器实例"""
        return QuotationGenerator(
            llm_client=mock_llm_client,
            memory_store=mock_memory_store,
        )

    def test_generator_initialization(self, generator):
        """测试初始化"""
        assert generator.llm_client is not None
        assert generator.memory_store is not None

    def test_generate_quotation_id(self, generator):
        """测试生成报价 ID"""
        id1 = generator._generate_quotation_id()
        id2 = generator._generate_quotation_id()
        
        assert id1.startswith("QUO-")
        assert id2.startswith("QUO-")
        assert id1 != id2

    def test_calculate_base_price_development(self, generator):
        """测试计算开发项目基础价格"""
        price = generator.calculate_base_price(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=10,
        )
        
        assert price == 200 * 10

    def test_calculate_base_price_design(self, generator):
        """测试计算设计项目基础价格"""
        price = generator.calculate_base_price(
            category=ServiceCategory.DESIGN,
            complexity=ComplexityLevel.SIMPLE,
            estimated_hours=5,
        )
        
        assert price == 50 * 5

    def test_calculate_base_price_writing(self, generator):
        """测试计算写作项目基础价格"""
        price = generator.calculate_base_price(
            category=ServiceCategory.WRITING,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=8,
        )
        
        assert price == 50 * 8

    def test_estimate_delivery_days_moderate(self, generator):
        """测试预估中等复杂度交付时间"""
        days = generator.estimate_delivery_days(
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="standard",
        )
        
        assert days >= 3

    def test_estimate_delivery_days_rush(self, generator):
        """测试预估加急交付时间"""
        days_standard = generator.estimate_delivery_days(
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="standard",
        )
        
        days_rush = generator.estimate_delivery_days(
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="rush",
        )
        
        assert days_rush < days_standard

    def test_estimate_delivery_days_relaxed(self, generator):
        """测试预估宽松交付时间"""
        days_standard = generator.estimate_delivery_days(
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="standard",
        )
        
        days_relaxed = generator.estimate_delivery_days(
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="relaxed",
        )
        
        assert days_relaxed > days_standard

    def test_estimate_delivery_days_simple(self, generator):
        """测试预估简单项目交付时间"""
        days = generator.estimate_delivery_days(
            complexity=ComplexityLevel.SIMPLE,
            estimated_hours=8,
            urgency="standard",
        )
        
        assert days >= 1

    def test_estimate_delivery_days_expert(self, generator):
        """测试预估专家级项目交付时间"""
        days = generator.estimate_delivery_days(
            complexity=ComplexityLevel.EXPERT,
            estimated_hours=40,
            urgency="standard",
        )
        
        assert days >= 7

    def test_generate_terms(self, generator):
        """测试生成条款"""
        terms = generator._generate_terms(7)
        
        assert "7" in terms
        assert "Delivery" in terms
        assert "revisions" in terms

    def test_service_category_enum(self):
        """测试服务类别枚举"""
        assert ServiceCategory.DESIGN.value == "design"
        assert ServiceCategory.DEVELOPMENT.value == "development"
        assert ServiceCategory.WRITING.value == "writing"
        assert ServiceCategory.MARKETING.value == "marketing"
        assert ServiceCategory.VIDEO.value == "video"
        assert ServiceCategory.MUSIC.value == "music"
        assert ServiceCategory.OTHER.value == "other"

    def test_complexity_level_enum(self):
        """测试复杂度级别枚举"""
        assert ComplexityLevel.SIMPLE.value == "simple"
        assert ComplexityLevel.MODERATE.value == "moderate"
        assert ComplexityLevel.COMPLEX.value == "complex"
        assert ComplexityLevel.EXPERT.value == "expert"

    def test_base_rates_structure(self, generator):
        """测试基础费率结构"""
        assert ServiceCategory.DESIGN in generator.BASE_RATES
        assert ServiceCategory.DEVELOPMENT in generator.BASE_RATES
        
        assert "simple" in generator.BASE_RATES[ServiceCategory.DESIGN]
        assert "moderate" in generator.BASE_RATES[ServiceCategory.DESIGN]
        assert "complex" in generator.BASE_RATES[ServiceCategory.DESIGN]
        assert "expert" in generator.BASE_RATES[ServiceCategory.DESIGN]

    def test_delivery_multipliers(self, generator):
        """测试交付乘数"""
        assert generator.DELIVERY_MULTIPLIERS["rush"] == 1.5
        assert generator.DELIVERY_MULTIPLIERS["standard"] == 1.0
        assert generator.DELIVERY_MULTIPLIERS["relaxed"] == 0.85

    @pytest.mark.asyncio
    async def test_analyze_request(self, generator):
        """测试分析请求"""
        request = "I need a logo design for my business"
        
        analysis = await generator.analyze_request(request)
        
        assert "category" in analysis
        assert "complexity" in analysis
        assert "estimated_hours" in analysis

    @pytest.mark.asyncio
    async def test_analyze_request_with_invalid_response(
        self, mock_llm_client, mock_memory_store
    ):
        """测试分析无效响应"""
        mock_llm_client.chat = AsyncMock(
            return_value='{"invalid": "json"}'
        )
        
        generator = QuotationGenerator(
            llm_client=mock_llm_client,
            memory_store=mock_memory_store,
        )
        
        analysis = await generator.analyze_request("test")
        
        assert analysis["category"] == ServiceCategory.OTHER
        assert analysis["complexity"] == ComplexityLevel.MODERATE

    @pytest.mark.asyncio
    async def test_analyze_request_with_exception(
        self, mock_llm_client, mock_memory_store
    ):
        """测试分析异常"""
        mock_llm_client.chat = AsyncMock(side_effect=Exception("API Error"))
        
        generator = QuotationGenerator(
            llm_client=mock_llm_client,
            memory_store=mock_memory_store,
        )
        
        analysis = await generator.analyze_request("test")
        
        assert analysis["category"] == ServiceCategory.OTHER
        assert analysis["complexity"] == ComplexityLevel.MODERATE


class TestQuotationModel:
    """Quotation 模型单元测试"""

    def test_quotation_item_creation(self):
        """测试报价项创建"""
        item = QuotationItem(
            description="Logo Design",
            quantity=2,
            unit_price=100.0,
            total=200.0,
            notes="Rush delivery",
        )
        
        assert item.description == "Logo Design"
        assert item.quantity == 2
        assert item.unit_price == 100.0
        assert item.total == 200.0
        assert item.notes == "Rush delivery"

    def test_quotation_item_default_quantity(self):
        """测试报价项默认数量"""
        item = QuotationItem(
            description="Service",
            unit_price=50.0,
            total=50.0,
        )
        
        assert item.quantity == 1

    def test_quotation_creation(self):
        """测试报价创建"""
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
                    total=100.0,
                )
            ],
            subtotal=100.0,
            discount=10.0,
            total=90.0,
            delivery_days=7,
            revision_count=3,
            valid_until=datetime.now() + timedelta(days=7),
        )
        
        assert quotation.id == "QUO-001"
        assert quotation.buyer_username == "test_buyer"
        assert len(quotation.items) == 1
        assert quotation.discount == 10.0
        assert quotation.revision_count == 3

    def test_quotation_default_values(self):
        """测试报价默认值"""
        quotation = Quotation(
            id="QUO-002",
            buyer_username="buyer",
            project_title="Project",
            category=ServiceCategory.OTHER,
            complexity=ComplexityLevel.SIMPLE,
            items=[],
            subtotal=0.0,
            total=0.0,
            delivery_days=7,
            valid_until=datetime.now() + timedelta(days=7),
        )
        
        assert quotation.discount == 0.0
        assert quotation.tax == 0.0
        assert quotation.revision_count == 2


# ============================================================================
# Pricing Advisor Tests
# ============================================================================


class TestPricingAdvisor:
    """PricingAdvisor 单元测试"""

    @pytest.fixture
    def advisor(self, mock_llm_client, mock_memory_store):
        """创建定价顾问实例"""
        return PricingAdvisor(
            llm_client=mock_llm_client,
            memory_store=mock_memory_store,
        )

    def test_advisor_initialization(self, advisor):
        """测试初始化"""
        assert advisor.llm_client is not None
        assert advisor.memory_store is not None
        assert len(advisor._price_history) == 0

    def test_market_data_exists(self, advisor):
        """测试市场数据存在"""
        assert ServiceCategory.DEVELOPMENT in advisor.MARKET_DATA
        assert ServiceCategory.DESIGN in advisor.MARKET_DATA
        assert ServiceCategory.WRITING in advisor.MARKET_DATA

    def test_market_data_structure(self, advisor):
        """测试市场数据结构"""
        dev_data = advisor.MARKET_DATA[ServiceCategory.DEVELOPMENT]
        
        assert "min" in dev_data
        assert "max" in dev_data
        assert "avg" in dev_data
        assert "median" in dev_data

    def test_complexity_multipliers(self, advisor):
        """测试复杂度乘数"""
        assert advisor.COMPLEXITY_MULTIPLIERS[ComplexityLevel.SIMPLE] == 0.7
        assert advisor.COMPLEXITY_MULTIPLIERS[ComplexityLevel.MODERATE] == 1.0
        assert advisor.COMPLEXITY_MULTIPLIERS[ComplexityLevel.COMPLEX] == 1.5
        assert advisor.COMPLEXITY_MULTIPLIERS[ComplexityLevel.EXPERT] == 2.2

    def test_strategy_adjustments(self, advisor):
        """测试策略调整"""
        assert advisor.STRATEGY_ADJUSTMENTS[PricingStrategy.COMPETITIVE] == 0.9
        assert advisor.STRATEGY_ADJUSTMENTS[PricingStrategy.PREMIUM] == 1.3
        assert advisor.STRATEGY_ADJUSTMENTS[PricingStrategy.VALUE] == 1.0
        assert advisor.STRATEGY_ADJUSTMENTS[PricingStrategy.PENETRATION] == 0.75

    @pytest.mark.asyncio
    async def test_analyze_market(self, advisor):
        """测试市场分析"""
        market_data = await advisor.analyze_market(ServiceCategory.DEVELOPMENT)
        
        assert market_data.category == ServiceCategory.DEVELOPMENT
        assert market_data.min_price > 0
        assert market_data.max_price > market_data.min_price
        assert market_data.avg_price > 0
        assert market_data.median_price > 0

    @pytest.mark.asyncio
    async def test_analyze_market_other_category(self, advisor):
        """测试分析其他类别市场"""
        market_data = await advisor.analyze_market(ServiceCategory.OTHER)
        
        assert market_data.category == ServiceCategory.OTHER
        assert market_data.min_price > 0

    @pytest.mark.asyncio
    async def test_calculate_pricing_factors(self, advisor):
        """测试计算定价因素"""
        factors = await advisor.calculate_pricing_factors(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="standard",
        )
        
        assert len(factors) >= 2
        
        factor_names = [f.name for f in factors]
        assert "Complexity" in factor_names
        assert "Urgency" in factor_names
        assert "Scope" in factor_names

    @pytest.mark.asyncio
    async def test_calculate_pricing_factors_with_buyer_history(self, advisor):
        """测试使用买家历史计算定价因素"""
        buyer_history = {"is_repeat": True, "total_orders": 5}
        
        factors = await advisor.calculate_pricing_factors(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="standard",
            buyer_history=buyer_history,
        )
        
        factor_names = [f.name for f in factors]
        assert "Client Relationship" in factor_names

    @pytest.mark.asyncio
    async def test_calculate_pricing_factors_with_requirements(self, advisor):
        """测试使用需求计算定价因素"""
        factors = await advisor.calculate_pricing_factors(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            urgency="standard",
            project_requirements=["req1", "req2", "req3"],
        )
        
        factor_names = [f.name for f in factors]
        assert "Requirements" in factor_names

    @pytest.mark.asyncio
    async def test_suggest_price(self, advisor):
        """测试价格建议"""
        suggestion = await advisor.suggest_price(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            strategy=PricingStrategy.VALUE,
        )
        
        assert suggestion.suggested_price > 0
        assert suggestion.price_range_min > 0
        assert suggestion.price_range_max > 0
        assert suggestion.confidence > 0
        assert suggestion.confidence <= 0.95
        assert len(suggestion.recommendations) > 0

    @pytest.mark.asyncio
    async def test_suggest_price_premium_strategy(self, advisor):
        """测试高端策略价格建议"""
        suggestion_value = await advisor.suggest_price(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            strategy=PricingStrategy.VALUE,
        )
        
        suggestion_premium = await advisor.suggest_price(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            strategy=PricingStrategy.PREMIUM,
        )
        
        assert suggestion_premium.suggested_price > suggestion_value.suggested_price

    @pytest.mark.asyncio
    async def test_suggest_price_penetration_strategy(self, advisor):
        """测试渗透策略价格建议"""
        suggestion_value = await advisor.suggest_price(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            strategy=PricingStrategy.VALUE,
        )
        
        suggestion_penetration = await advisor.suggest_price(
            category=ServiceCategory.DEVELOPMENT,
            complexity=ComplexityLevel.MODERATE,
            estimated_hours=20,
            strategy=PricingStrategy.PENETRATION,
        )
        
        assert suggestion_penetration.suggested_price < suggestion_value.suggested_price

    def test_generate_market_comparison(self, advisor):
        """测试生成市场比较"""
        comparison = advisor._generate_market_comparison(
            price=100,
            market_data=MarketData(
                category=ServiceCategory.DEVELOPMENT,
                min_price=50,
                max_price=200,
                avg_price=150,
                median_price=120,
                sample_size=100,
                last_updated=datetime.now(),
            ),
        )
        
        assert isinstance(comparison, str)

    def test_get_position_label(self, advisor):
        """测试获取定位标签"""
        assert advisor._get_position_label(10) == "Budget"
        assert advisor._get_position_label(30) == "Competitive"
        assert advisor._get_position_label(50) == "Market Average"
        assert advisor._get_position_label(70) == "Premium"
        assert advisor._get_position_label(90) == "Luxury"

    @pytest.mark.asyncio
    async def test_compare_with_competitors(self, advisor):
        """测试与竞争对手比较"""
        result = await advisor.compare_with_competitors(
            category=ServiceCategory.DEVELOPMENT,
            price=300,
        )
        
        assert "your_price" in result
        assert "market_min" in result
        assert "market_max" in result
        assert "market_avg" in result
        assert "percentile" in result
        assert "position" in result

    def test_pricing_strategy_enum(self):
        """测试定价策略枚举"""
        assert PricingStrategy.COMPETITIVE.value == "competitive"
        assert PricingStrategy.PREMIUM.value == "premium"
        assert PricingStrategy.VALUE.value == "value"
        assert PricingStrategy.PENETRATION.value == "penetration"


# ============================================================================
# Message Template Manager Tests
# ============================================================================


class TestMessageTemplateManager:
    """MessageTemplateManager 单元测试"""

    @pytest.fixture
    def manager(self):
        """创建消息模板管理器实例"""
        return MessageTemplateManager()

    def test_manager_initialization(self, manager):
        """测试初始化"""
        templates = manager.list_templates()
        assert len(templates) > 0

    def test_load_default_templates(self, manager):
        """测试加载默认模板"""
        templates = manager.list_templates()
        assert len(templates) >= 8

    def test_get_template_by_id(self, manager):
        """测试按 ID 获取模板"""
        template = manager.get_template("greeting_001")
        assert template is not None
        assert template.name == "Initial Greeting"
        assert template.type == MessageTemplateType.GREETING

    def test_get_non_existent_template(self, manager):
        """测试获取不存在的模板"""
        template = manager.get_template("non_existent")
        assert template is None

    def test_get_templates_by_type_greeting(self, manager):
        """测试按类型获取模板 - 问候"""
        templates = manager.get_templates_by_type(MessageTemplateType.GREETING)
        assert len(templates) > 0
        assert all(t.type == MessageTemplateType.GREETING for t in templates)

    def test_get_templates_by_type_quotation(self, manager):
        """测试按类型获取模板 - 报价"""
        templates = manager.get_templates_by_type(MessageTemplateType.QUOTATION)
        assert len(templates) > 0
        assert all(t.type == MessageTemplateType.QUOTATION for t in templates)

    def test_get_templates_by_type_delivery(self, manager):
        """测试按类型获取模板 - 交付"""
        templates = manager.get_templates_by_type(MessageTemplateType.DELIVERY)
        assert len(templates) > 0

    def test_render_template(self, manager):
        """测试渲染模板"""
        content = manager.render_template(
            "greeting_001",
            {
                "buyer_name": "John",
                "project_summary": "Logo design project",
                "seller_name": "Jane",
            },
        )
        
        assert content is not None
        assert "John" in content
        assert "Jane" in content

    def test_render_template_with_missing_variables(self, manager):
        """测试渲染缺少变量的模板"""
        content = manager.render_template(
            "greeting_001",
            {"buyer_name": "John"},
        )
        
        assert content is not None
        assert "[project_summary]" in content or "John" in content

    def test_render_template_with_subject(self, manager):
        """测试渲染带主题的模板"""
        result = manager.render_template_with_subject(
            "greeting_001",
            {
                "buyer_name": "John",
                "project_summary": "Logo design",
                "seller_name": "Jane",
            },
        )
        
        assert result is not None
        assert "subject" in result
        assert "content" in result

    def test_render_non_existent_template(self, manager):
        """测试渲染不存在的模板"""
        content = manager.render_template("non_existent", {})
        assert content is None

    def test_suggest_template_greeting(self, manager):
        """测试推荐模板 - 问候"""
        suggestions = manager.suggest_template("Hello, I'm interested in your services")
        assert len(suggestions) > 0
        assert any(t.type == MessageTemplateType.GREETING for t in suggestions)

    def test_suggest_template_quotation(self, manager):
        """测试推荐模板 - 报价"""
        suggestions = manager.suggest_template("What's your price for this project?")
        assert len(suggestions) > 0
        assert any(t.type == MessageTemplateType.QUOTATION for t in suggestions)

    def test_suggest_template_delivery(self, manager):
        """测试推荐模板 - 交付"""
        suggestions = manager.suggest_template("Your project is ready for delivery")
        assert len(suggestions) > 0
        assert any(t.type == MessageTemplateType.DELIVERY for t in suggestions)

    def test_suggest_template_revision(self, manager):
        """测试推荐模板 - 修改"""
        suggestions = manager.suggest_template("I need some revisions on the work")
        assert len(suggestions) > 0
        assert any(t.type == MessageTemplateType.REVISION for t in suggestions)

    def test_add_template(self, manager):
        """测试添加模板"""
        new_template = MessageTemplate(
            id="custom_001",
            name="Custom Template",
            type=MessageTemplateType.CUSTOM,
            content="Hello {name}! Welcome to our service.",
            variables=["name"],
        )
        
        manager.add_template(new_template)
        
        retrieved = manager.get_template("custom_001")
        assert retrieved is not None
        assert retrieved.name == "Custom Template"

    def test_update_template(self, manager):
        """测试更新模板"""
        result = manager.update_template(
            "greeting_001",
            subject="Updated Subject",
        )
        
        assert result is True
        
        template = manager.get_template("greeting_001")
        assert template.subject == "Updated Subject"

    def test_update_non_existent_template(self, manager):
        """测试更新不存在的模板"""
        result = manager.update_template(
            "non_existent",
            subject="New Subject",
        )
        
        assert result is False

    def test_delete_template(self, manager):
        """测试删除模板"""
        result = manager.delete_template("greeting_001")
        assert result is True
        
        template = manager.get_template("greeting_001")
        assert template.is_active is False

    def test_delete_non_existent_template(self, manager):
        """测试删除不存在的模板"""
        result = manager.delete_template("non_existent")
        assert result is False

    def test_create_custom_message(self, manager):
        """测试创建自定义消息"""
        message = manager.create_custom_message(
            message_type=MessageTemplateType.GREETING,
            buyer_name="John",
            seller_name="Jane",
            project_summary="Test project",
        )
        
        assert message is not None
        assert "John" in message
        assert "Jane" in message

    def test_create_custom_message_no_templates(self, manager):
        """测试创建无模板的自定义消息"""
        manager._templates.clear()
        
        message = manager.create_custom_message(
            message_type=MessageTemplateType.GREETING,
            buyer_name="John",
            seller_name="Jane",
        )
        
        assert message is not None
        assert "John" in message

    def test_list_templates(self, manager):
        """测试列出模板"""
        templates = manager.list_templates()
        assert len(templates) > 0
        assert all(t.is_active for t in templates)

    def test_message_template_type_enum(self):
        """测试消息模板类型枚举"""
        assert MessageTemplateType.GREETING.value == "greeting"
        assert MessageTemplateType.QUOTATION.value == "quotation"
        assert MessageTemplateType.ORDER_CONFIRMATION.value == "order_confirmation"
        assert MessageTemplateType.DELIVERY.value == "delivery"
        assert MessageTemplateType.REVISION.value == "revision"
        assert MessageTemplateType.FOLLOW_UP.value == "follow_up"
        assert MessageTemplateType.THANK_YOU.value == "thank_you"
        assert MessageTemplateType.CUSTOM.value == "custom"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
