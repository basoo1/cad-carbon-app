"""
Module: geminiAdvisor.py
Purpose:
    Serves as the AI reasoning and synthesis engine for VERDANT.
    Interfaces directly with the Google GenAI SDK using Gemini 3.5 Flash.
    Enforces structured Pydantic schemas to output deterministic,
    physics-grounded engineering proposals, bottleneck diagnoses,
    interactive technical chat responses, and formal ECP reports.
"""

import os
from typing import List, Dict
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

"""
Centralized Gemini API Key configuration.
Paste your active Google AI Studio API key directly into this variable.
Alternatively, set the GEMINI_API_KEY environment variable.
"""
geminiApiKey = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
geminiModelName = "gemini-3.5-flash"


class EngineeringBottleneck(BaseModel):
    """
    Pydantic schema representing an autonomously identified structural,
    thermal, or environmental design bottleneck in the uploaded geometry.
    """
    phenomenon: str = Field(description="Name of the physical risk mechanism such as Euler Buckling, Thermal Binding, or Notch Sensitivity")
    severity: str = Field(description="Severity classification: High, Medium, or Low")
    rootCause: str = Field(description="Physical explanation correlating applied mechanical loads, operating temperature, and CAD invariants")
    affectedRegion: str = Field(description="Specific geometric region identified such as thin web, sharp internal corner, or neutral axis core")


class EngineeringProposal(BaseModel):
    """
    Pydantic schema representing a concrete, multi-objective design strategy
    positioned on the Pareto optimization frontier.
    """
    strategyName: str = Field(description="Descriptive engineering strategy title")
    strategyType: str = Field(description="Strategy category such as Drop-in Replacement, Generative Coring, or Composite Re-engineering")
    badge: str = Field(description="Short UI label such as Zero Re-Tooling or Maximum Lightweighting")
    recommendedMaterial: str = Field(description="Exact substitute material selected from the candidate material pool")
    carbonReductionPct: float = Field(description="Projected percentage reduction in cradle-to-gate embodied carbon")
    costDeltaPct: float = Field(description="Projected percentage change in raw material unit cost, where negative indicates savings")
    estimatedNewMassKg: float = Field(description="Projected optimized mass of the component in kilograms")
    structuralFeasibility: str = Field(description="Mechanics analysis covering yield safety factors, stress distribution, and load path integrity")
    thermalFeasibility: str = Field(description="Thermal analysis covering CTE matching, expansion clearance, and temperature limits")
    cadModifications: List[str] = Field(description="Array of 3 to 5 actionable, dimensional CAD modeling modifications")


class DynamicDiagnosisReport(BaseModel):
    """
    Top-level structured output schema returned by the Gemini reasoning engine.
    Contains both the autonomous bottleneck diagnosis and the Pareto strategy deck.
    """
    identifiedBottlenecks: List[EngineeringBottleneck] = Field(
        description="List of 2 to 3 critical engineering bottlenecks or material inefficiencies discovered in the part"
    )
    engineeringProposals: List[EngineeringProposal] = Field(
        description="List of 3 distinct Pareto trade-off engineering proposals"
    )


def queryGeminiEngineer(invariantsPayload):
    """
    Executes boundary-invariant analysis and Pareto proposal generation.
    Enforces the DynamicDiagnosisReport schema on Gemini 3.5 Flash to guarantee
    valid JSON extraction without conversational formatting or syntax errors.
    """
    if not geminiApiKey or geminiApiKey == "YOUR_GEMINI_API_KEY_HERE":
        raise ValueError("A valid Gemini API key must be defined in geminiAdvisor.py or the GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=geminiApiKey)

    summary = invariantsPayload["baselineSummary"]
    operationalParams = invariantsPayload["operationalParams"]
    materialsPool = invariantsPayload["materialsPool"]

    systemInstruction = """
You are a Principal Mechanical Design and Sustainable Manufacturing Engineer.
You analyze deterministic boundary physics invariants and provide rigorous, unconstrained engineering diagnoses.
Do not generate vague generic advice. Point directly to physical mechanisms, CTE differences, stress tensors, and dimensional CAD modifications.
Do not include emojis.
"""

    prompt = f"""
PHYSICAL AND GEOMETRIC BOUNDARY INVARIANTS:
- CAD Format: {summary.get('cadFormat', 'Parametric Solid')}
- Dimensions: Bounding Box = {summary['extentsMm']} mm, Char Length = {summary['characteristicLengthMm']} mm, Min Thickness = {summary['minThicknessMm']} mm
- Volume: {summary['volumeCm3']} cm3 | Mass: {summary['massKg']} kg | Baseline Carbon: {summary['embodiedCo2eKg']} kg CO2e
- Second Moment of Inertia (Ixx): {summary['momentOfInertiaMm4']} mm4
- Mechanical Loading: {operationalParams['appliedForceN']} N ({operationalParams['loadType']}) -> Nominal Stress: {summary['appliedStressMpa']} MPa (Safety Factor: {summary['safetyFactor']}x)
- Buckling Assessment: Risk = {summary['isBucklingRisk']} (Buckling SF: {summary['bucklingSafetyFactor']}x)
- Thermal Environment: {operationalParams['tempMinC']} C to {operationalParams['tempMaxC']} C (Delta T = {operationalParams['tempDeltaC']} C)
  * Unconstrained Thermal Expansion (Delta L): {summary['deltaLengthMm']} mm
  * Constrained Thermal Stress: {summary['constrainedThermalStressMpa']} MPa
- Field Environment: {operationalParams['environmentType']}
- Baseline Material: {summary['material']}

AVAILABLE CANDIDATE MATERIAL POOL:
{materialsPool}

TASK:
1. Identify 2 to 3 critical engineering bottlenecks or sustainability inefficiencies specific to THIS geometry and load case.
2. Formulate 3 distinct engineering proposals representing different points on the Pareto frontier:
   - Strategy 1: Drop-In / Zero Re-Tooling (Minimal risk, identical mold geometry).
   - Strategy 2: Aggressive Generative Lightweighting (Maximum carbon/mass reduction via DFM coring and ribbing).
   - Strategy 3: Cost-First Circular / Composite (Optimized material cost and stiffness).
"""

    response = client.models.generate_content(
        model=geminiModelName,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=systemInstruction,
            response_mime_type="application/json",
            response_schema=DynamicDiagnosisReport,
            temperature=0.2,
        ),
    )

    return response.parsed


def chatWithEngineer(invariantsPayload, chatHistory, userQuery):
    """
    Maintains a stateful technical design review session.
    Injects immutable CAD invariants into the system instructions and appends
    the conversation history to provide context-aware responses to engineering queries.
    """
    if not geminiApiKey or geminiApiKey == "YOUR_GEMINI_API_KEY_HERE":
        raise ValueError("A valid Gemini API key must be defined in geminiAdvisor.py or the GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=geminiApiKey)

    summary = invariantsPayload["baselineSummary"]
    operationalParams = invariantsPayload["operationalParams"]

    systemInstruction = f"""
You are a Principal Mechanical and Materials Engineer collaborating live with a design engineer.
You are evaluating a specific 3D part with the following fixed CAD invariants:
- Part: {summary['material']} ({summary['massKg']} kg, Volume: {summary['volumeCm3']} cm3, Extents: {summary['extentsMm']} mm)
- Applied Load: {operationalParams['appliedForceN']} N ({operationalParams['loadType']}) -> Nominal Stress: {summary['appliedStressMpa']} MPa (Safety Factor: {summary['safetyFactor']}x)
- Second Moment of Inertia (Ixx): {summary['momentOfInertiaMm4']} mm4
- Thermal Range: {operationalParams['tempMinC']} C to {operationalParams['tempMaxC']} C (Unconstrained Delta L: {summary['deltaLengthMm']} mm)
- Environment: {operationalParams['environmentType']}

Answer questions concisely with rigorous engineering justifications (mention yield strength, fatigue limits, DFM, CTE, corrosion mechanisms).
Do not include emojis.
"""

    conversationLog = []
    for message in chatHistory:
        conversationLog.append(f"{message['role'].upper()}: {message['content']}")
    conversationLog.append(f"USER: {userQuery}")

    response = client.models.generate_content(
        model=geminiModelName,
        contents="\n\n".join(conversationLog),
        config=types.GenerateContentConfig(
            system_instruction=systemInstruction,
            temperature=0.3,
        ),
    )
    return response.text


def generateFormalEcpReport(invariantsPayload, chatHistory):
    """
    Synthesizes the physical CAD measurements, deterministic calculations,
    and interactive chat dialogue into an auditable Engineering Change Proposal (ECP).
    Outputs clean GitHub Markdown with clear technical sections and testing plans.
    """
    if not geminiApiKey or geminiApiKey == "YOUR_GEMINI_API_KEY_HERE":
        raise ValueError("A valid Gemini API key must be defined in geminiAdvisor.py or the GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=geminiApiKey)

    summary = invariantsPayload["baselineSummary"]
    operationalParams = invariantsPayload["operationalParams"]

    systemInstruction = """
You are a Senior Systems and Materials Engineering Director.
Generate an executive, comprehensive Engineering Change Proposal (ECP) Audit Report.
Format using clean GitHub Markdown with clear sections, mathematical formulas, quantitative data tables, and an actionable verification test plan.
Do not include conversational filler or emojis.
"""

    formattedChat = "\n".join([f"- **{message['role'].capitalize()}**: {message['content']}" for message in chatHistory])

    prompt = f"""
Synthesize an Engineering Change Proposal (ECP) for the following component:

BASE COMPONENT INVARIANTS:
- Material: {summary['material']}
- Volume: {summary['volumeCm3']} cm3 | Nominal Mass: {summary['massKg']} kg
- Direct Embodied Carbon: {summary['embodiedCo2eKg']} kg CO2e | Material Cost: ${summary['materialCostUsd']}
- Dimensions: {summary['extentsMm']} mm (Min Wall: {summary['minThicknessMm']} mm)
- Analytical Moment of Inertia (Ixx): {summary['momentOfInertiaMm4']} mm4
- Nominal Applied Stress: {summary['appliedStressMpa']} MPa under {operationalParams['appliedForceN']} N ({operationalParams['loadType']} loading)
- Safety Factor: {summary['safetyFactor']}x | Buckling Risk: {summary['isBucklingRisk']} (SF: {summary['bucklingSafetyFactor']}x)
- Thermal Delta L: {summary['deltaLengthMm']} mm across {operationalParams['tempMinC']} C to {operationalParams['tempMaxC']} C
- Operating Environment: {operationalParams['environmentType']}

TECHNICAL REVIEW AND CHAT CONTEXT:
{formattedChat if chatHistory else "Standard nominal operating review completed without special overrides."}

DOCUMENT STRUCTURE REQUIRED:
# ENGINEERING CHANGE PROPOSAL (ECP) - SUSTAINABILITY AND PERFORMANCE AUDIT
1. ## Executive Summary (High-level decision, carbon delta, mass reduction, cost impact)
2. ## Operating Envelope and Boundary Conditions (Tabulated mechanical, thermal, environmental constraints)
3. ## Structural and Physical Feasibility (Closed-form stress equations, safety factor verification, thermal strain management)
4. ## Step-by-Step CAD and DFM Action Checklist (Concrete dimensional changes: pocket depth, rib placement, fillets, hole tolerances)
5. ## Pre-Production Verification and Testing Plan (Specific ASTM standards, FEA load cases, modal/fatigue validation tests)
"""

    response = client.models.generate_content(
        model=geminiModelName,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=systemInstruction,
            temperature=0.2,
        ),
    )
    return response.text