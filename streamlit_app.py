"""
streamlit_app.py - Streamlit home page for the Bosch dashboard suite.

This file is the recommended entry point for a single Streamlit Cloud deploy.
The three dashboards are exposed through Streamlit's multi-page navigation by
wrapping the existing page scripts in the `pages/` directory.
"""

import streamlit as st


st.set_page_config(
    page_title="Bosch Dashboard Suite",
    page_icon="🔧",
    layout="wide",
)


st.title("Bosch Dashboard Suite")
st.caption("One GitHub repo, three dashboards, one live Streamlit deployment.")

st.markdown(
    """
    This app brings together the three dashboard experiences in the repository:

    - **Bosch Ticket Dashboard** for operations and ticket visibility
    - **Siemens Supplier Portal** for API-based ticket submission
    - **Continental Supplier Portal** for secure CSV / SFTP-based ticket submission

    Use the Streamlit sidebar to switch between pages after deployment.
    """
)

left, middle, right = st.columns(3)

with left:
    st.subheader("Bosch Ticket Dashboard")
    st.write("Operational view with KPI tiles, filters, and ticket tables.")
    st.code("streamlit run dashboard/app.py", language="bash")

with middle:
    st.subheader("Siemens Supplier Portal")
    st.write("API-based portal for raising support tickets directly with Bosch.")
    st.code("streamlit run dashboard/customer_portal.py --server.port 8502", language="bash")

with right:
    st.subheader("Continental Supplier Portal")
    st.write("File-drop portal that simulates the non-API supplier workflow.")
    st.code("streamlit run dashboard/continental_portal.py --server.port 8503", language="bash")

st.divider()
st.info(
    "For Streamlit Cloud, deploy `streamlit_app.py` as the main app file. "
    "The `pages/` wrappers included in this repo keep the existing dashboards reusable without rewriting them."
)