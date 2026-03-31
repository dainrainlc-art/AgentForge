"""
AgentForge API Documentation Generator
自动生成 API 文档和 SDK
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json
import yaml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from loguru import logger


class APIDocGenerator:
    def __init__(self, app: Optional[FastAPI] = None):
        self.app = app
        self.openapi_schema: Optional[Dict[str, Any]] = None
    
    def generate_openapi(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 schema"""
        if not self.app:
            raise ValueError("FastAPI app not configured")
        
        if self.openapi_schema is None:
            self.openapi_schema = get_openapi(
                title=self.app.title,
                version=self.app.version,
                description=self.app.description,
                routes=self.app.routes,
            )
        
        return self.openapi_schema
    
    def export_openapi_json(self, output_path: str = "docs/api/openapi.json") -> bool:
        """Export OpenAPI schema to JSON file"""
        try:
            schema = self.generate_openapi()
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            
            logger.info(f"OpenAPI schema exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export OpenAPI JSON: {e}")
            return False
    
    def export_openapi_yaml(self, output_path: str = "docs/api/openapi.yaml") -> bool:
        """Export OpenAPI schema to YAML file"""
        try:
            schema = self.generate_openapi()
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(schema, f, allow_unicode=True, default_flow_style=False)
            
            logger.info(f"OpenAPI schema exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export OpenAPI YAML: {e}")
            return False
    
    def generate_markdown_docs(self, output_path: str = "docs/api/README.md") -> bool:
        """Generate Markdown API documentation"""
        try:
            schema = self.generate_openapi()
            
            md_content = self._generate_markdown(schema)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"Markdown API docs generated at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate Markdown docs: {e}")
            return False
    
    def _generate_markdown(self, schema: Dict[str, Any]) -> str:
        """Generate Markdown content from OpenAPI schema"""
        lines = []
        
        # Title
        info = schema.get('info', {})
        lines.append(f"# {info.get('title', 'API Documentation')}")
        lines.append("")
        lines.append(f"**Version**: {info.get('version', '1.0.0')}")
        lines.append("")
        if info.get('description'):
            lines.append(info['description'])
            lines.append("")
        
        # Servers
        servers = schema.get('servers', [])
        if servers:
            lines.append("## 服务器")
            lines.append("")
            for server in servers:
                lines.append(f"- {server.get('url', '')} - {server.get('description', '')}")
            lines.append("")
        
        # Endpoints by tag
        paths = schema.get('paths', {})
        tags = {}
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    tag = details.get('tags', ['default'])[0]
                    if tag not in tags:
                        tags[tag] = []
                    tags[tag].append({
                        'path': path,
                        'method': method.upper(),
                        'details': details
                    })
        
        for tag, endpoints in sorted(tags.items()):
            lines.append(f"## {tag.replace('-', ' ').title()}")
            lines.append("")
            
            for endpoint in endpoints:
                path = endpoint['path']
                method = endpoint['method']
                details = endpoint['details']
                
                summary = details.get('summary', '')
                operation_id = details.get('operationId', '')
                
                lines.append(f"### `{method}` {path}")
                lines.append("")
                if summary:
                    lines.append(f"**{summary}**")
                    lines.append("")
                if operation_id:
                    lines.append(f"*Operation ID*: `{operation_id}`")
                    lines.append("")
                
                # Parameters
                parameters = details.get('parameters', [])
                if parameters:
                    lines.append("**Parameters**:")
                    lines.append("")
                    for param in parameters:
                        param_name = param.get('name', '')
                        param_in = param.get('in', '')
                        required = param.get('required', False)
                        param_schema = param.get('schema', {})
                        param_type = param_schema.get('type', 'string')
                        
                        req_mark = " **(required)**" if required else ""
                        lines.append(f"- `{param_name}` ({param_in}, {param_type}){req_mark}")
                        if param.get('description'):
                            lines.append(f"  - {param['description']}")
                    lines.append("")
                
                # Request body
                request_body = details.get('requestBody', {})
                if request_body:
                    lines.append("**Request Body**:")
                    lines.append("")
                    content = request_body.get('content', {})
                    if 'application/json' in content:
                        schema_ref = content['application/json'].get('schema', {})
                        lines.append(f"Content-Type: `application/json`")
                        lines.append("")
                        if 'properties' in schema_ref:
                            for prop_name, prop_details in schema_ref['properties'].items():
                                prop_type = prop_details.get('type', 'string')
                                prop_required = prop_name in schema_ref.get('required', [])
                                req_mark = " **(required)**" if prop_required else ""
                                lines.append(f"- `{prop_name}` ({prop_type}){req_mark}")
                                if prop_details.get('description'):
                                    lines.append(f"  - {prop_details['description']}")
                    lines.append("")
                
                # Responses
                responses = details.get('responses', {})
                if responses:
                    lines.append("**Responses**:")
                    lines.append("")
                    for status_code, response in sorted(responses.items()):
                        description = response.get('description', '')
                        lines.append(f"- `{status_code}` - {description}")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
        
        # Authentication
        components = schema.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        if security_schemes:
            lines.append("## 认证方式")
            lines.append("")
            for scheme_name, scheme_details in security_schemes.items():
                scheme_type = scheme_details.get('type', '')
                lines.append(f"### {scheme_name}")
                lines.append("")
                lines.append(f"- **Type**: {scheme_type}")
                if scheme_details.get('description'):
                    lines.append(f"- {scheme_details['description']}")
                lines.append("")
        
        return '\n'.join(lines)
    
    def generate_sdk(
        self,
        language: str = "python",
        output_path: str = "sdk"
    ) -> bool:
        """Generate SDK client code"""
        if language == "python":
            return self._generate_python_sdk(output_path)
        elif language == "typescript":
            return self._generate_typescript_sdk(output_path)
        else:
            logger.error(f"Unsupported language: {language}")
            return False
    
    def _generate_python_sdk(self, output_path: str) -> bool:
        """Generate Python SDK"""
        try:
            schema = self.generate_openapi()
            
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate client.py
            client_code = self._generate_python_client(schema)
            
            client_file = output_dir / "client.py"
            with open(client_file, 'w', encoding='utf-8') as f:
                f.write(client_code)
            
            # Generate __init__.py
            init_file = output_dir / "__init__.py"
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(f'"""Auto-generated SDK for {schema["info"]["title"]}"""\n')
                f.write(f'__version__ = "{schema["info"].get("version", "1.0.0")}"\n')
                f.write('from .client import APIClient\n')
            
            logger.info(f"Python SDK generated at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate Python SDK: {e}")
            return False
    
    def _generate_python_client(self, schema: Dict[str, Any]) -> str:
        """Generate Python client code"""
        lines = []
        
        lines.append('"""')
        lines.append(f'Auto-generated Python SDK for {schema["info"]["title"]}')
        lines.append(f'Version: {schema["info"].get("version", "1.0.0")}')
        lines.append('"""')
        lines.append('')
        lines.append('import httpx')
        lines.append('from typing import Dict, Any, Optional')
        lines.append('')
        lines.append('')
        lines.append('class APIClient:')
        lines.append(f'    """Client for {schema["info"]["title"]}"""')
        lines.append('')
        lines.append('    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):')
        lines.append('        self.base_url = base_url.rstrip("/")')
        lines.append('        self.api_key = api_key')
        lines.append('        self._client = httpx.AsyncClient(base_url=self.base_url)')
        lines.append('')
        
        # Add authentication header method
        lines.append('    async def _get_headers(self) -> Dict[str, str]:')
        lines.append('        headers = {"Content-Type": "application/json"}')
        lines.append('        if self.api_key:')
        lines.append('            headers["Authorization"] = f"Bearer {self.api_key}"')
        lines.append('        return headers')
        lines.append('')
        
        # Generate methods from endpoints
        paths = schema.get('paths', {})
        for path, methods in sorted(paths.items()):
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    method_code = self._generate_method(path, method, details)
                    lines.extend(method_code)
        
        lines.append('    async def close(self):')
        lines.append('        """Close the HTTP client"""')
        lines.append('        await self._client.aclose()')
        lines.append('')
        lines.append('    async def __aenter__(self):')
        lines.append('        return self')
        lines.append('')
        lines.append('    async def __aexit__(self, *args):')
        lines.append('        await self.close()')
        
        return '\n'.join(lines)
    
    def _generate_method(
        self,
        path: str,
        method: str,
        details: Dict[str, Any]
    ) -> list:
        """Generate a single method"""
        lines = []
        
        # Method name
        operation_id = details.get('operationId', f'{method}_{path.replace("/", "_")}')
        operation_id = operation_id.replace('-', '_')
        
        # Summary as docstring
        summary = details.get('summary', '')
        
        # Parameters
        parameters = details.get('parameters', [])
        path_params = [p for p in parameters if p.get('in') == 'path']
        query_params = [p for p in parameters if p.get('in') == 'query']
        
        # Method signature
        method_args = ['self']
        for param in path_params + query_params:
            param_name = param.get('name', '')
            param_schema = param.get('schema', {})
            param_type = param_schema.get('type', 'string')
            default = param_schema.get('default')
            
            if default is not None:
                method_args.append(f"{param_name}: {param_type} = {repr(default)}")
            else:
                method_args.append(f"{param_name}: {param_type}")
        
        if details.get('requestBody'):
            method_args.append("data: Dict[str, Any]")
        
        method_signature = f"    async def {operation_id}({', '.join(method_args)}) -> Dict[str, Any]:"
        lines.append(method_signature)
        
        # Docstring
        lines.append(f'        """{summary}"""')
        
        # URL formatting
        url_path = path
        for param in path_params:
            param_name = param.get('name', '')
            url_path = url_path.replace(f'{{{param_name}}}', f'{{{param_name}}}')
        
        # Build request
        lines.append(f'        url = f"{{self.base_url}}{url_path}"')
        lines.append('        headers = await self._get_headers()')
        lines.append('')
        
        if query_params:
            lines.append('        params = {')
            for param in query_params:
                param_name = param.get('name', '')
                lines.append(f'            "{param_name}": {param_name},')
            lines.append('        }')
            lines.append('')
        
        # Make request
        lines.append('        async with self._client as client:')
        if method == 'get':
            if query_params:
                lines.append('            response = await client.get(url, headers=headers, params=params)')
            else:
                lines.append('            response = await client.get(url, headers=headers)')
        elif method == 'post':
            if query_params:
                lines.append('            response = await client.post(url, headers=headers, params=params, json=data)')
            else:
                lines.append('            response = await client.post(url, headers=headers, json=data)')
        # Add other methods as needed
        
        lines.append('            response.raise_for_status()')
        lines.append('            return response.json()')
        lines.append('')
        
        return lines
    
    def _generate_typescript_sdk(self, output_path: str) -> bool:
        """Generate TypeScript SDK"""
        logger.warning("TypeScript SDK generation not yet implemented")
        return False


def init_api_docs(app: Optional[FastAPI] = None) -> APIDocGenerator:
    """Initialize API documentation generator"""
    generator = APIDocGenerator(app)
    return generator
