import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Multi-Channel Ad Performance",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Background color */
    .stApp {
        background-color: #F4F6F9;
    }
    
    /* KPI card styling */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #4f82c8;
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #666;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #1B2A4A;
        margin-bottom: 4px;
    }
    .kpi-sub {
        font-size: 11px;
        color: #999;
    }
    
    /* Chart card styling */
    .chart-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 12px !important;
    }
    
    /* Remove default streamlit padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Load and unify data
@st.cache_data
def load_data():
    con = duckdb.connect()
    unified = con.execute("""
        SELECT 
            date, 'Facebook' as platform, campaign_id, campaign_name,
            impressions, clicks, spend, conversions,
            video_views, engagement_rate, reach,
            ROUND(clicks::FLOAT / NULLIF(impressions,0) * 100, 3) as ctr
        FROM read_csv_auto('01_facebook_ads.csv')
        
        UNION ALL
        
        SELECT 
            date, 'Google' as platform, campaign_id, campaign_name,
            impressions, clicks, cost as spend, conversions,
            0 as video_views, ctr as engagement_rate, 0 as reach,
            ROUND(ctr * 100, 3) as ctr
        FROM read_csv_auto('02_google_ads.csv')
        
        UNION ALL
        
        SELECT 
            date, 'TikTok' as platform, campaign_id, campaign_name,
            impressions, clicks, cost as spend, conversions,
            video_views,
            ROUND((likes+shares+comments)::FLOAT / NULLIF(impressions,0), 4) as engagement_rate,
            0 as reach,
            ROUND(clicks::FLOAT / NULLIF(impressions,0) * 100, 3) as ctr
        FROM read_csv_auto('03_tiktok_ads.csv')
    """).df()
    return unified

df = load_data()

# Header
st.markdown("""
    <div style='background:linear-gradient(135deg,#1B2A4A,#2d4a7a);padding:24px 28px;
    border-radius:14px;margin-bottom:24px;box-shadow:0 4px 15px rgba(27,42,74,0.3)'>
        <h1 style='color:white;margin:0;font-size:26px;font-weight:700'>
            📊 Multi-Channel Ad Performance Dashboard
        </h1>
        <p style='color:#8fa8c8;margin:6px 0 0 0;font-size:13px'>
            January 2024 &nbsp;·&nbsp; Facebook &nbsp;·&nbsp; Google &nbsp;·&nbsp; TikTok
        </p>
    </div>
""", unsafe_allow_html=True)

# KPIs
total_spend = df['spend'].sum()
total_conversions = df['conversions'].sum()
avg_cpa = total_spend / total_conversions
total_impressions = df['impressions'].sum()
total_clicks = df['clicks'].sum()
avg_ctr = total_clicks / total_impressions * 100

k1,k2,k3,k4,k5,k6 = st.columns(6)

kpi_data = [
    (k1, "Total Spend", f"${total_spend:,.0f}", "All platforms", "#4f82c8"),
    (k2, "Total Conversions", f"{total_conversions:,.0f}", "All platforms", "#48a868"),
    (k3, "Avg CPA", f"${avg_cpa:.2f}", "Blended", "#d45a8a"),
    (k4, "Total Impressions", f"{total_impressions/1e6:.1f}M", "All platforms", "#f59e0b"),
    (k5, "Total Clicks", f"{total_clicks/1e3:.0f}K", "All platforms", "#8b5cf6"),
    (k6, "Avg CTR", f"{avg_ctr:.2f}%", "Blended", "#06b6d4"),
]

for col, title, value, sub, color in kpi_data:
    with col:
        st.markdown(f"""
            <div class='kpi-card' style='border-left-color:{color}'>
                <div class='kpi-title'>{title}</div>
                <div class='kpi-value' style='color:{color}'>{value}</div>
                <div class='kpi-sub'>{sub}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Platform colors
colors = {'Facebook':'#4f82c8','Google':'#48a868','TikTok':'#d45a8a'}

# Row 1 - Donut and Bar
c1, c2 = st.columns(2)

with c1:
    plat = df.groupby('platform')['spend'].sum().reset_index()
    fig1 = px.pie(plat, values='spend', names='platform', hole=0.6,
                  title='💰 Spend by Platform',
                  color='platform',
                  color_discrete_map=colors)
    fig1.update_layout(
        height=340,
        paper_bgcolor='white',
        plot_bgcolor='white',
        title_font_size=14,
        title_font_color='#1B2A4A'
    )
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    conv = df.groupby('platform')['conversions'].sum().reset_index()
    fig2 = px.bar(conv, x='conversions', y='platform', orientation='h',
                  title='🎯 Conversions by Platform',
                  color='platform',
                  color_discrete_map=colors,
                  text='conversions')
    fig2.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig2.update_layout(
        height=340,
        showlegend=False,
        paper_bgcolor='white',
        plot_bgcolor='white',
        title_font_size=14,
        title_font_color='#1B2A4A'
    )
    st.plotly_chart(fig2, use_container_width=True)

# Line chart
daily = df.groupby(['date','platform'])['spend'].sum().reset_index()
fig3 = px.line(daily, x='date', y='spend', color='platform',
               title='📈 Daily Spend Trend — January 2024',
               color_discrete_map=colors)
fig3.update_traces(line_width=2)
fig3.update_layout(
    height=300,
    paper_bgcolor='white',
    plot_bgcolor='white',
    title_font_size=14,
    title_font_color='#1B2A4A',
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor='#f0f0f0')
)
st.plotly_chart(fig3, use_container_width=True)

# CPA and CTR
c3, c4 = st.columns(2)

with c3:
    cpa = df.groupby('platform').apply(
        lambda x: x['spend'].sum() / x['conversions'].sum()
    ).reset_index()
    cpa.columns = ['platform', 'cpa']
    fig4 = px.bar(cpa, x='platform', y='cpa',
                  title='💡 CPA by Platform',
                  color='platform',
                  color_discrete_map=colors,
                  text='cpa')
    fig4.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
    fig4.update_layout(
        height=320,
        showlegend=False,
        paper_bgcolor='white',
        plot_bgcolor='white',
        title_font_size=14,
        title_font_color='#1B2A4A'
    )
    st.plotly_chart(fig4, use_container_width=True)

with c4:
    ctr = df.groupby('platform').apply(
        lambda x: x['clicks'].sum() / x['impressions'].sum() * 100
    ).reset_index()
    ctr.columns = ['platform', 'ctr']
    fig5 = px.bar(ctr, x='ctr', y='platform', orientation='h',
                  title='📊 CTR by Platform (%)',
                  color='platform',
                  color_discrete_map=colors,
                  text='ctr')
    fig5.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig5.update_layout(
        height=320,
        showlegend=False,
        paper_bgcolor='white',
        plot_bgcolor='white',
        title_font_size=14,
        title_font_color='#1B2A4A'
    )
    st.plotly_chart(fig5, use_container_width=True)

# Campaign table
st.markdown("""
    <div style='background:white;border-radius:12px;padding:16px 20px;
    box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-top:8px'>
        <h3 style='color:#1B2A4A;margin:0 0 12px 0;font-size:16px'>
            📋 Campaign Breakdown
        </h3>
    </div>
""", unsafe_allow_html=True)

camp = df.groupby(['platform','campaign_name']).agg(
    Spend=('spend','sum'),
    Conversions=('conversions','sum'),
    Clicks=('clicks','sum'),
    Impressions=('impressions','sum')
).reset_index()
camp['CPA'] = (camp['Spend'] / camp['Conversions']).round(2)
camp['CTR'] = (camp['Clicks'] / camp['Impressions'] * 100).round(2)
camp = camp.sort_values('CPA', ascending=True)
camp['Spend'] = camp['Spend'].apply(lambda x: f"${x:,.0f}")
camp['CPA'] = camp['CPA'].apply(lambda x: f"${x:.2f}")
camp['CTR'] = camp['CTR'].apply(lambda x: f"{x:.2f}%")
camp['Conversions'] = camp['Conversions'].apply(lambda x: f"{x:,.0f}")
camp.columns = ['Platform','Campaign','Spend','Conversions',
                'Clicks','Impressions','CPA','CTR']

# Add color styling to table
def color_platform(val):
    colors = {
        'Facebook': 'background-color: #dbeafe; color: #1e40af; font-weight:600',
        'Google': 'background-color: #dcfce7; color: #166534; font-weight:600',
        'TikTok': 'background-color: #fce7f3; color: #9d174d; font-weight:600'
    }
    return colors.get(val, '')

def color_cpa(val):
    try:
        num = float(val.replace('$',''))
        if num <= 8:
            return 'color: #16a34a; font-weight:700'
        elif num <= 15:
            return 'color: #d97706; font-weight:700'
        else:
            return 'color: #dc2626; font-weight:700'
    except:
        return ''

def color_ctr(val):
    try:
        num = float(val.replace('%',''))
        if num >= 3:
            return 'color: #16a34a; font-weight:700'
        elif num >= 1.5:
            return 'color: #d97706; font-weight:700'
        else:
            return 'color: #dc2626; font-weight:700'
    except:
        return ''

styled = camp[['Campaign','Platform','Spend','Conversions','CPA','CTR']].style\
    .map(color_platform, subset=['Platform'])\
    .map(color_cpa, subset=['CPA'])\
    .map(color_ctr, subset=['CTR'])\
    .set_properties(**{
        'font-size': '13px',
        'padding': '10px 14px',
        'border-bottom': '1px solid #f0f0f0'
    })\
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', '#1B2A4A'),
            ('color', 'white'),
            ('font-size', '11px'),
            ('text-transform', 'uppercase'),
            ('letter-spacing', '0.05em'),
            ('padding', '12px 14px'),
            ('font-weight', '600')
        ]},
        {'selector': 'tr:hover td', 'props': [
            ('background-color', '#f8fafc')
        ]}
    ])

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True
)
# Footer
st.markdown("""
    <div style='text-align:center;padding:20px;color:#999;font-size:12px;margin-top:20px'>
        Multi-Channel Ad Performance Dashboard · January 2024 · 
        Facebook · Google · TikTok
    </div>
""", unsafe_allow_html=True)