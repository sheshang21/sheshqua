import streamlit as st
import pandas as pd
from scraper import scrape_all_pages, verify_login
import time
import os

def show_quarterly_screener():
    """Main function to show the quarterly results screener"""
    
    st.header("📊 Quarterly Results Screener")
    st.markdown("Scrape and analyze quarterly results from Screener.in")
    st.markdown("---")
    
    # Initialize session state
    if 'screener_data' not in st.session_state:
        st.session_state.screener_data = None
    if 'screener_login_verified' not in st.session_state:
        st.session_state.screener_login_verified = False
    
    # Check for cookies file
    if not os.path.exists('screener_cookies.pkl'):
        st.error("🔐 **Cookie File Missing!**")
        st.markdown("""
        This feature requires pre-saved cookies from Screener.in.
        
        **Setup Instructions:**
        1. Run `local_login.py` locally to generate cookies
        2. Upload `screener_cookies.pkl` to the repository
        3. Redeploy the app
        """)
        
        uploaded_cookies = st.file_uploader("Upload screener_cookies.pkl", type=['pkl'])
        if uploaded_cookies:
            with open('screener_cookies.pkl', 'wb') as f:
                f.write(uploaded_cookies.read())
            st.success("✅ Cookies uploaded!")
            if st.button("🔄 Verify Login"):
                st.rerun()
        return
    
    # Verify login
    if not st.session_state.screener_login_verified:
        with st.spinner("🔐 Verifying Screener.in login..."):
            if verify_login():
                st.success("✅ Login verified! Ready to scrape.")
                st.session_state.screener_login_verified = True
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Login failed. Cookies may be expired.")
                st.markdown("""
                **Solutions:**
                1. Re-run `local_login.py` locally to refresh cookies
                2. Upload new `screener_cookies.pkl` file
                """)
                
                uploaded_cookies = st.file_uploader("Upload fresh screener_cookies.pkl", type=['pkl'], key="refresh_cookies")
                if uploaded_cookies:
                    with open('screener_cookies.pkl', 'wb') as f:
                        f.write(uploaded_cookies.read())
                    st.success("✅ New cookies uploaded!")
                    if st.button("🔄 Retry Verification"):
                        st.rerun()
                return
    
    st.markdown("---")
    
    # Page selection
    st.subheader("📄 Select Pages to Scrape")
    col1, col2 = st.columns(2)
    
    with col1:
        fetch_mode = st.radio(
            "Fetch Mode",
            ["All Pages (1-80)", "Custom Pages"],
            horizontal=True,
            key="screener_fetch_mode"
        )
    
    if fetch_mode == "Custom Pages":
        col3, col4 = st.columns(2)
        with col3:
            page_input = st.text_area(
                "Enter page numbers (comma-separated or ranges)",
                placeholder="e.g., 1,5,10-15,20,25-30,80",
                height=100,
                key="screener_page_input"
            )
        with col4:
            st.info("""
            **Examples:**
            - Single: `1,5,10`
            - Range: `1-10`
            - Mixed: `1,5-10,15,20-25`
            """)
    
    # Performance settings
    st.subheader("⚙️ Performance Settings")
    col_perf1, col_perf2 = st.columns(2)
    
    with col_perf1:
        num_workers = st.slider(
            "🔄 Parallel Workers",
            min_value=1,
            max_value=3,
            value=1,
            help="Limited to 3 workers on Streamlit Cloud. Use 1-2 for stability.",
            key="screener_workers"
        )
        if num_workers > 1:
            st.caption(f"⚡ {num_workers}x faster with {num_workers} parallel workers")
    
    with col_perf2:
        delay = st.slider(
            "⏱️ Delay Between Pages (seconds)",
            min_value=3,
            max_value=10,
            value=5,
            help="Recommended: 5-8s for Streamlit Cloud stability",
            key="screener_delay"
        )
    
    # Fetch button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Fetch Quarterly Results", type="primary", use_container_width=True, key="screener_fetch"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Parse pages
            if fetch_mode == "All Pages (1-80)":
                pages_to_fetch = list(range(1, 81))
            else:
                try:
                    pages_to_fetch = []
                    parts = page_input.replace(' ', '').split(',')
                    for part in parts:
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            pages_to_fetch.extend(range(start, end + 1))
                        else:
                            pages_to_fetch.append(int(part))
                    pages_to_fetch = sorted(list(set(pages_to_fetch)))
                except:
                    st.error("Invalid page format! Use: 1,5,10-15,20")
                    return
            
            def update_progress(current_idx, total):
                progress = current_idx / total
                progress_bar.progress(progress)
                status_text.text(f"Scraping page {current_idx}/{total}...")
            
            try:
                with st.spinner("Fetching data from Screener.in..."):
                    df = scrape_all_pages(
                        pages_list=pages_to_fetch, 
                        progress_callback=update_progress,
                        num_workers=num_workers,
                        delay=delay
                    )
                    st.session_state.screener_data = df
                    progress_bar.progress(1.0)
                    status_text.text(f"✅ Successfully fetched {len(df)} companies from {len(pages_to_fetch)} pages!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Error fetching data: {e}")
                st.info("Try reducing workers to 1 or increasing delay")
    
    # Display data
    if st.session_state.screener_data is not None and len(st.session_state.screener_data) > 0:
        df = st.session_state.screener_data.copy()
        
        if 'Price' not in df.columns or len(df) == 0:
            st.error("No data fetched. Please try again with different pages.")
            return
        
        st.markdown("---")
        st.subheader("🔍 Filters")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            company_search = st.text_input("🏢 Company Name", placeholder="Search...", key="screener_company_search")
        
        with col2:
            st.markdown("💰 **Price (₹)**")
            price_data_min = float(df['Price'].min()) if 'Price' in df.columns and df['Price'].notna().any() else 0.0
            price_data_max = float(df['Price'].max()) if 'Price' in df.columns and df['Price'].notna().any() else 10000.0
            price_col1, price_col2 = st.columns(2)
            with price_col1:
                price_min = st.number_input("Minimum", value=price_data_min, min_value=0.0, key="screener_price_min", label_visibility="visible")
            with price_col2:
                price_max = st.number_input("Maximum", value=price_data_max, min_value=0.0, key="screener_price_max", label_visibility="visible")
            price_range = (price_min, price_max)
        
        with col3:
            st.markdown("📈 **Market Cap (Cr)**")
            mcap_data_min = float(df['Market_Cap'].min()) if 'Market_Cap' in df.columns and df['Market_Cap'].notna().any() else 0.0
            mcap_data_max = float(df['Market_Cap'].max()) if 'Market_Cap' in df.columns and df['Market_Cap'].notna().any() else 50000.0
            mcap_col1, mcap_col2 = st.columns(2)
            with mcap_col1:
                mcap_min = st.number_input("Minimum", value=mcap_data_min, min_value=0.0, key="screener_mcap_min", label_visibility="visible")
            with mcap_col2:
                mcap_max = st.number_input("Maximum", value=mcap_data_max, min_value=0.0, key="screener_mcap_max", label_visibility="visible")
            mcap_range = (mcap_min, mcap_max)
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.markdown("📊 **Sales YOY %**")
            sales_col1, sales_col2 = st.columns(2)
            with sales_col1:
                sales_yoy_min = st.number_input("Minimum", value=-100.0, key="screener_sales_min", label_visibility="visible")
            with sales_col2:
                sales_yoy_max = st.number_input("Maximum", value=500.0, key="screener_sales_max", label_visibility="visible")
            sales_yoy = (sales_yoy_min, sales_yoy_max)
        
        with col6:
            st.markdown("💹 **EBIDT YOY %**")
            ebidt_col1, ebidt_col2 = st.columns(2)
            with ebidt_col1:
                ebidt_yoy_min = st.number_input("Minimum", value=-100.0, key="screener_ebidt_min", label_visibility="visible")
            with ebidt_col2:
                ebidt_yoy_max = st.number_input("Maximum", value=500.0, key="screener_ebidt_max", label_visibility="visible")
            ebidt_yoy = (ebidt_yoy_min, ebidt_yoy_max)
        
        with col7:
            st.markdown("💵 **Net Profit YOY %**")
            profit_col1, profit_col2 = st.columns(2)
            with profit_col1:
                profit_yoy_min = st.number_input("Minimum", value=-100.0, key="screener_profit_min", label_visibility="visible")
            with profit_col2:
                profit_yoy_max = st.number_input("Maximum", value=500.0, key="screener_profit_max", label_visibility="visible")
            profit_yoy = (profit_yoy_min, profit_yoy_max)
        
        with col8:
            st.markdown("📉 **EPS YOY %**")
            eps_col1, eps_col2 = st.columns(2)
            with eps_col1:
                eps_yoy_min = st.number_input("Minimum", value=-100.0, key="screener_eps_min", label_visibility="visible")
            with eps_col2:
                eps_yoy_max = st.number_input("Maximum", value=500.0, key="screener_eps_max", label_visibility="visible")
            eps_yoy = (eps_yoy_min, eps_yoy_max)
        
        # Apply filters
        filtered_df = df.copy()
        
        if company_search:
            if 'Company' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Company'].str.contains(company_search, case=False, na=False)]
        
        if 'Price' in filtered_df.columns:
            filtered_df = filtered_df[(filtered_df['Price'].between(price_range[0], price_range[1], inclusive='both') | filtered_df['Price'].isna())]
        
        if 'Market_Cap' in filtered_df.columns:
            filtered_df = filtered_df[(filtered_df['Market_Cap'].between(mcap_range[0], mcap_range[1], inclusive='both') | filtered_df['Market_Cap'].isna())]
        
        if 'Sales_YOY' in filtered_df.columns:
            filtered_df = filtered_df[(filtered_df['Sales_YOY'].between(sales_yoy[0], sales_yoy[1], inclusive='both') | filtered_df['Sales_YOY'].isna())]
        
        if 'EBIDT_YOY' in filtered_df.columns:
            filtered_df = filtered_df[(filtered_df['EBIDT_YOY'].between(ebidt_yoy[0], ebidt_yoy[1], inclusive='both') | filtered_df['EBIDT_YOY'].isna())]
        
        if 'NetProfit_YOY' in filtered_df.columns:
            filtered_df = filtered_df[(filtered_df['NetProfit_YOY'].between(profit_yoy[0], profit_yoy[1], inclusive='both') | filtered_df['NetProfit_YOY'].isna())]
        
        if 'EPS_YOY' in filtered_df.columns:
            filtered_df = filtered_df[(filtered_df['EPS_YOY'].between(eps_yoy[0], eps_yoy[1], inclusive='both') | filtered_df['EPS_YOY'].isna())]
        
        st.markdown("---")
        st.subheader(f"📋 Results ({len(filtered_df)} companies)")
        
        column_order = [
            'Company', 'Price', 'Market_Cap', 'PE',
            'Sales_YOY', 'Sales_Dec25', 'Sales_Sep25', 'Sales_Dec24',
            'EBIDT_YOY', 'EBIDT_Dec25', 'EBIDT_Sep25', 'EBIDT_Dec24',
            'NetProfit_YOY', 'NetProfit_Dec25', 'NetProfit_Sep25', 'NetProfit_Dec24',
            'EPS_YOY', 'EPS_Dec25', 'EPS_Sep25', 'EPS_Dec24'
        ]
        
        column_order = [col for col in column_order if col in filtered_df.columns]
        display_df = filtered_df[column_order]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            column_config={
                "Company": st.column_config.TextColumn("Company", width="medium"),
                "Price": st.column_config.NumberColumn("Price (₹)", format="%.2f"),
                "Market_Cap": st.column_config.NumberColumn("M.Cap (Cr)", format="%.2f"),
                "PE": st.column_config.NumberColumn("P/E", format="%.1f"),
                "Sales_YOY": st.column_config.NumberColumn("Sales YOY%", format="%.1f"),
                "EBIDT_YOY": st.column_config.NumberColumn("EBIDT YOY%", format="%.1f"),
                "NetProfit_YOY": st.column_config.NumberColumn("Profit YOY%", format="%.1f"),
                "EPS_YOY": st.column_config.NumberColumn("EPS YOY%", format="%.1f"),
            }
        )
        
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="quarterly_results.csv",
            mime="text/csv",
            key="screener_download"
        )
    
    else:
        st.info("👆 Click 'Fetch Quarterly Results' to load data")
    
    st.markdown("---")
    st.caption("Data source: Screener.in | Updates: Quarterly")


if __name__ == "__main__":
    st.set_page_config(page_title="Quarterly Results Screener", layout="wide")
    show_quarterly_screener()
