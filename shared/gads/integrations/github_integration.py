"""
GitHub Integration for Google Ads Agent
Provides access to GitHub management tools specifically for the Google Ads sub-repo.

This integration allows the Google Ads agent to:
- Manage GitHub pushes for the Google Ads sub-repo
- Use GitHub CLI for bulk operations
- Run security scans and validations
- Generate changelogs and manage releases
- Handle collaboration and commit management
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import subprocess
import json


class GoogleAdsGitHubIntegration:
    """
    GitHub integration specifically for Google Ads sub-repo management.
    Provides access to all GitHub management tools with Google Ads context.
    """

    def __init__(self):
        # Set up paths to GitHub tools
        self.repo_root = Path(__file__).parent.parent.parent.parent.parent.parent.parent
        self.github_tools_path = self.repo_root / "7_tools" / "github"
        self.google_ads_repo_path = self.repo_root  # Main repo for Git operations
        self.google_ads_subpath = Path(__file__).parent.parent.parent  # Google Ads sub-directory

        # Add GitHub tools to path
        if str(self.github_tools_path) not in sys.path:
            sys.path.insert(0, str(self.github_tools_path))

        # Initialize tool availability
        self.tools_available = self._check_tools_availability()

    def _check_tools_availability(self) -> Dict[str, bool]:
        """Check which GitHub tools are available."""
        tools = {}

        # Check CLI tools
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True, timeout=5)
            tools["gh_cli"] = result.returncode == 0
        except:
            tools["gh_cli"] = False

        # Check Python tools
        try:
            from github_api_tool.github_api_tool_main import check_github_cli
            tools["github_api_tool"] = check_github_cli()
        except:
            tools["github_api_tool"] = False

        try:
            from sensitive_data_scanner_tool.sensitive_data_scanner_tool_main import check_gitleaks
            tools["gitleaks"] = check_gitleaks()
        except:
            tools["gitleaks"] = False

        try:
            from commitlint_tool.commitlint_tool_main import check_commitlint
            tools["commitlint"] = check_commitlint()
        except:
            tools["commitlint"] = False

        # Check binary tools
        try:
            result = subprocess.run(["git-cliff", "--version"], capture_output=True, text=True, timeout=5)
            tools["git_cliff"] = result.returncode == 0
        except:
            tools["git_cliff"] = False

        try:
            result = subprocess.run(["git-mit", "--version"], capture_output=True, text=True, timeout=5)
            tools["git_mit"] = result.returncode == 0
        except:
            tools["git_mit"] = False

        try:
            result = subprocess.run(["git-filter-repo", "--version"], capture_output=True, text=True, timeout=5)
            tools["git_filter_repo"] = result.returncode == 0
        except:
            tools["git_filter_repo"] = False

        try:
            result = subprocess.run(["lefthook", "--version"], capture_output=True, text=True, timeout=5)
            tools["lefthook"] = result.returncode == 0
        except:
            tools["lefthook"] = False

        return tools

    def get_available_tools(self) -> Dict[str, bool]:
        """Get status of all available GitHub tools."""
        return self.tools_available.copy()

    def _run_github_cli_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Run a GitHub CLI command."""
        try:
            result = subprocess.run(
                ["gh"] + command,
                cwd=cwd or self.google_ads_repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
        except Exception as e:
            return False, f"Error: {e}"

    def _run_tool_command(self, tool_name: str, command: List[str], **kwargs) -> Tuple[bool, Any]:
        """Run a specific GitHub tool command."""
        try:
            if tool_name == "github_api_tool":
                from github_api_tool.github_api_tool_main import GitHubAPITool
                tool = GitHubAPITool(str(self.google_ads_repo_path))
                method_name = command[0]
                if hasattr(tool, method_name):
                    method = getattr(tool, method_name)
                    return True, method(**kwargs)
                else:
                    return False, f"Method {method_name} not found"

            elif tool_name == "sensitive_data_scanner":
                from sensitive_data_scanner_tool.sensitive_data_scanner_tool_main import SensitiveDataScannerTool
                scanner = SensitiveDataScannerTool(str(self.google_ads_repo_path))
                method_name = command[0]
                if hasattr(scanner, method_name):
                    method = getattr(scanner, method_name)
                    return True, method(**kwargs)
                else:
                    return False, f"Method {method_name} not found"

            elif tool_name == "commitlint":
                from commitlint_tool.commitlint_tool_main import CommitlintTool
                commitlint = CommitlintTool(str(self.google_ads_repo_path))
                method_name = command[0]
                if hasattr(commitlint, method_name):
                    method = getattr(commitlint, method_name)
                    return True, method(**kwargs)
                else:
                    return False, f"Method {method_name} not found"

            elif tool_name == "git_cliff":
                from git_cliff_tool.git_cliff_tool_main import GitCliffTool
                cliff = GitCliffTool(str(self.google_ads_repo_path))
                method_name = command[0]
                if hasattr(cliff, method_name):
                    method = getattr(cliff, method_name)
                    return True, method(**kwargs)
                else:
                    return False, f"Method {method_name} not found"

            elif tool_name == "git_mit":
                from git_mit_tool.git_mit_tool_main import GitMitTool
                mit = GitMitTool(str(self.google_ads_repo_path))
                method_name = command[0]
                if hasattr(mit, method_name):
                    method = getattr(mit, method_name)
                    return True, method(**kwargs)
                else:
                    return False, f"Method {method_name} not found"

            elif tool_name == "git_filter_repo":
                from git_filter_repo_tool.git_filter_repo_tool_main import GitFilterRepoTool
                filter_repo = GitFilterRepoTool(str(self.google_ads_repo_path))
                method_name = command[0]
                if hasattr(filter_repo, method_name):
                    method = getattr(filter_repo, method_name)
                    return True, method(**kwargs)
                else:
                    return False, f"Method {method_name} not found"

        except Exception as e:
            return False, f"Error running {tool_name}: {e}"

        return False, f"Tool {tool_name} not supported"

    # GitHub CLI Operations
    def list_repositories(self) -> Tuple[bool, str]:
        """List user's repositories."""
        return self._run_github_cli_command(["repo", "list"])

    def create_pull_request(self, title: str, body: str, base: str = "main", head: str = None) -> Tuple[bool, str]:
        """Create a pull request for the Google Ads repo."""
        cmd = ["pr", "create", "--title", title, "--body", body, "--base", base]
        if head:
            cmd.extend(["--head", head])
        return self._run_github_cli_command(cmd, cwd=self.google_ads_repo_path)

    def check_pull_requests(self) -> Tuple[bool, str]:
        """Check open pull requests for the Google Ads repo."""
        return self._run_github_cli_command(["pr", "list"], cwd=self.google_ads_repo_path)

    def run_security_scan(self) -> Tuple[bool, Any]:
        """Run security scan on the Google Ads repo."""
        return self._run_tool_command("sensitive_data_scanner", ["scan"])

    def validate_commits(self, commit_range: Optional[str] = None) -> Tuple[bool, Any]:
        """Validate commits using commitlint."""
        if commit_range:
            return self._run_tool_command("commitlint", ["validate_commit_range"], from_ref=commit_range.split("..")[0], to_ref=commit_range.split("..")[1])
        else:
            # Validate recent commits
            return self._run_tool_command("commitlint", ["validate_commit_range"], from_ref="HEAD~5", to_ref="HEAD")

    def generate_changelog(self) -> Tuple[bool, Any]:
        """Generate changelog for the Google Ads repo."""
        return self._run_tool_command("git_cliff", ["generate_changelog"])

    def set_co_authors(self, authors: List[Dict[str, str]]) -> Tuple[bool, Any]:
        """Set co-authors for the next commit."""
        return self._run_tool_command("git_mit", ["set_authors"], authors=authors)

    def clean_repository_history(self, patterns: List[str]) -> Tuple[bool, Any]:
        """Clean sensitive data from repository history."""
        return self._run_tool_command("git_filter_repo", ["remove_sensitive_files"], file_paths=patterns)

    def run_bulk_operations(self, operation: str, **kwargs) -> Tuple[bool, Any]:
        """Run bulk GitHub operations."""
        return self._run_tool_command("github_api_tool", [operation], **kwargs)

    def get_repository_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the Google Ads sub-repo within the main repository."""
        status = {
            "repository_path": str(self.google_ads_repo_path),
            "google_ads_subpath": str(self.google_ads_subpath),
            "tools_available": self.get_available_tools(),
            "repository_info": {},
            "pull_requests": {},
            "security_status": {},
            "commit_validation": {}
        }

        # Get repository info (main repo)
        success, repo_info = self._run_github_cli_command(["repo", "view"], cwd=self.google_ads_repo_path)
        status["repository_info"] = {"success": success, "info": repo_info}

        # Get PR status (main repo)
        success, pr_info = self.check_pull_requests()
        status["pull_requests"] = {"success": success, "info": pr_info}

        # Get security status (Google Ads specific)
        success, security_info = self.run_security_scan()
        status["security_status"] = {"success": success, "info": security_info}

        # Get commit validation status
        success, validation_info = self.validate_commits()
        status["commit_validation"] = {"success": success, "info": validation_info}

        return status

    def push_google_ads_changes(self, commit_message: str, **kwargs) -> Dict[str, Any]:
        """
        Complete workflow to push Google Ads changes with validation and security checks.
        Works on the main repository but focuses on Google Ads sub-directory changes.

        Args:
            commit_message: The commit message to use
            **kwargs: Additional options for tools (e.g., co_authors, skip_security, etc.)
        """
        results = {
            "security_scan": {},
            "commit_validation": {},
            "git_operations": {},
            "push_status": {},
            "overall_success": False
        }

        try:
            # 1. Run security scan (unless skipped)
            if not kwargs.get("skip_security", False):
                success, security_result = self.run_security_scan()
                results["security_scan"] = {"success": success, "result": security_result}
                if not success:
                    results["error"] = "Security scan failed"
                    return results

            # 2. Validate commit message
            if not kwargs.get("skip_validation", False):
                success, validation_result = self._run_tool_command(
                    "commitlint", ["validate_commit_message"], commit_message=commit_message
                )
                results["commit_validation"] = {"success": success, "result": validation_result}
                if not success:
                    results["error"] = "Commit validation failed"
                    return results

            # 3. Set co-authors if provided
            if kwargs.get("co_authors"):
                success, co_author_result = self.set_co_authors(kwargs["co_authors"])
                results["co_authors"] = {"success": success, "result": co_author_result}

            # 4. Add and commit Google Ads specific changes
            try:
                # Change to Google Ads sub-directory and add only those changes
                google_ads_rel_path = self.google_ads_subpath.relative_to(self.google_ads_repo_path)

                # Add only the Google Ads changes
                subprocess.run(["git", "add", str(google_ads_rel_path)],
                             cwd=self.google_ads_repo_path, check=True)

                # Set co-authors if provided
                if kwargs.get("co_authors"):
                    env = os.environ.copy()
                    co_author_trailers = []
                    for author in kwargs["co_authors"]:
                        co_author_trailers.append(f"Co-authored-by: {author['name']} <{author['email']}>")
                    commit_message += "\n\n" + "\n".join(co_author_trailers)

                # Commit
                subprocess.run(["git", "commit", "-m", commit_message],
                             cwd=self.google_ads_repo_path, check=True)
                results["git_operations"] = {"success": True, "message": f"Google Ads changes committed successfully from {google_ads_rel_path}"}

            except subprocess.CalledProcessError as e:
                results["git_operations"] = {"success": False, "error": str(e)}
                results["error"] = "Git commit failed"
                return results

            # 5. Push changes
            try:
                subprocess.run(["git", "push"], cwd=self.google_ads_repo_path, check=True)
                results["push_status"] = {"success": True, "message": "Changes pushed successfully"}
            except subprocess.CalledProcessError as e:
                results["push_status"] = {"success": False, "error": str(e)}
                results["error"] = "Git push failed"
                return results

            # 6. Create PR if requested
            if kwargs.get("create_pr", False):
                pr_title = kwargs.get("pr_title", f"Google Ads: {commit_message[:50]}...")
                pr_body = kwargs.get("pr_body", f"Automated update for Google Ads agent\n\nChanges in: {google_ads_rel_path}\n\n{commit_message}")
                success, pr_result = self.create_pull_request(pr_title, pr_body)
                results["pull_request"] = {"success": success, "result": pr_result}

            results["overall_success"] = True
            return results

        except Exception as e:
            results["error"] = f"Unexpected error: {e}"
            return results


# Convenience functions for direct use
def create_google_ads_github_integration():
    """Create and return a Google Ads GitHub integration instance."""
    return GoogleAdsGitHubIntegration()


def push_google_ads_changes(commit_message: str, **kwargs):
    """Convenience function to push Google Ads changes."""
    integration = create_google_ads_github_integration()
    return integration.push_google_ads_changes(commit_message, **kwargs)


def get_google_ads_repo_status():
    """Convenience function to get Google Ads repository status."""
    integration = create_google_ads_github_integration()
    return integration.get_repository_status()


if __name__ == "__main__":
    # Example usage
    integration = create_google_ads_github_integration()

    print("🛠️  Google Ads GitHub Integration")
    print("=" * 50)

    # Check tool availability
    tools = integration.get_available_tools()
    print("\n📦 Available Tools:")
    for tool, available in tools.items():
        status = "✅" if available else "❌"
        print(f"  {status} {tool}")

    # Get repository status
    print("\n📊 Repository Status:")
    status = integration.get_repository_status()
    print(f"Repository: {status['repository_path']}")
    print(f"Security scan: {'✅' if status['security_status'].get('success') else '❌'}")
    print(f"Commit validation: {'✅' if status['commit_validation'].get('success') else '❌'}")