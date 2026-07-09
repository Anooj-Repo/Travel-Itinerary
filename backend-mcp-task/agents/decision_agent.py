"""
Decision Agent - Agent 9
Consolidates all agent outputs and generates final assignment recommendations
"""
from agents import Agent
from typing import Dict, Any, List
import json

class DecisionAgent(Agent):
    """
    Consolidates outputs from all agents and makes final routing decisions.
    This is the 9th agent in the pipeline (LLM Call 5).
    """
    
    def __init__(self):
        super().__init__(
            name="DecisionAgent",
            description="Makes final routing decisions based on all agent outputs"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final assignment recommendations
        
        Args:
            context: Contains outputs from all previous agents
        
        Returns:
            Final routing decisions
        """
        self.log("Starting decision making...")
        
        # Get data from all previous agents
        tasks = context.get('TaskClassificationAgent', {}).get('classified_tasks', [])
        resource_matching = context.get('ResourceMatchingAgent', {})
        workload_optimization = context.get('WorkloadOptimizationAgent', {})
        cost_optimization = context.get('CostOptimizationAgent', {})
        risk_sla = context.get('RiskSLAAgent', {})
        
        if not tasks:
            self.log("No tasks to make decisions on")
            return {
                "final_decisions": [],
                "status": "no_data"
            }
        
        # Generate decisions for each task
        final_decisions = []
        
        for i, task in enumerate(tasks):
            self.log(f"Making decision for task {i+1}/{len(tasks)}: {task.get('task_name')}")
            decision = self.make_task_decision(task, i, context)
            final_decisions.append(decision)
        
        # Generate executive decision summary
        decision_summary = self.generate_decision_summary(final_decisions)
        
        return {
            "final_decisions": final_decisions,
            "decision_summary": decision_summary,
            "total_decisions": len(final_decisions),
            "status": "success"
        }
    
    def make_task_decision(self, task: Dict, task_index: int, context: Dict) -> Dict:
        """Make routing decision for a single task using LLM"""
        
        # Gather all relevant data for this task
        task_data = {
            "task_name": task.get('task_name'),
            "description": task.get('description'),
            "complexity": task.get('complexity'),
            "priority": task.get('priority'),
            "estimated_effort": task.get('estimated_effort'),
            "skills_required": task.get('skills_required'),
            "category": task.get('category')
        }
        
        # Get resource recommendations
        resource_matching = context.get('ResourceMatchingAgent', {})
        task_recommendations = resource_matching.get('task_recommendations', [])
        resource_options = []
        if task_index < len(task_recommendations):
            matched_resources = task_recommendations[task_index].get('matched_resources', [])
            resource_options = matched_resources[:5]  # Top 5 options
        
        # Get cost analysis
        cost_optimization = context.get('CostOptimizationAgent', {})
        task_cost_analyses = cost_optimization.get('task_cost_analysis', [])
        cost_data = {}
        if task_index < len(task_cost_analyses):
            cost_data = task_cost_analyses[task_index]
        
        # Get risk analysis
        risk_sla = context.get('RiskSLAAgent', {})
        task_risk_analyses = risk_sla.get('task_risk_analyses', [])
        risk_data = {}
        if task_index < len(task_risk_analyses):
            risk_data = task_risk_analyses[task_index]
        
        # Get workload insights
        workload_optimization = context.get('WorkloadOptimizationAgent', {})
        workload_analysis = workload_optimization.get('workload_analysis', {})
        
        # Use LLM to make final decision
        system_prompt = """You are an intelligent task routing decision maker. You must analyze all available data and recommend the BEST resource assignment for a task.

Consider:
1. Skill match quality (higher is better)
2. Resource availability and workload
3. Cost efficiency (balance cost vs quality)
4. Risk factors (SLA, quality risks)
5. Priority and complexity

Your decision should BALANCE all factors, not just optimize for one. Critical tasks should prioritize quality and SLA compliance over cost.

Return a JSON object with:
- recommended_resource_name: Name of the recommended resource
- recommended_resource_type: "human" or "ai"
- recommended_resource_id: ID of the resource
- confidence_score: 0-100 confidence in this decision
- reasoning: Detailed explanation of why this resource is recommended
- alternative_resource: Name of second-best option
- key_factors: List of key factors that influenced the decision"""
        
        # Prepare decision context
        decision_context = json.dumps({
            "task": task_data,
            "resource_options": resource_options,
            "cost_analysis": {
                "best_value": cost_data.get('best_value', {}),
                "cheapest": cost_data.get('cheapest_option', {}),
                "cost_range": cost_data.get('cost_range', {})
            },
            "risk_analysis": {
                "overall_risk_level": risk_data.get('overall_risk_level', 'Unknown'),
                "breach_risk": risk_data.get('breach_risk', {}),
                "quality_risk": risk_data.get('quality_risk', {}),
                "mitigation_recommendations": risk_data.get('mitigation_recommendations', [])
            },
            "workload_context": {
                "overloaded_count": workload_analysis.get('overload_count', 0),
                "underutilized_count": workload_analysis.get('underutilized_count', 0)
            }
        }, indent=2)
        
        user_message = f"""Make the optimal routing decision for this task:

{decision_context}

Select the BEST resource considering all factors. Critical and High priority tasks should prioritize quality and SLA compliance."""
        
        # Call LLM
        llm_response = self.call_llm(system_prompt, user_message, temperature=0.4, response_format='json')
        
        try:
            decision = json.loads(llm_response)
            
            # Merge decision with original data
            return {
                **task_data,
                "task_id": task.get('task_id', task_index + 1),
                "recommended_resource": {
                    "name": decision.get('recommended_resource_name'),
                    "type": decision.get('recommended_resource_type'),
                    "id": decision.get('recommended_resource_id')
                },
                "alternative_resource": decision.get('alternative_resource'),
                "confidence_score": decision.get('confidence_score', 70),
                "reasoning": decision.get('reasoning', ''),
                "key_factors": decision.get('key_factors', []),
                "cost_estimate": cost_data.get('best_value', {}).get('total_cost', 0),
                "risk_level": risk_data.get('overall_risk_level', 'Unknown'),
                "decision_timestamp": "2026-07-10"
            }
        
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse LLM decision: {str(e)}")
            # Fallback: use simple logic
            return self.fallback_decision(task, task_index, resource_options, cost_data, risk_data)
    
    def fallback_decision(self, task: Dict, task_index: int, resource_options: List, cost_data: Dict, risk_data: Dict) -> Dict:
        """Simple fallback decision logic"""
        
        # Pick highest skill match with good workload
        best_resource = resource_options[0] if resource_options else {}
        
        return {
            "task_id": task.get('task_id', task_index + 1),
            "task_name": task.get('task_name'),
            "complexity": task.get('complexity'),
            "priority": task.get('priority'),
            "recommended_resource": {
                "name": best_resource.get('name', 'Unknown'),
                "type": best_resource.get('type', 'human'),
                "id": best_resource.get('resource_id', 0)
            },
            "confidence_score": 60,
            "reasoning": "Fallback decision based on skill match",
            "key_factors": ["Skill Match"],
            "cost_estimate": cost_data.get('best_value', {}).get('total_cost', 0),
            "risk_level": risk_data.get('overall_risk_level', 'Unknown')
        }
    
    def generate_decision_summary(self, decisions: List[Dict]) -> Dict:
        """Generate summary of all decisions"""
        
        total = len(decisions)
        ai_assignments = len([d for d in decisions if d.get('recommended_resource', {}).get('type') == 'ai'])
        human_assignments = total - ai_assignments
        
        high_confidence = len([d for d in decisions if d.get('confidence_score', 0) >= 80])
        medium_confidence = len([d for d in decisions if 60 <= d.get('confidence_score', 0) < 80])
        low_confidence = len([d for d in decisions if d.get('confidence_score', 0) < 60])
        
        high_risk_assignments = len([d for d in decisions if d.get('risk_level') == 'High'])
        
        total_cost = sum([d.get('cost_estimate', 0) for d in decisions])
        
        return {
            "total_tasks": total,
            "ai_assignments": ai_assignments,
            "human_assignments": human_assignments,
            "assignment_distribution": {
                "AI": ai_assignments,
                "Human": human_assignments
            },
            "confidence_distribution": {
                "High (≥80)": high_confidence,
                "Medium (60-79)": medium_confidence,
                "Low (<60)": low_confidence
            },
            "high_risk_assignments": high_risk_assignments,
            "total_estimated_cost": round(total_cost, 2),
            "average_confidence": round(sum([d.get('confidence_score', 0) for d in decisions]) / total if total > 0 else 0, 2)
        }
