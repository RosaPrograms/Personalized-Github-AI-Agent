"""Base agent class with planning, tool use, and reflection patterns"""
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from src.tools import OllamaClient
from src.config import settings


class BaseAgent(ABC):
    """Base agent implementing Planning, Tool Use, and Reflection patterns"""

    def __init__(self, name: str, model: Optional[str] = None):
        self.name = name
        self.llm = OllamaClient(model=model)
        self.max_iterations = settings.AGENT_MAX_ITERATIONS
        self.temperature = settings.AGENT_TEMPERATURE
        self.memory: List[Dict[str, str]] = []

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

    @abstractmethod
    def get_available_tools(self) -> str:
        """Return description of available tools"""
        pass

    def plan(self, task: str) -> str:
        """Planning phase: Break down the task into steps"""
        plan_prompt = f"""You are {self.name}. 
        
System: {self.get_system_prompt()}

Available Tools:
{self.get_available_tools()}

User Task: {task}

Create a detailed step-by-step plan to accomplish this task. Format your response as:
PLAN:
1. [First step]
2. [Second step]
...

Be concise and direct."""

        response = self.llm.generate(plan_prompt, temperature=self.temperature)
        return response.get("response", "")

    def execute_step(self, step: str, context: str) -> str:
        """Tool Use phase: Execute a single step using available tools"""
        execution_prompt = f"""You are {self.name}.

System: {self.get_system_prompt()}

Available Tools:
{self.get_available_tools()}

Current Context:
{context}

Execute this step: {step}

Respond with:
ACTION: [what you're doing]
RESULT: [the result or analysis]

Be concise."""

        response = self.llm.generate(
            execution_prompt, temperature=self.temperature)
        return response.get("response", "")

    def reflect(self, task: str, results: List[str]) -> Dict[str, Any]:
        """Reflection phase: Analyze results and make decisions"""
        results_text = "\n".join(
            [f"Result {i+1}: {r}" for i, r in enumerate(results)])

        reflection_prompt = f"""You are {self.name}.

Task: {task}

Execution Results:
{results_text}

Reflect on these results and provide:
1. SUMMARY: [brief summary of what was accomplished]
2. ANALYSIS: [key findings and insights]
3. DECISION: [what action should be taken]

Be direct and structured."""

        response = self.llm.generate(
            reflection_prompt, temperature=self.temperature)
        text = response.get("response", "")

        # Parse response
        return self._parse_reflection(text)

    def _parse_reflection(self, text: str) -> Dict[str, str]:
        """Parse reflection response into structured format"""
        result = {
            "summary": "",
            "analysis": "",
            "decision": ""
        }

        sections = text.split("\n")
        current_key = None

        for line in sections:
            if "SUMMARY:" in line:
                current_key = "summary"
                result["summary"] = line.split("SUMMARY:")[1].strip()
            elif "ANALYSIS:" in line:
                current_key = "analysis"
                result["analysis"] = line.split("ANALYSIS:")[1].strip()
            elif "DECISION:" in line:
                current_key = "decision"
                result["decision"] = line.split("DECISION:")[1].strip()
            elif current_key and line.strip():
                result[current_key] += " " + line.strip()

        return result

    def execute(self, task: str) -> Dict[str, Any]:
        """Main execution loop: Planning -> Tool Use -> Reflection"""
        print(f"\n[{self.name}] Starting execution...")

        # Phase 1: Planning
        print(f"[{self.name}] Phase 1: Planning...")
        plan = self.plan(task)
        print(f"[{self.name}] Plan: {plan[:200]}...")

        # Phase 2: Tool Use
        print(f"[{self.name}] Phase 2: Executing steps...")
        results = []
        steps = self._extract_steps(plan)
        context = task

        for i, step in enumerate(steps[:self.max_iterations]):
            print(f"[{self.name}] Step {i+1}: {step[:100]}...")
            result = self.execute_step(step, context)
            results.append(result)
            context += f"\nStep {i+1} Result: {result}"

        # Phase 3: Reflection
        print(f"[{self.name}] Phase 3: Reflecting...")
        reflection = self.reflect(task, results)

        return {
            "agent": self.name,
            "task": task,
            "plan": plan,
            "steps_executed": len(steps),
            "results": results,
            "reflection": reflection,
            "final_decision": reflection.get("decision", "")
        }

    def _extract_steps(self, plan: str) -> List[str]:
        """Extract numbered steps from plan"""
        steps = []
        for line in plan.split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and "." in line:
                step = line.split(".", 1)[1].strip()
                steps.append(step)
        return steps
