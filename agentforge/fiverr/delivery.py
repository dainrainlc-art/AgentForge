"""
AgentForge Fiverr Delivery Automation Module
Handles deliverable packaging and format standardization
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from loguru import logger

from agentforge.llm.model_router import ModelRouter


class DeliveryFormat(str, Enum):
    ZIP = "zip"
    RAR = "rar"
    TAR_GZ = "tar.gz"
    FOLDER = "folder"


class DeliverableType(str, Enum):
    SOURCE_CODE = "source_code"
    DOCUMENTATION = "documentation"
    DESIGN_ASSETS = "design_assets"
    DATA_FILES = "data_files"
    CONFIGURATION = "configuration"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGES = "images"
    MIXED = "mixed"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    FAILED = "failed"


class DeliverableFile(BaseModel):
    path: str
    size: int
    file_type: str
    category: DeliverableType
    is_required: bool = True
    description: Optional[str] = None


class DeliveryPackage(BaseModel):
    id: str
    order_id: str
    name: str
    format: DeliveryFormat = DeliveryFormat.ZIP
    files: List[DeliverableFile] = Field(default_factory=list)
    total_size: int = 0
    status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    delivery_path: Optional[str] = None
    readme_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeliveryTemplate(BaseModel):
    id: str
    name: str
    service_type: str
    required_files: List[str]
    optional_files: List[str] = Field(default_factory=list)
    folder_structure: Dict[str, Any] = Field(default_factory=dict)
    readme_template: str
    file_naming_convention: str = "descriptive"


class DeliveryValidator:
    def __init__(self):
        self.llm = ModelRouter()
    
    def validate_files(
        self,
        files: List[DeliverableFile],
        template: Optional[DeliveryTemplate] = None
    ) -> Dict[str, Any]:
        result = {
            "valid": True,
            "missing_required": [],
            "invalid_files": [],
            "warnings": []
        }
        
        if template:
            required_paths = set(template.required_files)
            actual_paths = {f.path for f in files}
            
            missing = required_paths - actual_paths
            if missing:
                result["missing_required"] = list(missing)
                result["valid"] = False
        
        for file in files:
            if file.size == 0:
                result["warnings"].append(f"Empty file: {file.path}")
            
            if not os.path.exists(file.path):
                result["invalid_files"].append({
                    "path": file.path,
                    "reason": "File does not exist"
                })
                result["valid"] = False
        
        return result
    
    def categorize_file(self, filename: str) -> DeliverableType:
        ext = os.path.splitext(filename)[1].lower()
        
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'}
        doc_extensions = {'.md', '.txt', '.pdf', '.doc', '.docx', '.rst'}
        design_extensions = {'.psd', '.ai', '.sketch', '.fig', '.xd', '.svg'}
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.aac'}
        data_extensions = {'.json', '.csv', '.xml', '.yaml', '.yml', '.sql'}
        config_extensions = {'.env', '.ini', '.conf', '.cfg', '.toml'}
        
        if ext in code_extensions:
            return DeliverableType.SOURCE_CODE
        elif ext in doc_extensions:
            return DeliverableType.DOCUMENTATION
        elif ext in design_extensions:
            return DeliverableType.DESIGN_ASSETS
        elif ext in image_extensions:
            return DeliverableType.IMAGES
        elif ext in video_extensions:
            return DeliverableType.VIDEO
        elif ext in audio_extensions:
            return DeliverableType.AUDIO
        elif ext in data_extensions:
            return DeliverableType.DATA_FILES
        elif ext in config_extensions:
            return DeliverableType.CONFIGURATION
        else:
            return DeliverableType.MIXED
    
    async def generate_readme(
        self,
        package: DeliveryPackage,
        order_details: Optional[Dict[str, Any]] = None
    ) -> str:
        file_list = "\n".join([
            f"- `{f.path}` ({self._format_size(f.size)}) - {f.description or f.category.value}"
            for f in package.files
        ])
        
        prompt = f"""Generate a professional README.md for a Fiverr delivery package.

Package Name: {package.name}
Order ID: {package.order_id}
Delivery Date: {package.created_at.strftime('%Y-%m-%d')}

Files Included:
{file_list}

{"Order Details: " + str(order_details) if order_details else ""}

Create a README that includes:
1. Project title and brief description
2. Installation/setup instructions
3. Usage guide
4. File structure explanation
5. Requirements/dependencies
6. Support/contact information

README content:"""

        response = await self.llm.chat_with_failover(
            message=prompt,
            task_type="creative"
        )
        return response.strip()
    
    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class DeliveryPackager:
    def __init__(self, output_dir: str = None):
        import tempfile
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="fiverr_deliveries_")
        self.validator = DeliveryValidator()
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def create_package(
        self,
        order_id: str,
        files: List[str],
        package_name: Optional[str] = None,
        delivery_format: DeliveryFormat = DeliveryFormat.ZIP,
        template: Optional[DeliveryTemplate] = None,
        include_readme: bool = True,
        order_details: Optional[Dict[str, Any]] = None
    ) -> DeliveryPackage:
        package_id = f"pkg_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if not package_name:
            package_name = f"delivery_{order_id}"
        
        deliverable_files = []
        for file_path in files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                deliverable_files.append(DeliverableFile(
                    path=file_path,
                    size=stat.st_size,
                    file_type=os.path.splitext(file_path)[1],
                    category=self.validator.categorize_file(file_path)
                ))
        
        package = DeliveryPackage(
            id=package_id,
            order_id=order_id,
            name=package_name,
            format=delivery_format,
            files=deliverable_files,
            total_size=sum(f.size for f in deliverable_files)
        )
        
        validation = self.validator.validate_files(deliverable_files, template)
        if not validation["valid"]:
            package.status = DeliveryStatus.FAILED
            package.metadata["validation_errors"] = validation
            return package
        
        package.status = DeliveryStatus.PREPARING
        
        try:
            if include_readme:
                package.readme_content = await self.validator.generate_readme(
                    package, order_details
                )
            
            output_path = await self._pack_files(package, template)
            package.delivery_path = output_path
            package.status = DeliveryStatus.READY
            
        except Exception as e:
            logger.error(f"Failed to create package: {e}")
            package.status = DeliveryStatus.FAILED
            package.metadata["error"] = str(e)
        
        return package
    
    async def _pack_files(
        self,
        package: DeliveryPackage,
        template: Optional[DeliveryTemplate] = None
    ) -> str:
        temp_dir = tempfile.mkdtemp(prefix=f"fiverr_{package.order_id}_")
        
        try:
            if template and template.folder_structure:
                self._create_folder_structure(temp_dir, template.folder_structure)
            
            for file in package.files:
                dest_dir = temp_dir
                
                if template and template.folder_structure:
                    dest_subdir = self._find_destination_folder(
                        file.path, template.folder_structure
                    )
                    if dest_subdir:
                        dest_dir = os.path.join(temp_dir, dest_subdir)
                        os.makedirs(dest_dir, exist_ok=True)
                
                dest_path = os.path.join(dest_dir, os.path.basename(file.path))
                shutil.copy2(file.path, dest_path)
            
            if package.readme_content:
                readme_path = os.path.join(temp_dir, "README.md")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(package.readme_content)
            
            output_filename = f"{package.name}.{package.format.value}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            if package.format == DeliveryFormat.ZIP:
                self._create_zip(temp_dir, output_path)
            elif package.format == DeliveryFormat.TAR_GZ:
                self._create_tar_gz(temp_dir, output_path)
            else:
                shutil.copytree(temp_dir, output_path)
            
            return output_path
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _create_folder_structure(self, base_dir: str, structure: Dict[str, Any]):
        for name, content in structure.items():
            path = os.path.join(base_dir, name)
            if isinstance(content, dict):
                os.makedirs(path, exist_ok=True)
                self._create_folder_structure(path, content)
            else:
                os.makedirs(path, exist_ok=True)
    
    def _find_destination_folder(
        self,
        file_path: str,
        structure: Dict[str, Any],
        current_path: str = ""
    ) -> Optional[str]:
        file_type = self.validator.categorize_file(file_path)
        
        type_to_folder = {
            DeliverableType.SOURCE_CODE: "src",
            DeliverableType.DOCUMENTATION: "docs",
            DeliverableType.DESIGN_ASSETS: "assets",
            DeliverableType.IMAGES: "images",
            DeliverableType.VIDEO: "videos",
            DeliverableType.AUDIO: "audio",
            DeliverableType.DATA_FILES: "data",
            DeliverableType.CONFIGURATION: "config",
        }
        
        return type_to_folder.get(file_type)
    
    def _create_zip(self, source_dir: str, output_path: str):
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
    
    def _create_tar_gz(self, source_dir: str, output_path: str):
        import tarfile
        with tarfile.open(output_path, 'w:gz') as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
    
    def get_package_info(self, package_path: str) -> Dict[str, Any]:
        if not os.path.exists(package_path):
            return {"error": "Package not found"}
        
        stat = os.stat(package_path)
        
        return {
            "path": package_path,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "format": os.path.splitext(package_path)[1].lstrip('.')
        }


class DeliveryAutomation:
    def __init__(self, output_dir: str = None):
        self.packager = DeliveryPackager(output_dir)
        self.validator = DeliveryValidator()
        self._templates: Dict[str, DeliveryTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        self._templates["web_development"] = DeliveryTemplate(
            id="web_development",
            name="Web Development Project",
            service_type="web",
            required_files=["index.html", "style.css", "script.js"],
            optional_files=["README.md", "package.json", ".gitignore"],
            folder_structure={
                "src": {"js": {}, "css": {}, "assets": {}},
                "docs": {},
                "tests": {}
            },
            readme_template="web_project_readme"
        )
        
        self._templates["python_project"] = DeliveryTemplate(
            id="python_project",
            name="Python Project",
            service_type="python",
            required_files=["main.py", "requirements.txt"],
            optional_files=["README.md", "setup.py", "config.yaml"],
            folder_structure={
                "src": {},
                "tests": {},
                "docs": {},
                "config": {}
            },
            readme_template="python_project_readme"
        )
        
        self._templates["data_analysis"] = DeliveryTemplate(
            id="data_analysis",
            name="Data Analysis Project",
            service_type="data",
            required_files=["analysis.ipynb", "data.csv"],
            optional_files=["README.md", "report.pdf", "visualizations/"],
            folder_structure={
                "data": {"raw": {}, "processed": {}},
                "notebooks": {},
                "reports": {},
                "visualizations": {}
            },
            readme_template="data_analysis_readme"
        )
    
    def get_template(self, service_type: str) -> Optional[DeliveryTemplate]:
        return self._templates.get(service_type)
    
    def add_template(self, template: DeliveryTemplate):
        self._templates[template.id] = template
    
    async def prepare_delivery(
        self,
        order_id: str,
        files: List[str],
        service_type: Optional[str] = None,
        custom_name: Optional[str] = None,
        order_details: Optional[Dict[str, Any]] = None
    ) -> DeliveryPackage:
        template = None
        if service_type:
            template = self.get_template(service_type)
        
        package = await self.packager.create_package(
            order_id=order_id,
            files=files,
            package_name=custom_name,
            template=template,
            include_readme=True,
            order_details=order_details
        )
        
        return package
    
    async def validate_delivery(
        self,
        files: List[str],
        service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        template = None
        if service_type:
            template = self.get_template(service_type)
        
        deliverable_files = []
        for file_path in files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                deliverable_files.append(DeliverableFile(
                    path=file_path,
                    size=stat.st_size,
                    file_type=os.path.splitext(file_path)[1],
                    category=self.validator.categorize_file(file_path)
                ))
        
        return self.validator.validate_files(deliverable_files, template)
    
    def list_templates(self) -> List[Dict[str, str]]:
        return [
            {"id": t.id, "name": t.name, "service_type": t.service_type}
            for t in self._templates.values()
        ]


delivery_automation = DeliveryAutomation()
