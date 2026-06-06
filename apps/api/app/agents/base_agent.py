import logging
from abc import ABC, abstractmethod
from importlib import import_module
from time import perf_counter
from typing import Any

from pydantic import BaseModel

from app.agents.schemas import (
    AgentExecutionRecord,
    AgentTokenUsage,
    OpenAIAgentSpec,
    WorkflowState,
)
from app.core.errors import AppError


class BaseAgent[InputT: BaseModel, OutputT: BaseModel](ABC):
    """Base abstraction for service-backed workflow agents."""

    agent_name: str

    def __init__(self, agent_name: str, sdk_spec: OpenAIAgentSpec) -> None:
        self.agent_name = agent_name
        self.sdk_spec = sdk_spec
        self._logger = logging.getLogger(f"app.agents.{agent_name}")

    async def execute(self, agent_input: InputT, state: WorkflowState) -> OutputT:
        started_at = perf_counter()
        self._logger.info(
            "agent_started",
            extra={
                "user_id": state.user_id,
                "agent_name": self.agent_name,
                "workflow_id": state.workflow_id,
            },
        )
        try:
            output = await self.run(agent_input, state)
            state.mark_completed(self.agent_name)
            self._record_execution(state=state, started_at=started_at, success=True)
            self._logger.info(
                "agent_completed",
                extra={
                    "user_id": state.user_id,
                    "agent_name": self.agent_name,
                    "workflow_id": state.workflow_id,
                },
            )
            return output
        except AppError as error:
            state.record_error(self.agent_name, str(error))
            self._record_execution(
                state=state,
                started_at=started_at,
                success=False,
                error_message=str(error),
            )
            self._logger.warning(
                "agent_failed",
                extra={
                    "user_id": state.user_id,
                    "agent_name": self.agent_name,
                    "workflow_id": state.workflow_id,
                },
                exc_info=True,
            )
            raise
        except Exception as error:
            state.record_error(self.agent_name, str(error))
            self._record_execution(
                state=state,
                started_at=started_at,
                success=False,
                error_message=str(error),
            )
            self._logger.exception(
                "agent_unhandled_error",
                extra={
                    "user_id": state.user_id,
                    "agent_name": self.agent_name,
                    "workflow_id": state.workflow_id,
                },
            )
            raise AppError(f"{self.agent_name} failed. Please try again.") from error

    async def execute_with_openai_agents_sdk(
        self,
        agent_input: InputT,
        state: WorkflowState,
    ) -> OutputT:
        """Execute this service-backed agent as an OpenAI Agents SDK tool.

        The existing service remains the source of truth. The SDK agent gets a single tool that
        delegates into this agent's service-backed `execute` method.
        """
        try:
            sdk_module: Any = import_module("agents")
        except ImportError as error:
            raise AppError("OpenAI Agents SDK is not installed") from error

        agent_factory = sdk_module.Agent
        runner = sdk_module.Runner
        function_tool = sdk_module.function_tool

        @function_tool  # type: ignore[untyped-decorator]
        async def run_service_tool() -> dict[str, Any]:
            """Run the existing application service for this workflow step."""
            output = await self.execute(agent_input, state)
            return output.model_dump(mode="json")

        sdk_agent = agent_factory(
            name=self.sdk_spec.name,
            instructions=self.sdk_spec.instructions,
            tools=[run_service_tool],
            tool_use_behavior="stop_on_first_tool",
        )
        result = await runner.run(
            sdk_agent,
            "Run the configured service tool exactly once and return its output.",
            context=state,
        )
        return self._coerce_sdk_output(result.final_output)

    @abstractmethod
    async def run(self, agent_input: InputT, state: WorkflowState) -> OutputT:
        raise NotImplementedError

    @abstractmethod
    def _coerce_sdk_output(self, final_output: Any) -> OutputT:
        raise NotImplementedError

    def _record_execution(
        self,
        state: WorkflowState,
        started_at: float,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        state.record_execution(
            AgentExecutionRecord(
                workflow_id=state.workflow_id,
                agent_name=self.agent_name,
                execution_time_ms=round((perf_counter() - started_at) * 1000),
                success=success,
                token_usage=AgentTokenUsage(),
                error_message=error_message,
            ),
        )
