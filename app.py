"""VERDANT — a guided workspace for lower-impact component design."""
import hashlib
import html
import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from cadParser import parseCadFile
from physicsEngine import computePhysicalInvariants
from materialDatabase import materialDatabase
from geminiAdvisor import queryGeminiEngineer, chatWithEngineer, generateFormalEcpReport, geminiApiKey

st.set_page_config(page_title="Verdant · Design with less", page_icon="🌿", layout="wide")
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {color-scheme:light;}
[data-testid="stHeaderActionElements"] {display:none!important;}
a.anchor-link {display:none!important;}
.stApp {background:#f5f7f3;color:#213c32;font-family:'DM Sans',sans-serif;}
h1,h2,h3 {font-family:'Manrope',sans-serif!important;letter-spacing:-.045em!important;color:#173c2c!important;}
h1 {font-size:2.8rem!important;font-weight:800!important;} h2 {font-size:1.55rem!important;} h3 {font-size:1.15rem!important;}
[data-testid="stHeader"] {background:#f5f7f3e8;} .block-container {max-width:1440px;padding-top:4rem;padding-bottom:4rem;}
[data-testid="stSidebar"] {background:#ebf0e8;border-right:1px solid #dbe3d7;} [data-testid="stSidebar"] .block-container {padding-top:0!important;}
[data-testid="stSidebarUserContent"] {padding-top:0!important;}
[data-testid="stSidebarHeader"] {padding-top:0!important;padding-bottom:0!important;min-height:0!important;height:0!important;overflow:visible;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:16px!important;}
[data-testid="stMetric"] {background:white;padding:20px;border:1px solid #e1e7dd;border-radius:14px;}
[data-testid="stMetricValue"] {font-family:'Manrope',sans-serif;font-size:1.8rem;color:#193e2b;}
[data-testid="stMetricLabel"] {color:#69796b;font-size:.8rem;}
.stButton button,.stDownloadButton button {border-radius:9px;min-height:42px;font-weight:600;}
.stButton button[kind="primary"] {background:#244e39;border:1px solid #244e39;color:white;}
.stButton button[kind="primary"]:hover {background:#366c4e;border-color:#366c4e;}
[data-baseweb="tab-list"] {gap:8px;border-bottom:0;margin-bottom:20px;padding:6px;background:#e3eadf;border-radius:12px;flex-wrap:wrap;height:auto;}
[data-baseweb="tab"] {color:#354f3e;padding:12px 20px;border-radius:8px;min-height:48px;height:auto;flex:1;white-space:normal;}
[data-baseweb="tab"] p {font-size:15px;font-weight:700;}
[data-baseweb="tab"][aria-selected="true"] {background:#244e39;color:#fff;}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"] {display:none;}
[data-baseweb="tab"]:focus-visible {outline:3px solid #709965;outline-offset:2px;}
[data-testid="stFileUploader"] {background:#fff;border-radius:12px;}
.brand {font-family:Manrope,sans-serif;font-weight:800;font-size:26px;letter-spacing:-1px;margin-bottom:3px;}
.brand span {color:#7d9c55;} .eyebrow {color:#4d634f;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;}
.subtle {color:#4d634f;font-size:13px;line-height:1.6;} .hero {border-radius:14px;padding:18px 24px;background:#e4eddf;margin:4px 0 12px;}
.hero h1 {font-size:1.85rem!important;margin:0 0 6px;padding:0!important;max-width:none;line-height:1.25!important;} .hero p {color:#425d3c;font-size:14px;line-height:1.5;margin:0;}
.pill {display:inline-block;border:1px solid #c8d8bf;border-radius:30px;padding:5px 12px;font-size:11px;color:#4d6845;letter-spacing:.5px;}
.step {font-size:12px;color:#6e8065;padding:0 0 20px;letter-spacing:.3px;} .step b {color:#244e39;} .step span {margin:0 18px;color:#a3b09b;}
.file-name {font-family:Manrope,sans-serif;font-size:22px;font-weight:700;color:#244e39;overflow-wrap:anywhere;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color:#4d634f!important;opacity:1;}
@media(max-width:700px){.hero h1{font-size:1.5rem!important}.hero{padding:16px}[data-baseweb="tab"]{padding:10px 12px}.block-container{padding-left:1rem;padding-right:1rem}}
</style>''', unsafe_allow_html=True)

for key, default in dict(chatMessages=[], ecpReportContent=None, aiReport=None, contextKey=None, sample=None, analyzedModel=None, activeModel=None, analyzedContext=None).items():
    if key not in st.session_state:
        st.session_state[key] = default


def error_message(exc):
    return str(exc).replace(geminiApiKey, "[hidden]") if geminiApiKey else str(exc)


@st.cache_data(show_spinner=False, max_entries=8)
def geometry(data, name):
    return parseCadFile(data, name)


def mesh_plot(cad):
    v, f = cad['vertices'], cad['faces']
    fig = go.Figure(go.Mesh3d(x=v[:, 0], y=v[:, 1], z=v[:, 2], i=f[:, 0], j=f[:, 1], k=f[:, 2],
        color='#709965', flatshading=True, lighting=dict(ambient=.55, diffuse=.8, roughness=.5), hoverinfo='skip'))
    fig.update_layout(height=370, paper_bgcolor='#ffffff', margin=dict(l=0,r=0,t=0,b=0),
        scene=dict(bgcolor='#ffffff', aspectmode='data',
                   camera=dict(up=dict(x=0, y=1, z=0), eye=dict(x=1.6, y=1.1, z=1.6)),
        xaxis=dict(title='X · mm',showbackground=False,gridcolor='#edf0e9'),
        yaxis=dict(title='Y · mm',showbackground=False,gridcolor='#edf0e9'),
        zaxis=dict(title='Z · mm',showbackground=False,gridcolor='#edf0e9')))
    return fig


def materials_plot(active):
    rows=list(materialDatabase.items())
    fig=go.Figure(go.Scatter(x=[v['carbonFactorKgCo2ePerKg'] for _,v in rows],
        y=[v['yieldStrengthMpa'] for _,v in rows],mode='markers',
        text=[v['displayName'] for _,v in rows],
        marker=dict(size=[18 if k==active else 11 for k,_ in rows],color=['#244e39' if k==active else '#b6caa3' for k,_ in rows],line=dict(color='white',width=2)),
        hovertemplate='%{text}<br>%{x} kg CO₂e/kg<br>%{y} MPa<extra></extra>'))
    fig.update_layout(height=370,paper_bgcolor='white',plot_bgcolor='white',font=dict(color='#657660'),
        margin=dict(l=20,r=20,t=20,b=20),xaxis=dict(title='Embodied carbon · kg CO₂e/kg',gridcolor='#edf0e9'),
        yaxis=dict(title='Yield strength · MPa',gridcolor='#edf0e9'))
    return fig


with st.sidebar:
    st.markdown('<div class="brand">◈ verdant<span>.</span></div><div class="subtle">Less impact. Better design.</div>',unsafe_allow_html=True)
    st.divider()
    st.markdown('### Design conditions')
    st.caption('Set the baseline for your component.')
    selected=st.selectbox('Baseline material',list(materialDatabase),format_func=lambda k:materialDatabase[k]['displayName'])
    environments={'indoor':'Indoor / controlled','outdoorUv':'Outdoor / UV exposure','marineCorrosive':'Marine / saline','chemicalContact':'Industrial / chemicals'}
    environment=st.selectbox('Operating environment',list(environments),format_func=environments.get)
    st.divider()
    load=st.selectbox('Load type',['compressive','tensile','bending'],format_func=str.capitalize)
    force=st.number_input('Applied force · N',min_value=10.0,max_value=1000000.0,value=8000.0,step=500.0)
    with st.expander('Temperature & mounting',expanded=True):
        a,b=st.columns(2)
        low=a.number_input('Min · °C',value=-10.0,step=5.0)
        high=b.number_input('Max · °C',value=65.0,step=5.0)
        constrained=st.checkbox('Rigidly constrained',help='Mounting prevents free thermal expansion.')
    st.divider()
    regeneration_slot = st.empty()

st.markdown('<div class="eyebrow">COMPONENT DESIGN STUDIO / WORKSPACE</div>',unsafe_allow_html=True)
st.markdown('''<div class="hero"><h1>Better parts. A lighter footprint.</h1><p>Explore your component, compare design ideas, and prepare your review.</p></div>''',unsafe_allow_html=True)

with st.expander('Component library',expanded=True):
    upload=st.file_uploader('Upload a component',type=['step','stp','stl','obj'],help='Mesh coordinates are interpreted as millimeters. STEP units are handled by the importer.')
    st.caption('No file handy? Start with a sample. Uploaded files take priority.')
    cols=st.columns(3)
    for col,(label,name) in zip(cols,[('Try a block','sample_block.stl'),('Try a bracket','sample_bracket.stl'),('Try a cylinder','sample_cylinder.stl')]):
        if col.button(label,width='stretch'):
            st.session_state.sample=name

name=upload.name if upload else st.session_state.sample
if not name:
    a,b,c=st.columns(3)
    for col,title,body in [(a,'01 / Understand','Inspect a true-proportion 3D view and baseline material impact.'),(b,'02 / Explore','Request design ideas and compare material trade-offs.'),(c,'03 / Document','Ask follow-up questions and export an engineering review draft.')]:
        with col,st.container(border=True):
            st.markdown('### '+title); st.write(body)
    st.stop()
if high<low:
    st.error('Maximum temperature must be at least the minimum temperature. Adjust the sidebar to continue.'); st.stop()
try:
    data=upload.getvalue() if upload else (Path(__file__).parent/name).read_bytes()
    cad=geometry(data,name)
    if cad['volumeCm3']<=0:
        st.error('This model has no positive solid volume. Check its face orientation and export a closed solid to continue.'); st.stop()
    params=dict(baselineMaterialKey=selected,loadType=load,appliedForceN=force,tempMinC=low,tempMaxC=high,tempDeltaC=high-low,environmentType=environment,isConstrainedThermal=constrained)
    payload=computePhysicalInvariants(cad,params)
except Exception as exc:
    st.error('We couldn’t read this component. Try exporting it as a closed STEP or STL solid.')
    with st.expander('Error details'): st.code(error_message(exc))
    st.stop()
model_key=hashlib.sha256(data).hexdigest()
context=hashlib.sha256(data+json.dumps(params,sort_keys=True).encode()).hexdigest()
if model_key != st.session_state.activeModel:
    st.session_state.update(activeModel=model_key,aiReport=None,analyzedModel=None,analyzedContext=None,chatMessages=[],ecpReportContent=None)
if context != st.session_state.contextKey:
    st.session_state.update(contextKey=context,chatMessages=[],ecpReportContent=None)
pending_changes = st.session_state.aiReport is not None and st.session_state.analyzedContext != context
pending_message = 'Design conditions have changed. The ideas below still use your previous conditions. Click Regenerate design ideas in the sidebar to apply your changes.'
regenerate=False
if st.session_state.analyzedModel == model_key or st.session_state.aiReport is not None:
    with regeneration_slot.container():
        if pending_changes:
            st.warning('Changes not applied to Design ideas. Click Regenerate design ideas to update them.')
        regenerate=st.button('Regenerate design ideas',type='primary',width='stretch',disabled=not bool(geminiApiKey),key='sidebar_regenerate')
baseline=payload['baselineSummary']
st.markdown(f'<div class="file-name">{html.escape(name)}</div>',unsafe_allow_html=True)
st.caption(('STEP solid' if cad['isBRep'] else 'Polygon mesh')+'  ·  '+ ' × '.join(f'{v:g}' for v in baseline['extentsMm'])+' mm  ·  Current baseline')
metrics=st.columns(4)
for col,label,value in zip(metrics,['Estimated mass','Embodied carbon','Material cost','Model volume'],[f"{baseline['massKg']:g} kg",f"{baseline['embodiedCo2eKg']:g} kg CO₂e",f"${baseline['materialCostUsd']:.2f}",f"{baseline['volumeCm3']:g} cm³"]): col.metric(label,value)
st.write('')
overview,ideas,review=st.tabs(['Overview','Design ideas','Review & export'])
with overview:
    with st.container(border=True):
        st.markdown('### Your component'); st.caption('Drag to orbit · scroll to zoom · double-click to reset')
        st.plotly_chart(mesh_plot(cad),config={'displaylogo':False})
    with st.container(border=True):
        st.markdown('### Material landscape'); st.caption('Your baseline is highlighted. Hover to compare materials.')
        st.plotly_chart(materials_plot(selected),config={'displaylogo':False})
    with st.expander('Calculation assumptions & limitations'):
        st.write('These are screening estimates, not validated structural results. The current engine approximates the cross section from volume and bounding dimensions; its thickness and inertia estimates do not resolve local walls or complex sections. Bending and tension are not modeled separately. Mesh units are assumed to be millimeters, and open meshes use a convex-hull volume estimate.')
        st.write('Use verified geometry, material data, load conditions, and an appropriate engineering analysis before making a design decision.')
    st.info('Next: open Design ideas to request an AI review. Analysis runs only when you ask for it.')
with ideas:
    st.markdown('### Find your next design direction')
    st.caption('Compare opportunities for material substitution, lightweighting, and lower cost. AI suggestions require engineering verification.')
    if pending_changes:
        st.warning(pending_message)
    generate = False
    if st.session_state.aiReport is None:
        generate = st.button('Generate design ideas',type='primary',disabled=not bool(geminiApiKey))
    if generate or regenerate:
        with st.spinner('Reviewing your component and material options…'):
            try:
                result=queryGeminiEngineer(payload)
                if not result or not result.engineeringProposals: raise ValueError('No design proposals returned. Please try again.')
                st.session_state.aiReport=result
                st.session_state.ecpReportContent=None
                st.session_state.analyzedModel=model_key
                st.session_state.analyzedContext=context
                st.rerun()
            except Exception as exc: st.error('Analysis couldn’t finish. '+error_message(exc))
    if not geminiApiKey: st.info('Configure a Gemini key in local Streamlit secrets to enable AI features.')
    report=st.session_state.aiReport
    if report:
        st.markdown('#### Areas to investigate')
        for item in report.identifiedBottlenecks:
            with st.expander(f'{item.severity} · {item.phenomenon}'):
                st.caption(item.affectedRegion); st.write(item.rootCause)
        for i,proposal in enumerate(report.engineeringProposals,1):
            with st.container(border=True):
                st.caption(f'DIRECTION {i:02d} / {proposal.badge}')
                st.markdown('### '+proposal.strategyName); st.write(proposal.recommendedMaterial)
                x,y,z=st.columns(3)
                x.metric('Carbon reduction',f'{proposal.carbonReductionPct:g}%')
                y.metric('Cost change',f'{proposal.costDeltaPct:+g}%')
                z.metric('Proposed mass',f'{proposal.estimatedNewMassKg:g} kg')
                with st.expander('Reasoning & suggested changes'):
                    st.write('**Structural:** '+proposal.structuralFeasibility)
                    st.write('**Thermal:** '+proposal.thermalFeasibility)
                    for change in proposal.cadModifications: st.markdown('- '+change)
    else:
        with st.container(border=True):
            st.markdown('#### Your options will appear here')
            st.write('Add your operating conditions, then generate ideas. You can explore the model freely without triggering extra AI requests.')
with review:
    st.markdown('### A clearer path from idea to review')
    st.caption('Discuss constraints, then capture the conversation in a downloadable draft.')
    with st.container(border=True):
        for message in st.session_state.chatMessages:
            with st.chat_message(message['role']): st.markdown(message['content'])
        if not st.session_state.chatMessages: st.caption('Try: “What should I validate before switching materials?”')
        question=st.chat_input('Ask about materials, mounting, fatigue, or next steps…',disabled=not bool(geminiApiKey))
        if question:
            with st.chat_message('user'): st.write(question)
            with st.spinner('Considering your design context…'):
                try:
                    reply=chatWithEngineer(payload,st.session_state.chatMessages,question)
                    if not reply: raise ValueError('Empty response. Please try again.')
                    st.session_state.chatMessages.extend([dict(role='user',content=question),dict(role='assistant',content=reply)])
                    st.session_state.ecpReportContent=None
                    with st.chat_message('assistant'): st.markdown(reply)
                except Exception as exc: st.error('Couldn’t send your question. '+error_message(exc))
    st.markdown('### Engineering review draft')
    st.caption('Summarizes the current baseline and discussion. Recheck numerical claims before sharing.')
    if st.button('Create review draft',type='primary',disabled=not bool(geminiApiKey)):
        with st.spinner('Preparing your review draft…'):
            try:
                st.session_state.ecpReportContent=generateFormalEcpReport(payload,st.session_state.chatMessages)
            except Exception as exc: st.error('Couldn’t create the draft. '+error_message(exc))
    if st.session_state.ecpReportContent:
        st.download_button('Download review · Markdown',st.session_state.ecpReportContent,file_name='Verdant_Engineering_Review.md',mime='text/markdown')
        with st.expander('Preview review',expanded=True): st.markdown(st.session_state.ecpReportContent)
