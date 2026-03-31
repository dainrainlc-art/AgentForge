"""
AgentForge GitHub Integration
项目仓库自动创建和管理
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import httpx
from loguru import logger

from agentforge.config import settings


class RepositoryVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class RepositoryTemplate(str, Enum):
    PYTHON = "python"
    NODEJS = "nodejs"
    REACT = "react"
    MINIMAL = "minimal"
    CUSTOM = "custom"


class ProjectType(str, Enum):
    WEB_APP = "web_app"
    API = "api"
    CLI = "cli"
    LIBRARY = "library"
    DATA_SCIENCE = "data_science"
    MOBILE = "mobile"


class RepositoryConfig(BaseModel):
    name: str
    description: str = ""
    visibility: RepositoryVisibility = RepositoryVisibility.PRIVATE
    template: RepositoryTemplate = RepositoryTemplate.MINIMAL
    project_type: ProjectType = ProjectType.WEB_APP
    add_gitignore: bool = True
    add_readme: bool = True
    add_license: bool = True
    license_type: str = "mit"
    add_ci: bool = True
    branches: List[str] = Field(default_factory=lambda: ["main", "develop"])
    topics: List[str] = Field(default_factory=list)
    homepage: Optional[str] = None
    wiki_enabled: bool = False
    issues_enabled: bool = True
    projects_enabled: bool = True


class Repository(BaseModel):
    id: int
    name: str
    full_name: str
    description: str
    html_url: str
    clone_url: str
    ssh_url: str
    visibility: str
    created_at: datetime
    updated_at: datetime
    default_branch: str


class GitHubClient:
    BASE_URL = "https://api.github.com"
    
    def __init__(
        self,
        token: Optional[str] = None,
        owner: Optional[str] = None
    ):
        self.token = token or getattr(settings, 'github_token', None)
        self.owner = owner or getattr(settings, 'github_repo_owner', None)
        
        if not self.token:
            logger.warning("GitHub token not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def create_repository(
        self,
        config: RepositoryConfig
    ) -> Optional[Repository]:
        if not self.token:
            logger.error("GitHub token not configured")
            return None
        
        try:
            payload = {
                "name": config.name,
                "description": config.description,
                "private": config.visibility == RepositoryVisibility.PRIVATE,
                "auto_init": config.add_readme,
                "gitignore_template": self._get_gitignore_template(config.project_type) if config.add_gitignore else None,
                "license_template": config.license_type if config.add_license else None,
                "has_wiki": config.wiki_enabled,
                "has_issues": config.issues_enabled,
                "has_projects": config.projects_enabled,
                "homepage": config.homepage,
                "topics": config.topics
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/user/repos",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    
                    repo = Repository(
                        id=data["id"],
                        name=data["name"],
                        full_name=data["full_name"],
                        description=data.get("description", ""),
                        html_url=data["html_url"],
                        clone_url=data["clone_url"],
                        ssh_url=data["ssh_url"],
                        visibility="private" if data["private"] else "public",
                        created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                        default_branch=data.get("default_branch", "main")
                    )
                    
                    if config.add_ci:
                        await self._add_ci_workflow(repo.full_name, config.project_type)
                    
                    if len(config.branches) > 1:
                        await self._create_branches(repo.full_name, config.branches)
                    
                    await self._add_branch_protection(repo.full_name, config.branches[0])
                    
                    logger.info(f"Created repository: {repo.html_url}")
                    return repo
                else:
                    error = response.json()
                    logger.error(f"Failed to create repository: {error.get('message', response.text)}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to create repository: {e}")
            return None
    
    async def create_repository_from_template(
        self,
        template_owner: str,
        template_repo: str,
        config: RepositoryConfig
    ) -> Optional[Repository]:
        if not self.token:
            return None
        
        try:
            payload = {
                "owner": self.owner,
                "name": config.name,
                "description": config.description,
                "private": config.visibility == RepositoryVisibility.PRIVATE,
                "include_all_branches": False
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/repos/{template_owner}/{template_repo}/generate",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    
                    return Repository(
                        id=data["id"],
                        name=data["name"],
                        full_name=data["full_name"],
                        description=data.get("description", ""),
                        html_url=data["html_url"],
                        clone_url=data["clone_url"],
                        ssh_url=data["ssh_url"],
                        visibility="private" if data["private"] else "public",
                        created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                        default_branch=data.get("default_branch", "main")
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to create repository from template: {e}")
            return None
    
    async def get_repository(self, repo_name: str) -> Optional[Repository]:
        if not self.token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/repos/{self.owner}/{repo_name}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return Repository(
                        id=data["id"],
                        name=data["name"],
                        full_name=data["full_name"],
                        description=data.get("description", ""),
                        html_url=data["html_url"],
                        clone_url=data["clone_url"],
                        ssh_url=data["ssh_url"],
                        visibility="private" if data["private"] else "public",
                        created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                        default_branch=data.get("default_branch", "main")
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get repository: {e}")
            return None
    
    async def list_repositories(
        self,
        per_page: int = 30,
        page: int = 1
    ) -> List[Repository]:
        if not self.token:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/user/repos",
                    headers=self._get_headers(),
                    params={
                        "per_page": per_page,
                        "page": page,
                        "sort": "updated"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        Repository(
                            id=repo["id"],
                            name=repo["name"],
                            full_name=repo["full_name"],
                            description=repo.get("description", ""),
                            html_url=repo["html_url"],
                            clone_url=repo["clone_url"],
                            ssh_url=repo["ssh_url"],
                            visibility="private" if repo["private"] else "public",
                            created_at=datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00")),
                            updated_at=datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00")),
                            default_branch=repo.get("default_branch", "main")
                        )
                        for repo in data
                    ]
                return []
                
        except Exception as e:
            logger.error(f"Failed to list repositories: {e}")
            return []
    
    async def delete_repository(self, repo_name: str) -> bool:
        if not self.token:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.BASE_URL}/repos/{self.owner}/{repo_name}",
                    headers=self._get_headers()
                )
                
                return response.status_code == 204
                
        except Exception as e:
            logger.error(f"Failed to delete repository: {e}")
            return False
    
    async def create_issue(
        self,
        repo_name: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        if not self.token:
            return None
        
        try:
            payload = {
                "title": title,
                "body": body,
                "labels": labels or [],
                "assignees": assignees or []
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/repos/{self.owner}/{repo_name}/issues",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 201:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None
    
    async def create_pull_request(
        self,
        repo_name: str,
        title: str,
        head: str,
        base: str,
        body: str = "",
        draft: bool = False
    ) -> Optional[Dict[str, Any]]:
        if not self.token:
            return None
        
        try:
            payload = {
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/repos/{self.owner}/{repo_name}/pulls",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 201:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return None
    
    async def add_file(
        self,
        repo_name: str,
        path: str,
        message: str,
        content: str,
        branch: str = "main"
    ) -> bool:
        if not self.token:
            return False
        
        try:
            import base64
            
            encoded_content = base64.b64encode(content.encode()).decode()
            
            payload = {
                "message": message,
                "content": encoded_content,
                "branch": branch
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.BASE_URL}/repos/{self.owner}/{repo_name}/contents/{path}",
                    headers=self._get_headers(),
                    json=payload
                )
                
                return response.status_code == 201
                
        except Exception as e:
            logger.error(f"Failed to add file: {e}")
            return False
    
    async def _create_branches(
        self,
        repo_full_name: str,
        branches: List[str]
    ) -> bool:
        if len(branches) <= 1:
            return True
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                ref_response = await client.get(
                    f"{self.BASE_URL}/repos/{repo_full_name}/git/ref/heads/main",
                    headers=self._get_headers()
                )
                
                if ref_response.status_code != 200:
                    return False
                
                sha = ref_response.json()["object"]["sha"]
                
                for branch in branches[1:]:
                    await client.post(
                        f"{self.BASE_URL}/repos/{repo_full_name}/git/refs",
                        headers=self._get_headers(),
                        json={
                            "ref": f"refs/heads/{branch}",
                            "sha": sha
                        }
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to create branches: {e}")
            return False
    
    async def _add_branch_protection(
        self,
        repo_full_name: str,
        branch: str
    ) -> bool:
        if not self.token:
            return False
        
        try:
            payload = {
                "required_status_checks": {
                    "strict": True,
                    "contexts": []
                },
                "enforce_admins": False,
                "required_pull_request_reviews": {
                    "dismiss_stale_reviews": True,
                    "require_code_owner_reviews": False,
                    "required_approving_review_count": 1
                },
                "restrictions": None
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.BASE_URL}/repos/{repo_full_name}/branches/{branch}/protection",
                    headers=self._get_headers(),
                    json=payload
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to add branch protection: {e}")
            return False
    
    async def _add_ci_workflow(
        self,
        repo_full_name: str,
        project_type: ProjectType
    ) -> bool:
        workflow_content = self._get_ci_workflow(project_type)
        
        return await self.add_file(
            repo_name=repo_full_name.split("/")[1],
            path=".github/workflows/ci.yml",
            message="Add CI workflow",
            content=workflow_content
        )
    
    def _get_gitignore_template(self, project_type: ProjectType) -> str:
        templates = {
            ProjectType.WEB_APP: "Node",
            ProjectType.API: "Python",
            ProjectType.CLI: "Python",
            ProjectType.LIBRARY: "Python",
            ProjectType.DATA_SCIENCE: "Python",
            ProjectType.MOBILE: "ReactNative"
        }
        return templates.get(project_type, "Python")
    
    def _get_ci_workflow(self, project_type: ProjectType) -> str:
        if project_type in [ProjectType.API, ProjectType.CLI, ProjectType.LIBRARY, ProjectType.DATA_SCIENCE]:
            return '''name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.12"
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src
    - name: Lint
      run: |
        ruff check src/
        black --check src/
'''
        else:
            return '''name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node
      uses: actions/setup-node@v3
      with:
        node-version: "18"
    - name: Install dependencies
      run: npm ci
    - name: Run tests
      run: npm test
    - name: Build
      run: npm run build
'''


class ProjectManager:
    def __init__(self):
        self.github = GitHubClient()
    
    async def create_project(
        self,
        name: str,
        description: str = "",
        project_type: ProjectType = ProjectType.WEB_APP,
        visibility: RepositoryVisibility = RepositoryVisibility.PRIVATE,
        template: RepositoryTemplate = RepositoryTemplate.MINIMAL,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> Optional[Repository]:
        config = RepositoryConfig(
            name=self._sanitize_repo_name(name),
            description=description,
            project_type=project_type,
            visibility=visibility,
            template=template,
            **(additional_config or {})
        )
        
        if template != RepositoryTemplate.MINIMAL:
            template_mapping = {
                RepositoryTemplate.PYTHON: ("owner", "python-template"),
                RepositoryTemplate.NODEJS: ("owner", "nodejs-template"),
                RepositoryTemplate.REACT: ("owner", "react-template"),
                RepositoryTemplate.CUSTOM: ("owner", "custom-template")
            }
            
            template_owner, template_repo = template_mapping.get(template, (None, None))
            
            if template_owner and template_repo:
                return await self.github.create_repository_from_template(
                    template_owner,
                    template_repo,
                    config
                )
        
        return await self.github.create_repository(config)
    
    def _sanitize_repo_name(self, name: str) -> str:
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '-', name.lower())
        sanitized = re.sub(r'-+', '-', sanitized)
        sanitized = sanitized.strip('-._')
        
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    async def setup_project_structure(
        self,
        repo_name: str,
        project_type: ProjectType
    ) -> bool:
        structure = self._get_project_structure(project_type)
        
        for path, content in structure.items():
            success = await self.github.add_file(
                repo_name=repo_name,
                path=path,
                message=f"Add {path}",
                content=content
            )
            if not success:
                logger.warning(f"Failed to add {path}")
        
        return True
    
    def _get_project_structure(self, project_type: ProjectType) -> Dict[str, str]:
        structures = {
            ProjectType.API: {
                "src/__init__.py": "",
                "src/api/__init__.py": "",
                "src/api/routes.py": '"""API Routes"""\n',
                "src/core/__init__.py": "",
                "src/core/config.py": '"""Configuration"""\n',
                "tests/__init__.py": "",
                "tests/test_api.py": '"""API Tests"""\n',
                "requirements.txt": "fastapi\nuvicorn\npytest\n",
                "Dockerfile": "FROM python:3.12-slim\n"
            },
            ProjectType.WEB_APP: {
                "src/components/App.tsx": 'export function App() { return <div>Hello</div>; }\n',
                "src/index.tsx": 'import { App } from "./components/App";\n',
                "package.json": '{"name": "app", "version": "1.0.0"}\n'
            },
            ProjectType.CLI: {
                "src/__init__.py": "",
                "src/cli.py": '"""CLI Entry Point"""\n',
                "tests/__init__.py": "",
                "requirements.txt": "click\npytest\n"
            }
        }
        
        return structures.get(project_type, {})
    
    async def get_project_status(self, repo_name: str) -> Dict[str, Any]:
        repo = await self.github.get_repository(repo_name)
        
        if not repo:
            return {"status": "not_found"}
        
        return {
            "status": "active",
            "name": repo.name,
            "url": repo.html_url,
            "visibility": repo.visibility,
            "default_branch": repo.default_branch,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat()
        }


class ReleaseInfo(BaseModel):
    tag_name: str
    name: str
    body: str
    draft: bool = False
    prerelease: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    html_url: Optional[str] = None


class WebhookConfig(BaseModel):
    url: str
    content_type: str = "json"
    secret: Optional[str] = None
    events: List[str] = Field(default_factory=lambda: ["push", "pull_request"])


class CodeSyncManager:
    def __init__(self, github_client: Optional[GitHubClient] = None):
        self.github = github_client or GitHubClient()
        self._sync_state: Dict[str, Dict[str, Any]] = {}
    
    async def sync_local_to_remote(
        self,
        repo_name: str,
        local_path: str,
        branch: str = "main",
        commit_message: str = "Auto-sync from local"
    ) -> bool:
        import os
        from pathlib import Path
        
        local_root = Path(local_path)
        if not local_root.exists():
            logger.error(f"Local path does not exist: {local_path}")
            return False
        
        files_to_sync = []
        for root, dirs, files in os.walk(local_root):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(local_root)
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                files_to_sync.append({
                    "path": str(relative_path),
                    "content": content
                })
        
        success_count = 0
        for file_info in files_to_sync:
            if await self.github.add_file(
                repo_name=repo_name,
                path=file_info["path"],
                message=f"{commit_message}: {file_info['path']}",
                content=file_info["content"],
                branch=branch
            ):
                success_count += 1
        
        logger.info(f"Synced {success_count}/{len(files_to_sync)} files to {repo_name}")
        return success_count > 0
    
    async def create_release(
        self,
        repo_name: str,
        version: str,
        release_notes: str,
        prerelease: bool = False,
        draft: bool = False
    ) -> Optional[ReleaseInfo]:
        if not self.github.token:
            return None
        
        try:
            payload = {
                "tag_name": f"v{version}",
                "name": f"Release v{version}",
                "body": release_notes,
                "draft": draft,
                "prerelease": prerelease,
                "generate_release_notes": False
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.github.BASE_URL}/repos/{self.github.owner}/{repo_name}/releases",
                    headers=self.github._get_headers(),
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return ReleaseInfo(
                        tag_name=data["tag_name"],
                        name=data["name"],
                        body=data.get("body", ""),
                        draft=data.get("draft", False),
                        prerelease=data.get("prerelease", False),
                        published_at=datetime.fromisoformat(data["published_at"].replace("Z", "+00:00")) if data.get("published_at") else None,
                        html_url=data.get("html_url")
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to create release: {e}")
            return None
    
    async def get_latest_release(self, repo_name: str) -> Optional[ReleaseInfo]:
        if not self.github.token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.github.BASE_URL}/repos/{self.github.owner}/{repo_name}/releases/latest",
                    headers=self.github._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return ReleaseInfo(
                        tag_name=data["tag_name"],
                        name=data["name"],
                        body=data.get("body", ""),
                        draft=data.get("draft", False),
                        prerelease=data.get("prerelease", False),
                        published_at=datetime.fromisoformat(data["published_at"].replace("Z", "+00:00")) if data.get("published_at") else None,
                        html_url=data.get("html_url")
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get latest release: {e}")
            return None
    
    async def list_releases(
        self,
        repo_name: str,
        per_page: int = 10
    ) -> List[ReleaseInfo]:
        if not self.github.token:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.github.BASE_URL}/repos/{self.github.owner}/{repo_name}/releases",
                    headers=self.github._get_headers(),
                    params={"per_page": per_page}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        ReleaseInfo(
                            tag_name=release["tag_name"],
                            name=release["name"],
                            body=release.get("body", ""),
                            draft=release.get("draft", False),
                            prerelease=release.get("prerelease", False),
                            published_at=datetime.fromisoformat(release["published_at"].replace("Z", "+00:00")) if release.get("published_at") else None,
                            html_url=release.get("html_url")
                        )
                        for release in data
                    ]
                return []
                
        except Exception as e:
            logger.error(f"Failed to list releases: {e}")
            return []
    
    async def setup_webhook(
        self,
        repo_name: str,
        config: WebhookConfig
    ) -> Optional[Dict[str, Any]]:
        if not self.github.token:
            return None
        
        try:
            payload = {
                "name": "web",
                "active": True,
                "events": config.events,
                "config": {
                    "url": config.url,
                    "content_type": config.content_type,
                    "secret": config.secret
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.github.BASE_URL}/repos/{self.github.owner}/{repo_name}/hooks",
                    headers=self.github._get_headers(),
                    json=payload
                )
                
                if response.status_code == 201:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to setup webhook: {e}")
            return None
    
    async def get_commit_history(
        self,
        repo_name: str,
        branch: str = "main",
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        if not self.github.token:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.github.BASE_URL}/repos/{self.github.owner}/{repo_name}/commits",
                    headers=self.github._get_headers(),
                    params={"sha": branch, "per_page": per_page}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "sha": commit["sha"][:7],
                            "message": commit["commit"]["message"],
                            "author": commit["commit"]["author"]["name"],
                            "date": commit["commit"]["author"]["date"],
                            "url": commit["html_url"]
                        }
                        for commit in data
                    ]
                return []
                
        except Exception as e:
            logger.error(f"Failed to get commit history: {e}")
            return []
    
    async def auto_version_bump(
        self,
        repo_name: str,
        bump_type: str = "patch"
    ) -> Optional[str]:
        latest = await self.get_latest_release(repo_name)
        
        if latest:
            current_version = latest.tag_name.lstrip('v')
        else:
            current_version = "0.0.0"
        
        parts = current_version.split('.')
        while len(parts) < 3:
            parts.append('0')
        
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        
        return new_version
    
    async def generate_release_notes(
        self,
        repo_name: str,
        from_tag: Optional[str] = None
    ) -> str:
        commits = await self.get_commit_history(repo_name, per_page=50)
        
        if not commits:
            return "No commits found for release notes."
        
        features = []
        fixes = []
        other = []
        
        for commit in commits:
            message = commit["message"].lower()
            if message.startswith('feat'):
                features.append(f"- {commit['message'].split(':', 1)[-1].strip() if ':' in commit['message'] else commit['message']}")
            elif message.startswith('fix'):
                fixes.append(f"- {commit['message'].split(':', 1)[-1].strip() if ':' in commit['message'] else commit['message']}")
            else:
                other.append(f"- {commit['message']}")
        
        notes = []
        if features:
            notes.append("## ✨ Features\n" + "\n".join(features[:10]))
        if fixes:
            notes.append("## 🐛 Bug Fixes\n" + "\n".join(fixes[:10]))
        if other:
            notes.append("## 📝 Other Changes\n" + "\n".join(other[:5]))
        
        return "\n\n".join(notes) if notes else "Release notes not available."
