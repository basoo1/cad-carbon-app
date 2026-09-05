"""
Module: app.py
Application: VERDANT - Autonomous Engineering Co-Pilot for Sustainable DFM
Purpose:
    Serves the primary Streamlit user interface for VERDANT.
    Handles user interaction workflows including:
    - Ingesting parametric STEP and triangulated mesh CAD models
    - Displaying 1:1 true-scale 3D WebGL visualizations and Ashby trade-off plots
    - Presenting deterministic structural and thermal metric calculations
    - Invoking the Gemini 3.5 Flash reasoning engine for autonomous diagnosis
    - Facilitating interactive design review dialogues and exporting formal ECP reports
"""

import os
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from materialDatabase import materialDatabase
from cadParser import parseCadFile
from physicsEngine import computePhysicalInvariants
from geminiAdvisor import queryGeminiEngineer, chatWithEngineer, generateFormalEcpReport, geminiApiKey

# Page Setup and Session State Initialization
# Session state preserves user chat history and generated
# ECP markdown between Streamlit UI reruns.

st.set_page_config(
    page_title="VERDANT | Sustainable DFM and CAD Co-Pilot",
    layout="wide"
)

if "chatMessages" not in st.session_state:
    st.session_state.chatMessages = []

if "ecpReportContent" not in st.session_state:
    st.session_state.ecpReportContent = None

st.title("VERDANT: Autonomous Engineering Co-Pilot")
st.caption("Physics-Grounded DFM Optimization, Parametric B-Rep Analysis, and Multi-Objective Eco-Design")


# Sidebar User Inputs for Operational Boundary Conditions
# Configures material parameters, environment, mechanical
# loads, and thermal boundaries.

st.sidebar.header("Material and Environment")

materialOptions = {key: data["displayName"] for key, data in materialDatabase.items()}
selectedMaterialKey = st.sidebar.selectbox(
    "Baseline Material",
    options=list(materialOptions.keys()),
    format_func=lambda materialKey: materialOptions[materialKey],
    index=0
)

environmentType = st.sidebar.selectbox(
    "Operating Environment",
    options=["indoor", "outdoorUv", "marineCorrosive", "chemicalContact"],
    format_func=lambda envKey: {
        "indoor": "Indoor / Controlled",
        "outdoorUv": "Outdoor (UV Exposure and Weather)",
        "marineCorrosive": "Marine / Saline Corrosive",
        "chemicalContact": "Industrial Solvent / Chemical"
    }[envKey]
)

st.sidebar.header("Mechanical Loading")
loadType = st.sidebar.selectbox("Primary Load Direction", options=["compressive", "tensile", "bending"])
appliedForceN = st.sidebar.number_input("Applied Force (N)", min_value=10.0, max_value=1000000.0, value=8000.0, step=500.0)

st.sidebar.header("Thermal Environment")
tempCol1, tempCol2 = st.sidebar.columns(2)
with tempCol1:
    tempMinC = st.number_input("Min Temp (C)", value=-10.0, step=5.0)
with tempCol2:
    tempMaxC = st.number_input("Max Temp (C)", value=65.0, step=5.0)

isConstrainedThermal = st.sidebar.checkbox(
    "Rigidly Constrained Assembly?",
    value=False,
    help="Enable if thermal expansion is constrained by adjacent rigid mounting interfaces."
)


def render3dMesh(vertices, faces):
    """
    Renders 3D geometry using Plotly Mesh3d.
    Enforces aspectmode='data' to preserve exact physical aspect ratios (1:1 scale)
    and prevent thin parts from distorting into cubes.
    """
    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                color="#00ADB5",
                opacity=0.85,
                flatshading=True,
            )
        ]
    )
    fig.update_layout(
        scene=dict(
            aspectmode="data",
            xaxis=dict(showbackground=False, title="X (mm)"),
            yaxis=dict(showbackground=False, title="Y (mm)"),
            zaxis=dict(showbackground=False, title="Z (mm)"),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=340,
    )
    return fig


def renderAshbyPlot(activeBaselineKey):
    """
    Generates a 2D Ashby scatter plot comparing material yield strength
    against embodied carbon footprint to visualize Pareto trade-offs.
    """
    materialNames = [data["displayName"] for data in materialDatabase.values()]
    yieldStrengths = [data["yieldStrengthMpa"] for data in materialDatabase.values()]
    carbonFactors = [data["carbonFactorKgCo2ePerKg"] for data in materialDatabase.values()]
    allKeys = list(materialDatabase.keys())

    markerColors = ["#FF5722" if key == activeBaselineKey else "#3F51B5" for key in allKeys]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=carbonFactors,
            y=yieldStrengths,
            mode="markers+text",
            text=materialNames,
            textposition="top right",
            marker=dict(size=12, color=markerColors, line=dict(width=1, color="DarkSlateGrey")),
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title="Ashby Trade-Off: Strength vs. Embodied Carbon",
        xaxis_title="Embodied Carbon (kg CO2e / kg)",
        yaxis_title="Yield Strength (MPa)",
        margin=dict(l=40, r=40, b=40, t=40),
        height=340,
    )
    return fig

# Main Workspace Routing
# Views:
# 1. Design Workspace and Co-Pilot: Active geometry analysis,
#    Ashby charts, AI deck, and live chat.
# 2. Formal ECP Audit Report: Exportable document view for
#    finalized engineering proposals.

tabWorkspace, tabReport = st.tabs(["Design Workspace and Co-Pilot", "Formal ECP Audit Report"])

with tabWorkspace:
    uploadedFile = st.file_uploader(
        "Upload 3D CAD Geometry (.step, .stp, .stl, .obj)",
        type=["step", "stp", "stl", "obj"]
    )

    if uploadedFile is not None:
        try:
            fileBytes = uploadedFile.getvalue()
            cadMetrics = parseCadFile(fileBytes, uploadedFile.name)

            operationalParams = {
                "baselineMaterialKey": selectedMaterialKey,
                "loadType": loadType,
                "appliedForceN": appliedForceN,
                "tempMinC": tempMinC,
                "tempMaxC": tempMaxC,
                "tempDeltaC": abs(tempMaxC - tempMinC),
                "environmentType": environmentType,
                "isConstrainedThermal": isConstrainedThermal,
            }

            invariantsPayload = computePhysicalInvariants(cadMetrics, operationalParams)
            baseline = invariantsPayload["baselineSummary"]

            # Display deterministic structural and geometric invariants
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("CAD Solid", f"{'B-Rep STEP' if cadMetrics['isBRep'] else 'Mesh STL'}")
            col2.metric("Nominal Mass", f"{baseline['massKg']} kg")
            col3.metric("Embodied CO2e", f"{baseline['embodiedCo2eKg']} kg")
            col4.metric(
                "Stress and SF",
                f"{baseline['appliedStressMpa']} MPa",
                f"{baseline['safetyFactor']}x SF",
                delta_color="normal" if baseline["safetyFactor"] >= 1.5 else "inverse"
            )
            col5.metric(
                "Buckling Risk",
                "High Risk" if baseline["isBucklingRisk"] else "Low Risk",
                delta_color="inverse" if baseline["isBucklingRisk"] else "normal"
            )

            st.markdown("---")

            # Render 3D CAD view and 2D Ashby material selection space
            viewCol, ashbyCol = st.columns([1, 1])
            with viewCol:
                st.subheader("3D CAD Geometry")
                st.plotly_chart(render3dMesh(cadMetrics["vertices"], cadMetrics["faces"]), use_container_width=True)
                st.caption(f"Bounding Box: {baseline['extentsMm'][0]} x {baseline['extentsMm'][1]} x {baseline['extentsMm'][2]} mm | True Ixx: {baseline['momentOfInertiaMm4']} mm4")

            with ashbyCol:
                st.subheader("Material Selection Space")
                st.plotly_chart(renderAshbyPlot(selectedMaterialKey), use_container_width=True)

            st.markdown("---")

            # Execute Gemini 3.5 Flash autonomous reasoning pipeline
            hasValidApiKey = geminiApiKey and geminiApiKey != "YOUR_GEMINI_API_KEY_HERE"

            if hasValidApiKey:
                with st.spinner("Analyzing boundary invariants and generating Pareto trade-off proposals..."):
                    try:
                        aiReport = queryGeminiEngineer(invariantsPayload)

                        # Render discovered bottlenecks
                        st.subheader("Identified Engineering Bottlenecks and Inefficiencies")
                        bottleneckColumns = st.columns(len(aiReport.identifiedBottlenecks))
                        for index, bottleneck in enumerate(aiReport.identifiedBottlenecks):
                            with bottleneckColumns[index]:
                                st.markdown(f"#### [{bottleneck.severity.upper()}] {bottleneck.phenomenon}")
                                st.markdown(f"**Zone:** `{bottleneck.affectedRegion}`")
                                st.write(bottleneck.rootCause)

                        st.markdown("---")

                        # Render multi-strategy Pareto trade-off deck
                        st.subheader("Engineering Strategy Deck (Pareto Exploration)")
                        tabTitles = [f"{proposal.badge} - {proposal.strategyName}" for proposal in aiReport.engineeringProposals]
                        strategyTabs = st.tabs(tabTitles)

                        for index, strategyTab in enumerate(strategyTabs):
                            proposal = aiReport.engineeringProposals[index]
                            with strategyTab:
                                st.markdown(f"### {proposal.strategyName}")

                                metricCol1, metricCol2, metricCol3, metricCol4 = st.columns(4)
                                metricCol1.metric("Selected Material", proposal.recommendedMaterial)
                                metricCol2.metric("CO2e Reduction", f"-{proposal.carbonReductionPct}%")
                                metricCol3.metric("Cost Impact", f"{'+' if proposal.costDeltaPct > 0 else ''}{proposal.costDeltaPct}%")
                                metricCol4.metric("Optimized Mass", f"{proposal.estimatedNewMassKg} kg")

                                st.markdown("#### Structural and Thermal Justification")
                                st.markdown(f"**Structural Mechanics:** {proposal.structuralFeasibility}")
                                st.markdown(f"**Thermal Expansion:** {proposal.thermalFeasibility}")

                                st.markdown("#### Actionable CAD and DFM Redesign Checklist")
                                for modificationStep in proposal.cadModifications:
                                    st.markdown(f"- {modificationStep}")

                    except Exception as aiError:
                        st.error(f"Gemini Reasoning Engine Error: {str(aiError)}")
            else:
                st.warning("Configure a valid Gemini API key in geminiAdvisor.py to run the autonomous reasoning engine.")

            st.markdown("---")

            # Interactive design review and contextual engineering chat
            st.subheader("Interactive Design Review and Context Chat")
            st.caption("Provide operating context (fatigue limits, mounting constraints, vibration spectrums) to refine engineering reasoning.")

            for message in st.session_state.chatMessages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            userQuery = st.chat_input("Specify load cases, fatigue requirements, or packaging constraints...")
            if userQuery:
                st.session_state.chatMessages.append({"role": "user", "content": userQuery})
                with st.chat_message("user"):
                    st.markdown(userQuery)

                with st.chat_message("assistant"):
                    if hasValidApiKey:
                        with st.spinner("Evaluating operational context against CAD invariants..."):
                            try:
                                botReply = chatWithEngineer(invariantsPayload, st.session_state.chatMessages, userQuery)
                            except Exception as chatError:
                                botReply = f"Error generating reply: {str(chatError)}"
                            st.markdown(botReply)
                            st.session_state.chatMessages.append({"role": "assistant", "content": botReply})
                    else:
                        warningReply = "A valid Gemini API Key is required to engage in technical design review chat."
                        st.markdown(warningReply)
                        st.session_state.chatMessages.append({"role": "assistant", "content": warningReply})

            # Compile ECP report action button
            st.markdown("---")
            buttonCol1, buttonCol2 = st.columns([2, 1])
            with buttonCol1:
                st.write("Ready to synthesize this session into a formal engineering audit?")
            with buttonCol2:
                if st.button("Compile Formal ECP Report", use_container_width=True):
                    if hasValidApiKey:
                        with st.spinner("Synthesizing CAD metrics, physics calculations, and chat dialogue into formal ECP document..."):
                            try:
                                reportMarkdown = generateFormalEcpReport(invariantsPayload, st.session_state.chatMessages)
                                st.session_state.ecpReportContent = reportMarkdown
                                st.success("Formal ECP Report generated. View and export in the 'Formal ECP Audit Report' tab.")
                            except Exception as reportError:
                                st.error(f"Error generating ECP report: {str(reportError)}")
                    else:
                        st.error("A valid Gemini API Key is required to compile the formal ECP report.")

        except Exception as pipelineError:
            st.error(f"Analysis Pipeline Error: {str(pipelineError)}")
    else:
        st.info("Upload a .step, .stp, .stl, or .obj file to initiate analysis.")

with tabReport:
    if st.session_state.ecpReportContent:
        st.download_button(
            label="Download Formal ECP Report (.md)",
            data=st.session_state.ecpReportContent,
            file_name="VERDANT_ECP_Audit_Report.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.markdown("---")
        st.markdown(st.session_state.ecpReportContent)
    else:
        st.info("No report has been compiled yet. Conduct your analysis in the workspace tab and select 'Compile Formal ECP Report'.")