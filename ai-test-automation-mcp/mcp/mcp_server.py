"""
MCP Server — connects AI models to Selenium, Playwright, Jira, and CI/CD pipelines.
Model Context Protocol (MCP) integration for AI-assisted test automation.

Author: Golla Chandramouli | SDET | TCS | Lloyds Banking Group
"""

import json
import asyncio
import logging
from typing import Any
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPTestAutomationServer:
    """
    MCP Server that exposes test automation tools to AI models.
    Enables AI-assisted test case generation, step definition creation,
    and intelligent test maintenance.
    """

    def __init__(self):
        self.client = Anthropic()
        self.tools = self._register_tools()

    def _register_tools(self) -> list[dict]:
        """Register all test automation tools with MCP."""
        return [
            {
                "name": "generate_playwright_test",
                "description": "Generate a Playwright Python test from a user story or Jira ticket description.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "story_description": {"type": "string", "description": "User story or feature description"},
                        "page_url": {"type": "string", "description": "URL of the page to test"},
                        "test_type": {"type": "string", "enum": ["smoke", "regression", "negative"], "description": "Type of test to generate"}
                    },
                    "required": ["story_description"]
                }
            },
            {
                "name": "generate_bdd_feature",
                "description": "Generate a Gherkin BDD feature file with scenarios from acceptance criteria.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "feature_name": {"type": "string", "description": "Name of the feature"},
                        "acceptance_criteria": {"type": "string", "description": "Acceptance criteria text"},
                        "framework": {"type": "string", "enum": ["cucumber", "behave"], "description": "BDD framework to target"}
                    },
                    "required": ["feature_name", "acceptance_criteria"]
                }
            },
            {
                "name": "generate_api_test",
                "description": "Generate a PyTest REST API test suite from an OpenAPI spec or endpoint description.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "endpoint": {"type": "string", "description": "API endpoint path"},
                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                        "description": {"type": "string", "description": "What the endpoint does"},
                        "include_schema_validation": {"type": "boolean", "default": True}
                    },
                    "required": ["endpoint", "method", "description"]
                }
            },
            {
                "name": "fetch_jira_story",
                "description": "Fetch a Jira story description and acceptance criteria for test generation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "story_id": {"type": "string", "description": "Jira story ID e.g. BFSI-1234"}
                    },
                    "required": ["story_id"]
                }
            },
            {
                "name": "analyze_test_coverage",
                "description": "Analyze existing test files and suggest missing test coverage areas.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "test_directory": {"type": "string", "description": "Path to test directory"},
                        "coverage_threshold": {"type": "number", "description": "Target coverage percentage", "default": 90}
                    },
                    "required": ["test_directory"]
                }
            }
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute registered tools — handlers for each MCP tool."""
        handlers = {
            "generate_playwright_test": self._generate_playwright_test,
            "generate_bdd_feature": self._generate_bdd_feature,
            "generate_api_test": self._generate_api_test,
            "fetch_jira_story": self._fetch_jira_story,
            "analyze_test_coverage": self._analyze_test_coverage,
        }
        handler = handlers.get(tool_name)
        if handler:
            return handler(tool_input)
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def _generate_playwright_test(self, inputs: dict) -> str:
        """Generate Playwright test code."""
        story = inputs.get("story_description", "")
        url = inputs.get("page_url", "https://app.example.com")
        test_type = inputs.get("test_type", "smoke")

        template = f'''
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.{test_type}
def test_generated_scenario(page: Page):
    """
    AI-Generated Test | MCP | Story: {story[:60]}...
    Generated by: MCPTestAutomationServer
    """
    # Navigate to target page
    page.goto("{url}")

    # TODO: MCP will populate these steps based on story analysis
    # Step definitions generated from: {story[:100]}

    expect(page).to_have_url("{url}")
'''
        logger.info(f"[MCP] Generated Playwright {test_type} test for: {story[:50]}")
        return json.dumps({"test_code": template, "framework": "playwright", "type": test_type})

    def _generate_bdd_feature(self, inputs: dict) -> str:
        """Generate Gherkin BDD feature file."""
        feature_name = inputs.get("feature_name", "Feature")
        criteria = inputs.get("acceptance_criteria", "")
        framework = inputs.get("framework", "behave")

        feature = f'''Feature: {feature_name}
  # AI-Generated via MCP | Framework: {framework}
  # Source: Acceptance Criteria

  Background:
    Given the user is authenticated
    And the application is in a clean state

  @ai-generated @smoke
  Scenario: Happy path - {feature_name}
    Given the preconditions are met
    When the user performs the primary action
    Then the expected outcome should be visible
    And the data should be persisted in the database

  @ai-generated @negative
  Scenario: Negative path - {feature_name}
    Given invalid input is provided
    When the user attempts the action
    Then an appropriate error message should be shown
    And no data should be committed
'''
        logger.info(f"[MCP] Generated BDD feature: {feature_name} for {framework}")
        return json.dumps({"feature_content": feature, "framework": framework})

    def _generate_api_test(self, inputs: dict) -> str:
        """Generate PyTest API test."""
        endpoint = inputs.get("endpoint", "/api/v1/resource")
        method = inputs.get("method", "GET")
        description = inputs.get("description", "")
        schema_validation = inputs.get("include_schema_validation", True)

        test_code = f'''import pytest
import requests
from jsonschema import validate


BASE_URL = "https://api.example.com"

# AI-Generated API Test | MCP | Endpoint: {endpoint}
class Test{method.title()}{endpoint.replace("/", "_").replace("-", "_").title()}:

    def test_{method.lower()}_success(self, api_client):
        """
        Test: {description}
        Endpoint: {method} {endpoint}
        """
        response = api_client.{method.lower()}("{endpoint}")

        assert response.status_code == {"200" if method == "GET" else "201"}
        assert response.headers["Content-Type"] == "application/json"
        {"# Schema validation" if schema_validation else ""}
        {"data = response.json()" if schema_validation else ""}

    def test_{method.lower()}_unauthorized(self, api_client_no_auth):
        """Negative: Unauthorized access to {endpoint}"""
        response = api_client_no_auth.{method.lower()}("{endpoint}")
        assert response.status_code == 401

    def test_{method.lower()}_response_time(self, api_client):
        """Performance: Response time for {endpoint} should be under 2s"""
        import time
        start = time.time()
        response = api_client.{method.lower()}("{endpoint}")
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Response too slow: {{elapsed:.2f}}s"
'''
        return json.dumps({"test_code": test_code, "endpoint": endpoint, "method": method})

    def _fetch_jira_story(self, inputs: dict) -> str:
        """Mock Jira story fetch — replace with real Jira API in production."""
        story_id = inputs.get("story_id")
        # In production: call Jira REST API here
        mock_story = {
            "id": story_id,
            "summary": f"[MOCK] Story {story_id} — replace with real Jira API",
            "description": "As a user, I want to perform an action so that I achieve a goal.",
            "acceptance_criteria": "Given... When... Then...",
            "status": "In Progress"
        }
        logger.info(f"[MCP] Fetched Jira story: {story_id}")
        return json.dumps(mock_story)

    def _analyze_test_coverage(self, inputs: dict) -> str:
        """Analyze test coverage and return suggestions."""
        directory = inputs.get("test_directory", "tests/")
        threshold = inputs.get("coverage_threshold", 90)
        # In production: parse test files and coverage reports
        analysis = {
            "directory": directory,
            "current_coverage": 87,
            "target_coverage": threshold,
            "gap": threshold - 87,
            "suggestions": [
                "Add negative test cases for payment failure scenarios",
                "Missing DB rollback tests after failed transactions",
                "No tests for session timeout handling",
                "Add cross-browser tests for Safari"
            ]
        }
        return json.dumps(analysis)

    def run(self, user_request: str) -> str:
        """
        Main agentic loop — AI uses tools to fulfill test automation requests.
        Example: 'Generate a smoke test suite for the login page at /auth/login'
        """
        logger.info(f"[MCP] Processing request: {user_request[:80]}")
        messages = [{"role": "user", "content": user_request}]

        system_prompt = """You are an expert SDET and test automation engineer.
        Use the available tools to generate high-quality, production-ready test code.
        Always follow Page Object Model patterns, include assertions, and add meaningful comments.
        For BFSI applications, always include security and negative test scenarios."""

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=4096,
                system=system_prompt,
                tools=self.tools,
                messages=messages
            )

            if response.stop_reason == "end_turn":
                final_text = next(
                    (block.text for block in response.content if hasattr(block, "text")), ""
                )
                logger.info("[MCP] Request completed successfully.")
                return final_text

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        logger.info(f"[MCP] Executing tool: {block.name}")
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                break

        return "MCP processing complete."


if __name__ == "__main__":
    server = MCPTestAutomationServer()

    # Demo: Generate a full test suite from a user story
    result = server.run(
        "Generate a Playwright smoke test and BDD feature file for a banking login page "
        "that requires 2FA. Include negative scenarios for locked accounts."
    )
    print(result)
