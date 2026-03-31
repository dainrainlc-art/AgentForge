"""
Tests for SelfChecker class in self_evolution module
"""
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import json
import tempfile
import shutil

from agentforge.core.self_evolution import SelfChecker
from agentforge.memory import MemoryStore
from agentforge.llm import QianfanClient


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    temp_dir = tempfile.mkdtemp()
    log_dir = Path(temp_dir) / "logs"
    report_dir = Path(temp_dir) / "reports"
    log_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    yield {
        "base": temp_dir,
        "logs": log_dir,
        "reports": report_dir
    }
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client"""
    client = MagicMock(spec=QianfanClient)
    client.chat = AsyncMock(return_value='{"issues": [], "patterns": [], "suggestions": []}')
    return client


@pytest.fixture
def mock_memory_store():
    """Create a mock memory store"""
    store = MagicMock(spec=MemoryStore)
    store.store_memory = AsyncMock()
    return store


@pytest.fixture
def self_checker(mock_llm_client, mock_memory_store, temp_dirs):
    """Create a SelfChecker instance for testing"""
    return SelfChecker(
        llm_client=mock_llm_client,
        memory_store=mock_memory_store,
        log_dir=str(temp_dirs["logs"]),
        report_dir=str(temp_dirs["reports"])
    )


class TestSelfCheckerInitialization:
    """Test SelfChecker initialization"""
    
    def test_init_with_default_dirs(self, mock_llm_client, mock_memory_store):
        """Test initialization with default directories"""
        checker = SelfChecker(mock_llm_client, mock_memory_store)
        
        assert checker._log_dir is not None
        assert checker._report_dir is not None
        assert checker._error_log == []
        assert checker._last_check is None
        assert checker._is_running is False
    
    def test_init_with_custom_dirs(self, mock_llm_client, mock_memory_store, temp_dirs):
        """Test initialization with custom directories"""
        checker = SelfChecker(
            mock_llm_client, 
            mock_memory_store,
            log_dir=str(temp_dirs["logs"]),
            report_dir=str(temp_dirs["reports"])
        )
        
        assert checker._log_dir == temp_dirs["logs"]
        assert checker._report_dir == temp_dirs["reports"]


class TestErrorLogging:
    """Test error logging functionality"""
    
    @pytest.mark.asyncio
    async def test_log_error(self, self_checker, temp_dirs):
        """Test logging an error"""
        error = ValueError("Test error message")
        context = {"user_id": "test_user", "action": "test_action"}
        
        self_checker.log_error(error, context)
        
        assert len(self_checker._error_log) == 1
        assert self_checker._error_log[0]["error_type"] == "ValueError"
        assert self_checker._error_log[0]["error_message"] == "Test error message"
        assert self_checker._error_log[0]["context"] == context
        assert "timestamp" in self_checker._error_log[0]
        
        await asyncio.sleep(0.1)
        
        error_log_file = self_checker._error_log_file
        assert error_log_file.exists()
    
    @pytest.mark.asyncio
    async def test_log_error_truncation(self, self_checker):
        """Test that error log is truncated when it exceeds max size"""
        for i in range(110):
            self_checker.log_error(Exception(f"Error {i}"))
        
        assert len(self_checker._error_log) <= 100


class TestLogReading:
    """Test log reading functionality"""
    
    @pytest.mark.asyncio
    async def test_read_empty_logs(self, self_checker):
        """Test reading from empty log directory"""
        errors = await self_checker.read_error_logs()
        assert isinstance(errors, list)
    
    @pytest.mark.asyncio
    async def test_read_jsonl_logs(self, self_checker, temp_dirs):
        """Test reading from JSONL log files"""
        jsonl_file = temp_dirs["logs"] / "test_errors.jsonl"
        
        errors_data = [
            {"timestamp": "2026-03-28T10:00:00", "error_type": "ValueError", "error_message": "Error 1"},
            {"timestamp": "2026-03-28T11:00:00", "error_type": "TypeError", "error_message": "Error 2"},
        ]
        
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for error in errors_data:
                f.write(json.dumps(error) + '\n')
        
        errors = await self_checker.read_error_logs()
        
        assert len(errors) == 2
        assert errors[0]["error_type"] == "ValueError"
        assert errors[1]["error_type"] == "TypeError"
    
    @pytest.mark.asyncio
    async def test_parse_log_file(self, self_checker, temp_dirs):
        """Test parsing .log files"""
        log_file = temp_dirs["logs"] / "app.log"
        
        log_content = """2026-03-28 10:00:00 | INFO | module:function:123 - Info message
2026-03-28 10:01:00 | ERROR | module:function:124 - Error message
2026-03-28 10:02:00 | WARNING | module:function:125 - Warning message
2026-03-28 10:03:00 | ERROR | module:function:126 - Another error
"""
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        errors = await self_checker._parse_log_file(log_file)
        
        assert len(errors) == 2
        assert errors[0]["error_type"] == "ERROR"
        assert "Error message" in errors[0]["error_message"]


class TestSelfCheck:
    """Test self-check functionality"""
    
    @pytest.mark.asyncio
    async def test_run_self_check_no_errors(self, self_checker):
        """Test running self-check with no errors"""
        stats = await self_checker.run_self_check()
        
        assert stats["errors_analyzed"] == 0
        assert stats["file_errors_read"] == 0
        assert stats["memory_errors_read"] == 0
        assert stats["report_generated"] is True
    
    @pytest.mark.asyncio
    async def test_run_self_check_prevents_concurrent_execution(self, self_checker):
        """Test that concurrent self-checks are prevented"""
        self_checker._is_running = True
        
        stats = await self_checker.run_self_check()
        
        assert stats["status"] == "already_running"
        assert stats["message"] == "Self-check is already in progress"
    
    @pytest.mark.asyncio
    async def test_run_self_check_with_errors(self, self_checker):
        """Test running self-check with errors"""
        self_checker.log_error(ValueError("Test error"))
        
        with patch.object(self_checker.llm_client, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = json.dumps({
                "issues": [{"title": "Test issue", "description": "Test description", "root_cause": "Test cause", "impact": "Test impact", "severity": "medium"}],
                "patterns": [{"pattern_name": "Test pattern", "description": "Test description", "frequency": "Often", "suggestion": "Test suggestion"}],
                "suggestions": [{"title": "Test suggestion", "description": "Test description", "priority": "high", "estimated_effort": "1h"}]
            })
            
            stats = await self_checker.run_self_check()
            
            assert stats["errors_analyzed"] >= 1
            assert stats["issues_found"] >= 0
            assert stats["report_generated"] is True


class TestStatusMethods:
    """Test status query methods"""
    
    def test_get_self_check_status(self, self_checker):
        """Test getting self-check status"""
        status = self_checker.get_self_check_status()
        
        assert "last_check" in status
        assert "is_running" in status
        assert "error_log_count" in status
        assert "log_dir" in status
        assert "report_dir" in status
        assert status["is_running"] is False
    
    def test_get_last_self_check_time(self, self_checker):
        """Test getting last self-check time"""
        assert self_checker.get_last_self_check_time() is None
        
        self_checker._last_check = datetime.now()
        assert isinstance(self_checker.get_last_self_check_time(), datetime)
    
    @pytest.mark.asyncio
    async def test_trigger_self_check(self, self_checker):
        """Test manual trigger for self-check"""
        stats = await self_checker.trigger_self_check()
        
        assert isinstance(stats, dict)
        assert "errors_analyzed" in stats


class TestReportGeneration:
    """Test report generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_empty_report(self, self_checker, temp_dirs):
        """Test generating empty report when no errors"""
        report_path = await self_checker._generate_empty_report()
        
        assert report_path is not None
        assert report_path.exists()
        assert "self_check_" in str(report_path)
        assert report_path.suffix == ".md"
    
    @pytest.mark.asyncio
    async def test_generate_diagnostic_report(self, self_checker, temp_dirs):
        """Test generating diagnostic report with analysis"""
        analysis = {
            "issues": [
                {
                    "title": "API Connection Error",
                    "description": "Frequent connection timeouts",
                    "root_cause": "Network instability",
                    "impact": "Service degradation",
                    "severity": "high"
                }
            ],
            "patterns": [
                {
                    "pattern_name": "Connection Timeout Pattern",
                    "description": "Timeouts occur during peak hours",
                    "frequency": "Daily",
                    "suggestion": "Implement retry logic"
                }
            ],
            "suggestions": [
                {
                    "title": "Add Retry Logic",
                    "description": "Implement exponential backoff",
                    "priority": "high",
                    "code_changes": "Add retry decorator",
                    "estimated_effort": "2h"
                }
            ]
        }
        
        stats = {
            "errors_analyzed": 10,
            "file_errors_read": 5,
            "memory_errors_read": 5,
            "issues_found": 1,
            "patterns_identified": 1,
            "suggestions_generated": 1
        }
        
        report_path = await self_checker._generate_diagnostic_report(analysis, stats)
        
        assert report_path is not None
        assert report_path.exists()
        
        content = report_path.read_text(encoding='utf-8')
        assert "AgentForge 自我诊断报告" in content
        assert "API Connection Error" in content
        assert "Add Retry Logic" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
