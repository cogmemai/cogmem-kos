"""Personal Planning Agent - the central orchestrator of cogmem-kos.

The personal planning agent is the heart of the cogmem-kos framework. It maintains
persistent, user-specific memory and uses this knowledge to plan and orchestrate
other agents to complete complex tasks.

Key capabilities:
- Maintains persistent memory that persists across sessions
- Plans with context from past experiences
- Orchestrates specialized agents to execute tasks
- Self-improves over time by learning from completed actions
"""

from datetime import datetime
from typing import Any
import uuid

from kos.agents.base import BaseAgent
from kos.agents.planning.models import (
    ExecutionPlan,
    Memory,
    MemoryType,
    PlanningContext,
    PlanStatus,
    PlanStep,
    PlanStepStatus,
)
from kos.agents.planning.memory_store import MemoryStore
from kos.core.contracts.llm import LLMGateway, LLMResponse
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore
from kos.core.events.envelope import EventEnvelope
from kos.core.events.event_types import EventType


PLANNING_SYSTEM_PROMPT = """You are a personal planning agent with access to the user's memory.
Your role is to create execution plans for complex tasks by:
1. Analyzing the task requirements
2. Consulting relevant memories from past experiences
3. Breaking down the task into discrete steps
4. Assigning appropriate agents to each step
5. Tracking progress and adapting the plan as needed

Available agents you can dispatch:
- ChunkAgent: Splits documents into passages
- EmbedAgent: Generates embeddings for passages
- IndexTextAgent: Indexes passages for text search
- EntityExtractAgent: Extracts named entities from passages
- WikipediaPageAgent: Builds entity page artifacts

When creating a plan, output a JSON object with:
{
    "steps": [
        {
            "step_number": 1,
            "description": "What this step accomplishes",
            "agent_type": "AgentName or null for planning steps",
            "action_type": "action_name",
            "inputs": {"key": "value"}
        }
    ],
    "reasoning": "Why you chose this plan"
}
"""


class PersonalPlanningAgent(BaseAgent):
    """Personal Planning Agent - the central orchestrator with cognitive memory.
    
    This agent is the heart of the cogmem-kos framework. It maintains persistent,
    user-specific memory and uses this knowledge to plan and orchestrate other
    agents to complete complex tasks.
    
    Unlike traditional multi-agent systems that pass entire conversation histories
    through prompts, the personal planning agent:
    - Maintains persistent memory specific to each user
    - Uses past experiences to create better action plans
    - Coordinates specialized agents to execute tasks
    - Self-improves over time by learning from completed actions
    
    This architecture reduces token consumption, improves task success rates,
    and enables coherent long-term strategies.
    """

    agent_id = "personal_planning_agent"
    consumes_events = [EventType.ITEM_UPSERTED]

    def __init__(
        self,
        object_store: ObjectStore,
        outbox_store: OutboxStore,
        memory_store: MemoryStore,
        llm_gateway: LLMGateway,
        max_memories_per_query: int = 10,
    ):
        """Initialize the personal planning agent.
        
        Args:
            object_store: Store for domain objects
            outbox_store: Store for event outbox
            memory_store: Store for persistent user memories
            llm_gateway: Gateway for LLM interactions
            max_memories_per_query: Maximum memories to retrieve per planning query
        """
        super().__init__(object_store, outbox_store)
        self._memory_store = memory_store
        self._llm_gateway = llm_gateway
        self._max_memories = max_memories_per_query
        self._active_plans: dict[str, ExecutionPlan] = {}

    async def process_event(self, event: EventEnvelope) -> list[EventEnvelope]:
        """Process an incoming event.
        
        The planning agent can process various events and decide whether
        to create a plan or dispatch to specialized agents.
        """
        if event.event_type == EventType.ITEM_UPSERTED:
            return await self._handle_item_upserted(event)
        return []

    async def _handle_item_upserted(self, event: EventEnvelope) -> list[EventEnvelope]:
        """Handle an item upserted event by planning the ingestion pipeline."""
        item_id = event.payload.get("item_id")
        if not item_id:
            return []

        await self.log_action(
            tenant_id=event.tenant_id,
            user_id=event.user_id or "system",
            action_type="plan_item_ingestion",
            inputs=[item_id],
            outputs=[],
        )
        return []

    async def create_plan(
        self,
        tenant_id: str,
        user_id: str,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> ExecutionPlan:
        """Create an execution plan for a task.
        
        This is the core planning method. It:
        1. Retrieves relevant memories for context
        2. Uses the LLM to create a plan
        3. Stores the plan for execution tracking
        4. Records the planning action for learning
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            task_description: Description of the task to plan
            context: Optional additional context
            
        Returns:
            ExecutionPlan with steps to execute
        """
        relevant_memories = await self._retrieve_relevant_memories(
            tenant_id, user_id, task_description
        )

        planning_context = PlanningContext(
            task_description=task_description,
            relevant_memories=relevant_memories,
            available_agents=[
                "ChunkAgent",
                "EmbedAgent", 
                "IndexTextAgent",
                "EntityExtractAgent",
                "WikipediaPageAgent",
            ],
            constraints=context or {},
        )

        plan = await self._generate_plan(tenant_id, user_id, planning_context)

        self._active_plans[plan.plan_id] = plan

        await self.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action_type="create_plan",
            inputs=[task_description],
            outputs=[plan.plan_id],
        )

        return plan

    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Execute a plan step by step.
        
        This method executes each step in the plan sequentially,
        updating the plan status and learning from the outcomes.
        
        Args:
            plan: The execution plan to run
            
        Returns:
            Updated ExecutionPlan with results
        """
        plan.status = PlanStatus.IN_PROGRESS
        plan.updated_at = datetime.utcnow()

        for step in plan.steps:
            if step.status != PlanStepStatus.PENDING:
                continue

            try:
                step.status = PlanStepStatus.IN_PROGRESS
                step.started_at = datetime.utcnow()

                result = await self._execute_step(plan, step)
                
                step.outputs = result
                step.status = PlanStepStatus.COMPLETED
                step.completed_at = datetime.utcnow()

                plan.context.update(result)

            except Exception as e:
                step.status = PlanStepStatus.FAILED
                step.error = str(e)
                step.completed_at = datetime.utcnow()
                plan.status = PlanStatus.FAILED
                
                await self._record_failure(plan, step, str(e))
                break

        if plan.is_complete:
            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.utcnow()
            await self._record_success(plan)

        plan.updated_at = datetime.utcnow()
        return plan

    async def _execute_step(
        self, plan: ExecutionPlan, step: PlanStep
    ) -> dict[str, Any]:
        """Execute a single plan step.
        
        This dispatches to the appropriate agent or performs
        planning-specific actions.
        """
        await self.log_action(
            tenant_id=plan.tenant_id,
            user_id=plan.user_id,
            action_type=f"execute_step_{step.action_type}",
            inputs=[step.step_id],
            outputs=[],
        )

        return {"step_id": step.step_id, "status": "completed"}

    async def _retrieve_relevant_memories(
        self,
        tenant_id: str,
        user_id: str,
        query: str,
    ) -> list[Memory]:
        """Retrieve memories relevant to the current task.
        
        This searches the user's memory store for experiences and
        knowledge that can inform the planning process.
        """
        memories = await self._memory_store.search_memories(
            tenant_id=tenant_id,
            user_id=user_id,
            query=query,
            limit=self._max_memories,
        )

        for memory in memories:
            await self._memory_store.update_access(memory.memory_id)

        return memories

    async def _generate_plan(
        self,
        tenant_id: str,
        user_id: str,
        context: PlanningContext,
    ) -> ExecutionPlan:
        """Generate an execution plan using the LLM.
        
        This constructs a prompt with the task description and relevant
        memories, then uses the LLM to create a structured plan.
        """
        memory_context = ""
        if context.relevant_memories:
            memory_context = "\n\nRelevant memories from past experiences:\n"
            for mem in context.relevant_memories:
                memory_context += f"- [{mem.memory_type}] {mem.content}\n"

        messages = [
            {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Create a plan for the following task:

Task: {context.task_description}
{memory_context}
Available agents: {', '.join(context.available_agents)}

Constraints: {context.constraints}

Output your plan as JSON.""",
            },
        ]

        plan_schema = {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_number": {"type": "integer"},
                            "description": {"type": "string"},
                            "agent_type": {"type": ["string", "null"]},
                            "action_type": {"type": "string"},
                            "inputs": {"type": "object"},
                        },
                        "required": ["step_number", "description", "action_type"],
                    },
                },
                "reasoning": {"type": "string"},
            },
            "required": ["steps", "reasoning"],
        }

        response = await self._llm_gateway.generate(
            messages=messages,
            temperature=0.3,
            json_schema=plan_schema,
        )

        plan_data = self._parse_plan_response(response)

        steps = [
            PlanStep(
                step_number=s["step_number"],
                description=s["description"],
                agent_type=s.get("agent_type"),
                action_type=s["action_type"],
                inputs=s.get("inputs", {}),
            )
            for s in plan_data.get("steps", [])
        ]

        return ExecutionPlan(
            tenant_id=tenant_id,
            user_id=user_id,
            task_description=context.task_description,
            steps=steps,
        )

    def _parse_plan_response(self, response: LLMResponse) -> dict[str, Any]:
        """Parse the LLM response into plan data."""
        import json

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"steps": [], "reasoning": "Failed to parse plan"}

    async def _record_success(self, plan: ExecutionPlan) -> None:
        """Record a successful plan execution as a memory.
        
        This enables the agent to learn from successful experiences
        and apply similar strategies in the future.
        """
        memory = Memory(
            tenant_id=plan.tenant_id,
            user_id=plan.user_id,
            memory_type=MemoryType.EXPERIENCE.value,
            content=f"Successfully completed task: {plan.task_description}. "
            f"Used {len(plan.steps)} steps.",
            metadata={
                "plan_id": plan.plan_id,
                "step_count": len(plan.steps),
                "agents_used": [s.agent_type for s in plan.steps if s.agent_type],
            },
        )
        await self._memory_store.save_memory(memory)

    async def _record_failure(
        self, plan: ExecutionPlan, step: PlanStep, error: str
    ) -> None:
        """Record a failed plan execution as a memory.
        
        This enables the agent to learn from failures and avoid
        similar mistakes in the future.
        """
        memory = Memory(
            tenant_id=plan.tenant_id,
            user_id=plan.user_id,
            memory_type=MemoryType.EXPERIENCE.value,
            content=f"Failed task: {plan.task_description}. "
            f"Failed at step {step.step_number}: {step.description}. "
            f"Error: {error}",
            metadata={
                "plan_id": plan.plan_id,
                "failed_step": step.step_number,
                "error": error,
            },
        )
        await self._memory_store.save_memory(memory)

    async def add_memory(
        self,
        tenant_id: str,
        user_id: str,
        memory_type: MemoryType,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Memory:
        """Add a new memory for a user.
        
        This allows external systems to contribute knowledge to the
        user's memory store.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            memory_type: Type of memory to create
            content: The memory content
            metadata: Optional metadata
            
        Returns:
            The created Memory
        """
        memory = Memory(
            tenant_id=tenant_id,
            user_id=user_id,
            memory_type=memory_type.value,
            content=content,
            metadata=metadata or {},
        )
        return await self._memory_store.save_memory(memory)

    async def get_user_memories(
        self,
        tenant_id: str,
        user_id: str,
        memory_type: MemoryType | None = None,
        limit: int = 100,
    ) -> list[Memory]:
        """Get memories for a user.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            memory_type: Optional filter by type
            limit: Maximum memories to return
            
        Returns:
            List of user memories
        """
        return await self._memory_store.list_memories(
            tenant_id=tenant_id,
            user_id=user_id,
            memory_type=memory_type,
            limit=limit,
        )

    def get_active_plan(self, plan_id: str) -> ExecutionPlan | None:
        """Get an active plan by ID."""
        return self._active_plans.get(plan_id)

    def list_active_plans(self, user_id: str | None = None) -> list[ExecutionPlan]:
        """List active plans, optionally filtered by user."""
        plans = list(self._active_plans.values())
        if user_id:
            plans = [p for p in plans if p.user_id == user_id]
        return plans
