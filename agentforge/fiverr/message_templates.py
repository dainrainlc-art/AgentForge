"""
Fiverr Message Templates - Professional message templates for various scenarios
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum
import re


class MessageTemplateType(str, Enum):
    GREETING = "greeting"
    QUOTATION = "quotation"
    ORDER_CONFIRMATION = "order_confirmation"
    DELIVERY = "delivery"
    REVISION = "revision"
    FOLLOW_UP = "follow_up"
    THANK_YOU = "thank_you"
    CUSTOM = "custom"


class MessageTemplate(BaseModel):
    """Message template model"""
    id: str
    name: str
    type: MessageTemplateType
    subject: Optional[str] = None
    content: str
    variables: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class MessageTemplateManager:
    """Manage message templates for Fiverr communication"""
    
    DEFAULT_TEMPLATES = [
        {
            "id": "greeting_001",
            "name": "Initial Greeting",
            "type": MessageTemplateType.GREETING,
            "subject": "Welcome! Let's discuss your project",
            "content": """Hi {buyer_name},

Thank you for reaching out! I'm excited to help you with your project.

I've reviewed your requirements and I believe I can deliver exactly what you're looking for. Here's what I can offer:

{project_summary}

I'm available to discuss further details at your convenience. Feel free to share any specific requirements or questions you might have.

Looking forward to working with you!

Best regards,
{seller_name}""",
            "variables": ["buyer_name", "project_summary", "seller_name"]
        },
        {
            "id": "quotation_001",
            "name": "Quotation Follow-up",
            "type": MessageTemplateType.QUOTATION,
            "subject": "Your Project Quotation",
            "content": """Hi {buyer_name},

Thank you for your interest! Based on our discussion, here's a detailed quotation for your project:

Project: {project_title}
Total: ${total_price}
Delivery: {delivery_days} days
Revisions: {revision_count} included

What's included:
{deliverables_list}

This quotation is valid until {valid_until}.

If you have any questions or would like to adjust any aspect of the proposal, please let me know. I'm happy to accommodate your needs.

Ready to get started? Just place your order and we'll begin!

Best regards,
{seller_name}""",
            "variables": ["buyer_name", "project_title", "total_price", "delivery_days", "revision_count", "deliverables_list", "valid_until", "seller_name"]
        },
        {
            "id": "order_confirm_001",
            "name": "Order Confirmation",
            "type": MessageTemplateType.ORDER_CONFIRMATION,
            "subject": "Order Confirmed - Let's Get Started!",
            "content": """Hi {buyer_name},

Great news! Your order has been confirmed and I'm ready to start working on your project.

Order Details:
- Order ID: {order_id}
- Project: {project_title}
- Delivery Date: {delivery_date}

Next Steps:
1. I'll begin working on your project immediately
2. You'll receive updates on progress
3. Initial draft will be shared for your review

If you have any additional requirements or files to share, please send them now.

Thank you for trusting me with your project!

Best regards,
{seller_name}""",
            "variables": ["buyer_name", "order_id", "project_title", "delivery_date", "seller_name"]
        },
        {
            "id": "delivery_001",
            "name": "Project Delivery",
            "type": MessageTemplateType.DELIVERY,
            "subject": "Your Project is Ready!",
            "content": """Hi {buyer_name},

I'm pleased to inform you that your project is complete and ready for delivery!

Project: {project_title}
Order ID: {order_id}

Deliverables:
{deliverables_list}

Please review the work and let me know if you need any adjustments. I'm committed to ensuring your complete satisfaction.

If everything looks good, I'd really appreciate your feedback and a 5-star review!

Thank you for the opportunity to work with you.

Best regards,
{seller_name}""",
            "variables": ["buyer_name", "project_title", "order_id", "deliverables_list", "seller_name"]
        },
        {
            "id": "revision_001",
            "name": "Revision Completed",
            "type": MessageTemplateType.REVISION,
            "subject": "Revisions Complete - Please Review",
            "content": """Hi {buyer_name},

I've completed the revisions you requested for your project.

Changes Made:
{revision_notes}

Please review the updated work and let me know if there's anything else you'd like me to adjust. Your satisfaction is my priority!

Revisions remaining: {revisions_remaining}

Best regards,
{seller_name}""",
            "variables": ["buyer_name", "revision_notes", "revisions_remaining", "seller_name"]
        },
        {
            "id": "follow_up_001",
            "name": "Order Follow-up",
            "type": MessageTemplateType.FOLLOW_UP,
            "subject": "Checking In on Your Order",
            "content": """Hi {buyer_name},

I wanted to check in on your order and make sure everything is progressing as expected.

Current Status: {order_status}
Progress: {progress_percentage}%

{progress_notes}

Do you have any questions or additional requirements? I'm here to help ensure your project turns out exactly as you envisioned.

Best regards,
{seller_name}""",
            "variables": ["buyer_name", "order_status", "progress_percentage", "progress_notes", "seller_name"]
        },
        {
            "id": "thank_you_001",
            "name": "Thank You After Completion",
            "type": MessageTemplateType.THANK_YOU,
            "subject": "Thank You for Your Order!",
            "content": """Hi {buyer_name},

Thank you so much for completing your order with me! It was a pleasure working with you on {project_title}.

I hope you're satisfied with the results. If you need any future assistance or have questions about the deliverables, please don't hesitate to reach out.

If you're happy with my work, I'd be incredibly grateful for a positive review. Your feedback helps me improve and grow!

Looking forward to working with you again!

Best regards,
{seller_name}""",
            "variables": ["buyer_name", "project_title", "seller_name"]
        },
        {
            "id": "price_negotiation_001",
            "name": "Price Negotiation",
            "type": MessageTemplateType.CUSTOM,
            "subject": "Let's Find the Right Price",
            "content": """Hi {buyer_name},

Thank you for your interest in my services! I understand budget is an important factor, and I'm happy to work with you to find a solution that fits.

Original Quote: ${original_price}

Here are some options we can consider:
{price_options}

Each option is designed to deliver quality results within your budget. Let me know which works best for you, or if you'd like to discuss a custom package.

Best regards,
{seller_name}""",
            "variables": ["buyer_name", "original_price", "price_options", "seller_name"]
        }
    ]
    
    def __init__(self):
        self._templates: Dict[str, MessageTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default templates"""
        for template_data in self.DEFAULT_TEMPLATES:
            template = MessageTemplate(**template_data)
            self._templates[template.id] = template
        
        logger.info(f"Loaded {len(self._templates)} default message templates")
    
    def get_template(self, template_id: str) -> Optional[MessageTemplate]:
        """Get template by ID"""
        return self._templates.get(template_id)
    
    def get_templates_by_type(self, template_type: MessageTemplateType) -> List[MessageTemplate]:
        """Get all templates of a specific type"""
        return [
            t for t in self._templates.values()
            if t.type == template_type and t.is_active
        ]
    
    def list_templates(self) -> List[MessageTemplate]:
        """List all active templates"""
        return [t for t in self._templates.values() if t.is_active]
    
    def add_template(self, template: MessageTemplate) -> None:
        """Add a new template"""
        self._templates[template.id] = template
        logger.info(f"Added template: {template.name}")
    
    def update_template(self, template_id: str, **kwargs) -> bool:
        """Update an existing template"""
        if template_id not in self._templates:
            return False
        
        template = self._templates[template_id]
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.now()
        logger.info(f"Updated template: {template.name}")
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template (soft delete)"""
        if template_id not in self._templates:
            return False
        
        self._templates[template_id].is_active = False
        logger.info(f"Deactivated template: {template_id}")
        return True
    
    def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """Render a template with variables"""
        template = self.get_template(template_id)
        
        if not template:
            logger.error(f"Template not found: {template_id}")
            return None
        
        content = template.content
        
        for var in template.variables:
            placeholder = "{" + var + "}"
            value = variables.get(var, f"[{var}]")
            content = content.replace(placeholder, str(value))
        
        return content
    
    def render_template_with_subject(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """Render template with subject"""
        template = self.get_template(template_id)
        
        if not template:
            return None
        
        content = self.render_template(template_id, variables)
        subject = template.subject
        
        if subject:
            for var in template.variables:
                placeholder = "{" + var + "}"
                value = variables.get(var, f"[{var}]")
                subject = subject.replace(placeholder, str(value))
        
        return {
            "subject": subject,
            "content": content
        }
    
    def create_custom_message(
        self,
        message_type: MessageTemplateType,
        buyer_name: str,
        seller_name: str,
        **kwargs
    ) -> str:
        """Create a custom message based on type"""
        templates = self.get_templates_by_type(message_type)
        
        if not templates:
            return f"Hi {buyer_name},\n\nThank you for your message. I'll get back to you shortly.\n\nBest regards,\n{seller_name}"
        
        template = templates[0]
        variables = {
            "buyer_name": buyer_name,
            "seller_name": seller_name,
            **kwargs
        }
        
        return self.render_template(template.id, variables) or ""
    
    def suggest_template(self, context: str) -> List[MessageTemplate]:
        """Suggest templates based on context"""
        context_lower = context.lower()
        suggestions = []
        
        keywords = {
            MessageTemplateType.GREETING: ["hello", "hi", "new", "first", "initial", "start"],
            MessageTemplateType.QUOTATION: ["price", "quote", "cost", "budget", "rate"],
            MessageTemplateType.ORDER_CONFIRMATION: ["order", "confirmed", "start", "begin"],
            MessageTemplateType.DELIVERY: ["deliver", "complete", "done", "finished", "ready"],
            MessageTemplateType.REVISION: ["revision", "change", "modify", "update", "fix"],
            MessageTemplateType.FOLLOW_UP: ["follow", "check", "status", "progress", "update"],
            MessageTemplateType.THANK_YOU: ["thank", "complete", "finish", "done", "review"],
        }
        
        for template_type, words in keywords.items():
            if any(word in context_lower for word in words):
                suggestions.extend(self.get_templates_by_type(template_type))
        
        return suggestions[:3]


message_template_manager = MessageTemplateManager()
