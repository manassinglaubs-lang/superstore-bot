import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from schema_utils import get_schema_description
from sql_generator import generate_sql
from query_executor import execute_query
from answer_formatter import format_answer

st.set_page_config(page_title="Superstore Analytics Bot", page_icon="📊", layout="wide")

# ---------- Session state ----------
if "page" not in st.session_state:
    st.session_state.page = "💬 AI Chat"
if "schema" not in st.session_state:
    st.session_state.schema = get_schema_description()
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "saved_queries" not in st.session_state:
    st.session_state.saved_queries = {}

# ---------- Dark theme palette (Navy & Amber) ----------
BG, CARD, PRIMARY, SECONDARY, TEXT = "#0B1220", "#131C2E", "#60A5FA", "#FBBF24", "#F3F4F6"
MUTED = "#94A3B8"
BORDER = "rgba(255,255,255,0.08)"
BORDER_STRONG = "rgba(255,255,255,0.18)"
ON_PRIMARY = "#0B1220"      # dark text on light-blue buttons/tags
CODE_BG = "#0F172A"
PLOTLY_TEMPLATE = "plotly_dark"

SUCCESS, WARNING, DANGER = "#4ADE80", "#FBBF24", "#F87171"   # light tones: readable on dark
CURRENCY = "$"  # change to "₹" only if your actual data is in INR

# ---------- CSS ----------
st.markdown(f"""
<style>
    /* ===== Base surfaces (page, header, bottom chat bar) ===== */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background-color: {BG} !important; color: {TEXT};
    }}
    header[data-testid="stHeader"] {{ background-color: {BG} !important; }}
    header[data-testid="stHeader"] * {{ color: {MUTED} !important; }}
    [data-testid="stAppDeployButton"], .stDeployButton {{ display: none !important; }}
    [data-testid="stBottom"], [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {{ background-color: {BG} !important; }}

    /* ===== Text ===== */
    h1, h2, h3, h4, h5, h6 {{ color: {TEXT} !important; }}
    .stMarkdown p, .stMarkdown li, label, [data-testid="stWidgetLabel"] p {{ color: {TEXT} !important; }}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; }}
    a {{ color: {SECONDARY} !important; }}

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {{ background-color: {CARD} !important; border-right: 1px solid {BORDER_STRONG}; }}
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {{ color: {TEXT} !important; }}
    [data-testid="stSidebarCollapseButton"] * , [data-testid="stSidebarCollapsedControl"] * {{ color: {MUTED} !important; }}
    section[data-testid="stSidebar"] .stButton button {{ background-color: {BG} !important; }}

    .app-title {{ font-size: 1.4rem; font-weight: 700; color: {TEXT}; margin-bottom: 0; }}
    .app-subtitle {{ font-size: 0.8rem; color: {MUTED}; margin-bottom: 1rem; }}
    .hero-title {{ font-size: 1.7rem; font-weight: 700; color: {TEXT}; margin-bottom: 0.1rem; }}
    .hero-subtitle {{ font-size: 0.9rem; color: {MUTED}; margin-bottom: 1.3rem; }}
    .nav-label {{ font-size: 0.7rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; margin: 0.8rem 0 0.3rem 0; }}

    /* ===== KPI cards & metrics ===== */
    .kpi-card {{ background: {CARD}; border: 1px solid {BORDER_STRONG}; border-left: 3px solid {PRIMARY}; border-radius: 10px; padding: 1.1rem 1.2rem; }}
    .kpi-label {{ font-size: 0.72rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-bottom: 0.3rem; }}
    .kpi-value {{ font-size: 1.6rem; font-weight: 700; color: {TEXT}; }}
    [data-testid="stMetric"] {{ background: {CARD}; border: 1px solid {BORDER_STRONG}; border-radius: 10px; padding: 0.8rem 1rem; }}
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color: {MUTED} !important; }}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {{ color: {TEXT} !important; }}

    /* ===== Chat ===== */
    div[data-testid="stChatMessage"] {{ background: {CARD}; border: 1px solid {BORDER_STRONG}; border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.5rem; }}
    div[data-testid="stChatMessage"] p {{ color: {TEXT} !important; }}
    [data-testid="stChatInput"], [data-testid="stChatInput"] > div {{ background-color: {CARD} !important; border-color: {BORDER_STRONG} !important; }}
    [data-testid="stChatInput"] textarea {{ background-color: transparent !important; color: {TEXT} !important; caret-color: {PRIMARY}; }}
    [data-testid="stChatInput"] textarea::placeholder {{ color: {MUTED} !important; opacity: 1; }}
    [data-testid="stChatInput"] button {{ background-color: {PRIMARY} !important; }}
    [data-testid="stChatInput"] button svg {{ color: {ON_PRIMARY} !important; fill: {ON_PRIMARY} !important; }}

    /* ===== Buttons ===== */
    .stButton button, .stDownloadButton button {{ border-radius: 8px; border: 1px solid {BORDER_STRONG}; background-color: {CARD}; color: {TEXT} !important; font-size: 0.85rem; padding: 0.5rem 0.8rem; }}
    .stButton button p, .stDownloadButton button p {{ color: inherit !important; }}
    .stButton button:hover, .stDownloadButton button:hover {{ border-color: {PRIMARY}; color: {PRIMARY} !important; }}
    button[kind="primary"], button[kind="primaryFormSubmit"], .stFormSubmitButton button {{ background-color: {PRIMARY} !important; color: {ON_PRIMARY} !important; border: none !important; font-weight: 600; }}
    button[kind="primary"] p, .stFormSubmitButton button p {{ color: {ON_PRIMARY} !important; }}

    /* ===== Inputs (text, select, multiselect, date) ===== */
    input, textarea, [data-baseweb="input"], [data-baseweb="input"] > div,
    [data-baseweb="select"] > div, [data-baseweb="textarea"] {{ background-color: {CARD} !important; color: {TEXT} !important; border-color: {BORDER_STRONG} !important; }}
    input::placeholder, textarea::placeholder {{ color: {MUTED} !important; opacity: 1; }}
    [data-baseweb="select"] span, [data-baseweb="select"] svg {{ color: {TEXT} !important; fill: {TEXT} !important; }}
    [data-baseweb="tag"] {{ background-color: {PRIMARY} !important; }}
    [data-baseweb="tag"], [data-baseweb="tag"] span, [data-baseweb="tag"] svg {{ color: {ON_PRIMARY} !important; fill: {ON_PRIMARY} !important; }}

    /* dropdown / calendar popovers (rendered outside .stApp) */
    [data-baseweb="popover"], [data-baseweb="popover"] > div, [data-baseweb="menu"], [data-baseweb="menu"] ul,
    [data-baseweb="calendar"], [data-baseweb="datepicker"] {{ background-color: {CARD} !important; color: {TEXT} !important; }}
    [data-baseweb="popover"] li, [data-baseweb="menu"] li, [data-baseweb="popover"] span, [data-baseweb="calendar"] * {{ color: {TEXT} !important; }}
    [data-baseweb="menu"] li:hover, [role="option"]:hover, [aria-selected="true"][role="option"] {{ background-color: {BG} !important; }}

    /* ===== Expanders, alerts, code, tables ===== */
    [data-testid="stExpander"] details {{ background-color: {CARD}; border: 1px solid {BORDER_STRONG}; border-radius: 8px; }}
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span {{ color: {TEXT} !important; }}
    [data-testid="stAlert"] p, [data-testid="stAlert"] div {{ color: {TEXT} !important; }}
    [data-testid="stCode"], [data-testid="stCode"] pre, pre {{ background-color: {CODE_BG} !important; }}
    [data-testid="stCode"] code {{ color: #E2E8F0; }}
    div[data-testid="stDataFrame"] {{ border-radius: 8px; overflow: hidden; border: 1px solid {BORDER_STRONG}; }}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers: formatting ----------
def format_currency_compact(value):
    if value is None:
        return f"{CURRENCY}0"
    value = float(value)
    if abs(value) >= 1e6:
        return f"{CURRENCY}{value/1e6:,.2f}M"
    elif abs(value) >= 1e3:
        return f"{CURRENCY}{value/1e3:,.1f}K"
    return f"{CURRENCY}{value:,.0f}"

# ---------- Helpers: Plotly styling ----------
def style_fig(fig, title=None):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=12),
        title=title,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
    )
    fig.update_xaxes(title_font=dict(color=TEXT), tickfont=dict(color=TEXT), gridcolor=BORDER, linecolor=MUTED)
    fig.update_yaxes(title_font=dict(color=TEXT), tickfont=dict(color=TEXT), gridcolor=BORDER, linecolor=MUTED)
    return fig

def make_bar(df, x_col, y_col, title=None, horizontal=False):
    if horizontal:
        fig = px.bar(df, x=y_col, y=x_col, orientation="h", color_discrete_sequence=[PRIMARY])
    else:
        fig = px.bar(df, x=x_col, y=y_col, color_discrete_sequence=[PRIMARY])
    return style_fig(fig, title)

def make_line(df, x_col, y_col, title=None):
    fig = px.line(df, x=x_col, y=y_col, markers=True, color_discrete_sequence=[PRIMARY])
    return style_fig(fig, title)

# ---------- Helpers: KPI cards ----------
def kpi_card_with_delta(label, value_display, delta_pct=None):
    if delta_pct is None:
        delta_html = ""
    else:
        up = delta_pct >= 0
        color = SUCCESS if up else DANGER
        arrow = "↑" if up else "↓"
        delta_html = f'<div style="color:{color};font-size:0.8rem;font-weight:600;margin-top:0.2rem;">{arrow} {abs(delta_pct)}%</div>'
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value_display}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)

def get_kpis_with_deltas(where_clause=""):
    join_clause = """
        FROM orders o
        JOIN order_details od ON o.Order_Key = od.Order_Key
        JOIN products p ON od.Product_ID = p.Product_ID
    """

    _, r = execute_query(f"SELECT ROUND(SUM(od.Sales),2), ROUND(SUM(od.Profit),2) {join_clause} {where_clause}")
    sales_cur = float(r[0][0] or 0)
    profit_cur = float(r[0][1] or 0)

    _, r = execute_query(f"SELECT COUNT(DISTINCT o.Order_ID) {join_clause} {where_clause}")
    orders_cur = r[0][0] or 0

    _, r = execute_query(f"SELECT COUNT(DISTINCT o.Customer_ID) {join_clause} {where_clause}")
    customers_cur = r[0][0] or 0

    def period_sum(col, month_offset):
        cond = where_clause if where_clause else "WHERE 1=1"
        _, r = execute_query(f"""
            SELECT ROUND(SUM(od.{col}),2) {join_clause}
            {cond} AND strftime('%Y-%m', o.Order_Date) =
                strftime('%Y-%m', (SELECT MAX(Order_Date) FROM orders), 'start of month', '-{month_offset} months')
        """)
        return float(r[0][0] or 0)

    def pct_change(cur, prev):
        if not prev:
            return None
        return round(((cur - prev) / prev) * 100, 1)

    sales_prev = period_sum("Sales", 1)
    profit_prev = period_sum("Profit", 1)
    sales_this_month = period_sum("Sales", 0)
    profit_this_month = period_sum("Profit", 0)

    return {
        "sales": (sales_cur, pct_change(sales_this_month, sales_prev)),
        "profit": (profit_cur, pct_change(profit_this_month, profit_prev)),
        "orders": (orders_cur, None),
        "customers": (customers_cur, None),
    }

def render_kpis(where_clause=""):
    try:
        k = get_kpis_with_deltas(where_clause)
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card_with_delta("Total Sales", format_currency_compact(k["sales"][0]), k["sales"][1])
        with c2: kpi_card_with_delta("Total Profit", format_currency_compact(k["profit"][0]), k["profit"][1])
        with c3: kpi_card_with_delta("Orders", f"{k['orders'][0]:,}")
        with c4: kpi_card_with_delta("Customers", f"{k['customers'][0]:,}")
        st.markdown("<br>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load KPIs: {e}")

def detect_chart_columns(df):
    if df.shape[0] < 2 or df.shape[0] > 30:
        return None
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude="number").columns.tolist()
    if numeric_cols and non_numeric_cols:
        return non_numeric_cols[0], numeric_cols[0]
    return None

def render_result_chart(df, chart_cols, key=None):
    cat_col, num_col = chart_cols
    fig = make_bar(df, cat_col, num_col, horizontal=(df.shape[0] > 8))
    st.plotly_chart(fig, use_container_width=True, key=key)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="app-title">📊 Superstore Analytics Bot</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">AI-powered conversational analytics</div>', unsafe_allow_html=True)

    st.markdown('<div class="nav-label">Navigate</div>', unsafe_allow_html=True)
    pages = ["📊 Dashboard", "💬 AI Chat", "🧮 What-If Analysis", "🕘 Query History", "⭐ Saved Queries", "⚙ Settings"]
    st.session_state.page = st.radio("Navigate", pages,
                                       index=pages.index(st.session_state.page) if st.session_state.page in pages else 1,
                                       label_visibility="collapsed")

    st.markdown('<div class="nav-label">Try Asking</div>', unsafe_allow_html=True)
    examples = [
        "Total sales revenue overall",
        "Top 5 customers by profit",
        "Total profit by region",
        "Monthly sales trend in 2017",
        "Which products have negative profit?",
        "Average discount by category",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.pending_question = ex
            st.session_state.page = "💬 AI Chat"
            st.rerun()

    st.markdown('<div class="nav-label">Display Options</div>', unsafe_allow_html=True)
    show_sql = st.toggle("Show generated SQL", value=True)
    show_chart = st.toggle("Auto-generate charts", value=True)

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# ============================================================
# PAGE: DASHBOARD
# ============================================================
if st.session_state.page == "📊 Dashboard":
    st.markdown('<div class="hero-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Key performance indicators from your sales data.</div>', unsafe_allow_html=True)

    # ---------- Filters ----------
    with st.expander("🔍 Filters", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        _, date_range = execute_query("SELECT MIN(Order_Date), MAX(Order_Date) FROM orders")

        def _to_date(val):
            if isinstance(val, datetime.date):
                return val
            if isinstance(val, str):
                return datetime.datetime.strptime(val, "%Y-%m-%d").date()
            return val

        min_date, max_date = _to_date(date_range[0][0]), _to_date(date_range[0][1])
        with fc1:
            date_filter = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        with fc2:
            _, regions = execute_query("SELECT DISTINCT Region FROM orders")
            region_filter = st.multiselect("Region", [r[0] for r in regions])
        with fc3:
            _, categories = execute_query("SELECT DISTINCT Category FROM products")
            category_filter = st.multiselect("Category", [c[0] for c in categories])
        with fc4:
            _, products = execute_query("SELECT DISTINCT Product_Name FROM products LIMIT 200")
            product_filter = st.multiselect("Product", [p[0] for p in products])

    def _esc(v):
        return str(v).replace("'", "''")

    conditions = []
    if isinstance(date_filter, tuple) and len(date_filter) == 2:
        conditions.append(f"o.Order_Date BETWEEN '{date_filter[0]}' AND '{date_filter[1]}'")
    if region_filter:
        vals = ",".join(f"'{_esc(r)}'" for r in region_filter)
        conditions.append(f"o.Region IN ({vals})")
    if category_filter:
        vals = ",".join(f"'{_esc(c)}'" for c in category_filter)
        conditions.append(f"p.Category IN ({vals})")
    if product_filter:
        vals = ",".join(f"'{_esc(p)}'" for p in product_filter)
        conditions.append(f"p.Product_Name IN ({vals})")
    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    render_kpis(where_clause)

    col1, col2 = st.columns(2)
    with col1:
        try:
            cols, rows = execute_query(f"""
                SELECT o.Region, ROUND(SUM(od.Sales),2) AS Sales
                FROM orders o
                JOIN order_details od ON o.Order_Key = od.Order_Key
                JOIN products p ON od.Product_ID = p.Product_ID
                {where_clause}
                GROUP BY o.Region ORDER BY Sales DESC
            """)
            if rows:
                df = pd.DataFrame(rows, columns=cols)
                st.plotly_chart(make_bar(df, cols[0], cols[1], "Sales by Region"), use_container_width=True, key="dash_region")
        except Exception as e:
            st.warning(f"Could not load chart: {e}")

    with col2:
        try:
            cols, rows = execute_query(f"""
                SELECT strftime('%Y-%m', o.Order_Date) AS Month,
                       ROUND(SUM(od.Sales),2) AS Sales, ROUND(SUM(od.Profit),2) AS Profit
                FROM orders o
                JOIN order_details od ON o.Order_Key = od.Order_Key
                JOIN products p ON od.Product_ID = p.Product_ID
                {where_clause}
                GROUP BY Month ORDER BY Month
            """)
            if rows:
                df = pd.DataFrame(rows, columns=cols)
                df_melted = df.melt(id_vars=cols[0], value_vars=[cols[1], cols[2]],
                                     var_name="Metric", value_name="Amount")
                fig = px.line(df_melted, x=cols[0], y="Amount", color="Metric", markers=True,
                              color_discrete_sequence=[PRIMARY, SECONDARY])
                st.plotly_chart(style_fig(fig, "Monthly Sales & Profit Trend"), use_container_width=True, key="dash_trend")
        except Exception as e:
            st.warning(f"Could not load chart: {e}")

    col3, col4 = st.columns(2)
    with col3:
        try:
            cols, rows = execute_query(f"""
                SELECT p.Category, ROUND(SUM(od.Sales),2) AS Sales, ROUND(SUM(od.Profit),2) AS Profit
                FROM order_details od
                JOIN products p ON od.Product_ID = p.Product_ID
                JOIN orders o ON od.Order_Key = o.Order_Key
                {where_clause}
                GROUP BY p.Category ORDER BY Sales DESC
            """)
            if rows:
                df = pd.DataFrame(rows, columns=cols)
                df_melted = df.melt(id_vars=cols[0], value_vars=[cols[1], cols[2]],
                                     var_name="Metric", value_name="Amount")
                fig = px.bar(df_melted, x=cols[0], y="Amount", color="Metric",
                             barmode="group", color_discrete_sequence=[PRIMARY, SECONDARY])
                st.plotly_chart(style_fig(fig, "Sales & Profit by Category"), use_container_width=True, key="dash_cat")
        except Exception as e:
            st.warning(f"Could not load chart: {e}")

    with col4:
        try:
            cols, rows = execute_query(f"""
                SELECT p.Product_Name, ROUND(SUM(od.Sales),2) AS Sales
                FROM order_details od
                JOIN products p ON od.Product_ID = p.Product_ID
                JOIN orders o ON od.Order_Key = o.Order_Key
                {where_clause}
                GROUP BY p.Product_Name ORDER BY Sales DESC LIMIT 10
            """)
            if rows:
                df = pd.DataFrame(rows, columns=cols).sort_values(cols[1])
                st.plotly_chart(make_bar(df, cols[0], cols[1], "Top 10 Products by Sales", horizontal=True), use_container_width=True, key="dash_top10")
        except Exception as e:
            st.warning(f"Could not load chart: {e}")

    try:
        cols, rows = execute_query(f"""
            SELECT c.Customer_Name, ROUND(SUM(od.Sales),2) AS Sales
            FROM order_details od
            JOIN orders o ON od.Order_Key = o.Order_Key
            JOIN customers c ON o.Customer_ID = c.Customer_ID
            JOIN products p ON od.Product_ID = p.Product_ID
            {where_clause}
            GROUP BY c.Customer_Name ORDER BY Sales DESC LIMIT 10
        """)
        if rows:
            df = pd.DataFrame(rows, columns=cols).sort_values(cols[1])
            st.plotly_chart(make_bar(df, cols[0], cols[1], "Top 10 Customers by Sales", horizontal=True), use_container_width=True, key="dash_customers")
    except Exception as e:
        st.warning(f"Could not load chart: {e}")

# ============================================================
# PAGE: AI CHAT
# ============================================================
elif st.session_state.page == "💬 AI Chat":
    st.markdown('<div class="hero-title">Ask Your Sales Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Ask a question in plain English — I\'ll write the SQL, run it, and explain the results.</div>', unsafe_allow_html=True)

    for i, msg in enumerate(st.session_state.history):
        with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            if msg.get("sql") and show_sql:
                with st.expander("🔎 View SQL query"):
                    st.code(msg["sql"], language="sql")
            if msg.get("df") is not None:
                st.dataframe(msg["df"], use_container_width=True)
                csv = msg["df"].to_csv(index=False).encode("utf-8")
                st.download_button("⬇ Download CSV", csv, "result.csv", "text/csv", key=f"dl_{i}")
                if show_chart and msg.get("chart_cols"):
                    render_result_chart(msg["df"], msg["chart_cols"], key=f"chart_hist_{i}")

    question = st.chat_input("Ask a question about the sales data...")
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None

    if question:
        st.session_state.history.append({"role": "user", "content": question})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyzing your question..."):
                try:
                    sql = generate_sql(question, st.session_state.schema)
                    if show_sql:
                        with st.expander("🔎 View SQL query"):
                            st.code(sql, language="sql")

                    columns, rows = execute_query(sql)
                    df = pd.DataFrame(rows, columns=columns)

                    if df.empty:
                        answer = "I ran the query, but no matching data was found. Try rephrasing, or double-check names/categories."
                        st.markdown(answer)
                        st.session_state.history.append({"role": "assistant", "content": answer, "sql": sql, "df": None})
                    else:
                        answer = format_answer(question, columns, rows)
                        st.markdown(answer)
                        st.dataframe(df, use_container_width=True)

                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button("⬇ Download CSV", csv, "result.csv", "text/csv", key="dl_new")

                        chart_cols = detect_chart_columns(df) if show_chart else None
                        if chart_cols:
                            render_result_chart(df, chart_cols, key="chart_new")

                        st.session_state.history.append({
                            "role": "assistant", "content": answer, "sql": sql,
                            "df": df, "chart_cols": chart_cols
                        })

                except ValueError as ve:
                    msg = f"⚠️ {ve}"
                    st.warning(msg)
                    st.session_state.history.append({"role": "assistant", "content": msg})
                except Exception as e:
                    msg = "I couldn't process that question. Try rephrasing it more simply."
                    st.error(msg)
                    with st.expander("Technical details"):
                        st.code(str(e))
                    st.session_state.history.append({"role": "assistant", "content": msg})

# ============================================================
# PAGE: WHAT-IF ANALYSIS
# ============================================================
elif st.session_state.page == "🧮 What-If Analysis":
    st.markdown('<div class="hero-title">What-If Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Model projected outcomes by adjusting key assumptions.</div>', unsafe_allow_html=True)

    _, r = execute_query("SELECT ROUND(SUM(Sales),2), ROUND(SUM(Profit),2) FROM order_details")
    current_sales = float(r[0][0] or 0)
    current_profit = float(r[0][1] or 0)
    current_margin = (current_profit / current_sales * 100) if current_sales else 0

    st.markdown("#### Current Baseline")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Current Sales", format_currency_compact(current_sales))
    with c2: st.metric("Current Profit", format_currency_compact(current_profit))
    with c3: st.metric("Current Margin", f"{current_margin:.1f}%")

    st.markdown("#### Assumptions")
    c1, c2 = st.columns(2)
    with c1:
        sales_growth = st.slider("Sales Growth (%)", -50, 100, 10)
        discount_change = st.slider("Discount Change (percentage points)", -10, 10, 0)
    with c2:
        cost_growth = st.slider("Cost Growth (%)", -50, 100, 5)
        margin_target = st.slider("Additional Margin Adjustment (pp)", -20, 20, 0)

    projected_sales = current_sales * (1 + sales_growth / 100)
    current_cost = current_sales - current_profit
    projected_cost = current_cost * (1 + cost_growth / 100)
    projected_profit = projected_sales - projected_cost
    projected_profit -= projected_sales * (discount_change / 100)
    projected_margin = (projected_profit / projected_sales * 100) if projected_sales else 0
    projected_margin += margin_target

    st.markdown("#### Projected Outcome")
    c1, c2, c3 = st.columns(3)
    with c1:
        delta = ((projected_sales - current_sales) / current_sales * 100) if current_sales else 0
        st.metric("Projected Sales", format_currency_compact(projected_sales), f"{delta:+.1f}%")
    with c2:
        delta = ((projected_profit - current_profit) / current_profit * 100) if current_profit else 0
        st.metric("Projected Profit", format_currency_compact(projected_profit), f"{delta:+.1f}%")
    with c3:
        delta = projected_margin - current_margin
        st.metric("Projected Margin", f"{projected_margin:.1f}%", f"{delta:+.1f}pp")

    st.caption("⚠️ This is a simplified linear projection based on your assumptions — treat it as an estimate, not a forecast model.")

# ============================================================
# PAGE: QUERY HISTORY
# ============================================================
elif st.session_state.page == "🕘 Query History":
    st.markdown('<div class="hero-title">Query History</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Revisit and re-run past questions.</div>', unsafe_allow_html=True)

    user_qs = [m["content"] for m in st.session_state.history if m["role"] == "user"]
    if not user_qs:
        st.info("No queries yet — ask something in the AI Chat tab.")
    for i, q in enumerate(reversed(user_qs)):
        col1, col2 = st.columns([5, 1])
        col1.write(q)
        if col2.button("Run again", key=f"rerun_{i}"):
            st.session_state.pending_question = q
            st.session_state.page = "💬 AI Chat"
            st.rerun()

# ============================================================
# PAGE: SAVED QUERIES
# ============================================================
elif st.session_state.page == "⭐ Saved Queries":
    st.markdown('<div class="hero-title">Saved Queries</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Save frequently used questions for quick access.</div>', unsafe_allow_html=True)

    with st.form("save_form"):
        name = st.text_input("Name")
        question_text = st.text_input("Question")
        if st.form_submit_button("Save") and name and question_text:
            st.session_state.saved_queries[name] = question_text
            st.success(f"Saved '{name}'")

    for name, q in list(st.session_state.saved_queries.items()):
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"**{name}** — {q}")
        if col2.button("Run", key=f"run_{name}"):
            st.session_state.pending_question = q
            st.session_state.page = "💬 AI Chat"
            st.rerun()
        if col3.button("Delete", key=f"del_{name}"):
            del st.session_state.saved_queries[name]
            st.rerun()

# ============================================================
# PAGE: SETTINGS
# ============================================================
elif st.session_state.page == "⚙ Settings":
    st.markdown('<div class="hero-title">Settings</div>', unsafe_allow_html=True)
    with st.expander("📋 Database schema", expanded=True):
        st.text(st.session_state.schema)