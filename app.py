import streamlit as st
import pandas as pd
from scraper import scrape_all_pages, verify_login, manual_login
import time
import os

st.set_page_config(page_title="Quarterly Results Screener", layout="wide")

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'login_verified' not in st.session_state:
    st.session_state.login_verified = False

st.title("📊 Quarterly Results Screener")
st.markdown("---")

# Check login status
if not st.session_state.login_verified:
    st.info("🔐 Checking Screener.in login status...")
    
    if verify_login():
        st.success("✅ Already logged in! Ready to scrape.")
        st.session_state.login_verified = True
        time.sleep(1)
        st.rerun()
    else:
        st.warning("⚠️ You need to login to Screener.in first")
        st.markdown("""
        **Steps:**
        1. Click the 'Login to Screener.in' button below
        2. A browser window will open
        3. Login with your Screener.in credentials
        4. Wait for the browser to close automatically
        5. Return here and start scraping!
        """)
        
        if st.button("🔐 Login to Screener.in", type="primary"):
            with st.spinner("Opening browser for login..."):
                success = manual_login()
                if success:
                    st.success("✅ Login successful!")
                    st.session_state.login_verified = True
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Login failed. Please try again.")
        st.stop()

st.markdown("---")

# Page selection
st.subheader("📄 Select Pages to Scrape")
col1, col2 = st.columns(2)

with col1:
    fetch_mode = st.radio(
        "Fetch Mode",
        ["All Pages (1-80)", "Custom Pages"],
        horizontal=True
    )

if fetch_mode == "Custom Pages":
    col3, col4 = st.columns(2)
    with col3:
        page_input = st.text_area(
            "Enter page numbers (comma-separated or ranges)",
            placeholder="e.g., 1,5,10-15,20,25-30,80",
            height=100
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
        max_value=5,
        value=1,
        help="More workers = faster scraping. 2-3 workers recommended for balance."
    )
    if num_workers > 1:
        st.caption(f"⚡ {num_workers}x faster with {num_workers} parallel workers")

with col_perf2:
    delay = st.slider(
        "⏱️ Delay Between Pages (seconds)",
        min_value=1,
        max_value=10,
        value=5,
        help="Lower delay = faster but may trigger rate limits. 3-5s recommended."
    )

# Fetch button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Fetch Quarterly Results", type="primary", use_container_width=True):
        with st.spinner("Fetching data from Screener.in..."):
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
                    pages_to_fetch = sorted(list(set(pages_to_fetch)))  # Remove duplicates and sort
                except:
                    st.error("Invalid page format! Use: 1,5,10-15,20")
                    st.stop()
            
            def update_progress(current_idx, total):
                progress = current_idx / total
                progress_bar.progress(progress)
                status_text.text(f"Scraping page {current_idx}/{total}...")
            
            try:
                from scraper import scrape_all_pages
                df = scrape_all_pages(
                    pages_list=pages_to_fetch, 
                    progress_callback=update_progress,
                    num_workers=num_workers,
                    delay=delay
                )
                st.session_state.data = df
                progress_bar.progress(100)
                status_text.text(f"✅ Successfully fetched {len(df)} companies from {len(pages_to_fetch)} pages!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error fetching data: {e}")

# Display data if available
if st.session_state.data is not None and len(st.session_state.data) > 0:
    df = st.session_state.data.copy()
    
    # Check if required columns exist
    if 'Price' not in df.columns or len(df) == 0:
        st.error("No data fetched. Please try again with different pages.")
        st.stop()
    
    st.markdown("---")
    st.subheader("🔍 Filters")
    
    # Filters in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        company_search = st.text_input("🏢 Company Name", placeholder="Search...")
    
    with col2:
        price_min = float(df['Price'].min()) if 'Price' in df.columns and df['Price'].notna().any() else 0.0
        price_max = float(df['Price'].max()) if 'Price' in df.columns and df['Price'].notna().any() else 10000.0
        price_range = st.slider("💰 Price (₹)", price_min, price_max, (price_min, price_max))
    
    with col3:
        mcap_min = float(df['Market_Cap'].min()) if 'Market_Cap' in df.columns and df['Market_Cap'].notna().any() else 0.0
        mcap_max = float(df['Market_Cap'].max()) if 'Market_Cap' in df.columns and df['Market_Cap'].notna().any() else 50000.0
        mcap_range = st.slider("📈 Market Cap (Cr)", mcap_min, mcap_max, (mcap_min, mcap_max))
    
    # YOY Filters
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        sales_yoy = st.slider("📊 Sales YOY %", -100.0, 500.0, (-100.0, 500.0))
    
    with col6:
        ebidt_yoy = st.slider("💹 EBIDT YOY %", -100.0, 500.0, (-100.0, 500.0))
    
    with col7:
        profit_yoy = st.slider("💵 Net Profit YOY %", -100.0, 500.0, (-100.0, 500.0))
    
    with col8:
        eps_yoy = st.slider("📉 EPS YOY %", -100.0, 500.0, (-100.0, 500.0))
    
    # Apply filters
    filtered_df = df.copy()
    
    if company_search:
        if 'Company' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Company'].str.contains(company_search, case=False, na=False)]
    
    # Apply numeric filters only if columns exist
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
    
    # Reorder columns for better display
    column_order = [
        'Company', 'Price', 'Market_Cap', 'PE',
        'Sales_YOY', 'Sales_Dec25', 'Sales_Sep25', 'Sales_Dec24',
        'EBIDT_YOY', 'EBIDT_Dec25', 'EBIDT_Sep25', 'EBIDT_Dec24',
        'NetProfit_YOY', 'NetProfit_Dec25', 'NetProfit_Sep25', 'NetProfit_Dec24',
        'EPS_YOY', 'EPS_Dec25', 'EPS_Sep25', 'EPS_Dec24'
    ]
    
    # Only include columns that exist
    column_order = [col for col in column_order if col in filtered_df.columns]
    display_df = filtered_df[column_order]
    
    # Format for display
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
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="quarterly_results.csv",
        mime="text/csv"
    )

else:
    st.info("👆 Click 'Fetch Quarterly Results' to load data")
    
st.markdown("---")
st.caption("Data source: Screener.in | Updates: Quarterly")

def show_quarterly_results_screener():
    """
    Standalone function to show quarterly results screener
    Can be imported and used in other Streamlit apps
    """
    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'login_verified' not in st.session_state:
        st.session_state.login_verified = False

    st.title("📊 Quarterly Results Screener")
    st.markdown("---")

    # Check login status
    if not st.session_state.login_verified:
        st.info("🔐 Checking Screener.in login status...")
        
        if verify_login():
            st.success("✅ Already logged in! Ready to scrape.")
            st.session_state.login_verified = True
            time.sleep(1)
            st.rerun()
        else:
            st.warning("⚠️ You need to login to Screener.in first")
            st.markdown("""
            **Steps:**
            1. Click the 'Login to Screener.in' button below
            2. A browser window will open
            3. Login with your Screener.in credentials
            4. Wait for the browser to close automatically
            5. Return here and start scraping!
            """)
            
            if st.button("🔐 Login to Screener.in", type="primary"):
                with st.spinner("Opening browser for login..."):
                    success = manual_login()
                    if success:
                        st.success("✅ Login successful!")
                        st.session_state.login_verified = True
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Login failed. Please try again.")
            st.stop()

    st.markdown("---")

    # Page selection
    st.subheader("📄 Select Pages to Scrape")
    col1, col2 = st.columns(2)

    with col1:
        fetch_mode = st.radio(
            "Fetch Mode",
            ["All Pages (1-80)", "Custom Pages"],
            horizontal=True
        )

    if fetch_mode == "Custom Pages":
        col3, col4 = st.columns(2)
        with col3:
            page_input = st.text_area(
                "Enter page numbers (comma-separated or ranges)",
                placeholder="e.g., 1,5,10-15,20,25-30,80",
                height=100
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
            max_value=5,
            value=1,
            help="More workers = faster scraping. 2-3 workers recommended for balance."
        )
        if num_workers > 1:
            st.caption(f"⚡ {num_workers}x faster with {num_workers} parallel workers")

    with col_perf2:
        delay = st.slider(
            "⏱️ Delay Between Pages (seconds)",
            min_value=1,
            max_value=10,
            value=5,
            help="Lower delay = faster but may trigger rate limits. 3-5s recommended."
        )

    # Fetch button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📄 Fetch Quarterly Results", type="primary", use_container_width=True):
            with st.spinner("Fetching data from Screener.in..."):
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
                        pages_to_fetch = sorted(list(set(pages_to_fetch)))  # Remove duplicates and sort
                    except:
                        st.error("Invalid page format! Use: 1,5,10-15,20")
                        st.stop()
                
                def update_progress(current_idx, total):
                    progress = current_idx / total
                    progress_bar.progress(progress)
                    status_text.text(f"Scraping page {current_idx}/{total}...")
                
                try:
                    df = scrape_all_pages(
                        pages_list=pages_to_fetch, 
                        progress_callback=update_progress,
                        num_workers=num_workers,
                        delay=delay
                    )
                    st.session_state.data = df
                    progress_bar.progress(100)
                    status_text.text(f"✅ Successfully fetched {len(df)} companies from {len(pages_to_fetch)} pages!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error fetching data: {e}")

    # Display data if available
    if st.session_state.data is not None and len(st.session_state.data) > 0:
        df = st.session_state.data.copy()
        
        # Check if required columns exist
        if 'Price' not in df.columns or len(df) == 0:
            st.error("No data fetched. Please try again with different pages.")
            st.stop()
        
        st.markdown("---")
        st.subheader("🔍 Filters")
        
        # Filters in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            company_search = st.text_input("🏢 Company Name", placeholder="Search...")
        
        with col2:
            price_min = float(df['Price'].min()) if 'Price' in df.columns and df['Price'].notna().any() else 0.0
            price_max = float(df['Price'].max()) if 'Price' in df.columns and df['Price'].notna().any() else 10000.0
            price_range = st.slider("💰 Price (₹)", price_min, price_max, (price_min, price_max))
        
        with col3:
            mcap_min = float(df['Market_Cap'].min()) if 'Market_Cap' in df.columns and df['Market_Cap'].notna().any() else 0.0
            mcap_max = float(df['Market_Cap'].max()) if 'Market_Cap' in df.columns and df['Market_Cap'].notna().any() else 50000.0
            mcap_range = st.slider("📈 Market Cap (Cr)", mcap_min, mcap_max, (mcap_min, mcap_max))
        
        # YOY Filters
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            sales_yoy = st.slider("📊 Sales YOY %", -100.0, 500.0, (-100.0, 500.0))
        
        with col6:
            ebidt_yoy = st.slider("💹 EBIDT YOY %", -100.0, 500.0, (-100.0, 500.0))
        
        with col7:
            profit_yoy = st.slider("💵 Net Profit YOY %", -100.0, 500.0, (-100.0, 500.0))
        
        with col8:
            eps_yoy = st.slider("📉 EPS YOY %", -100.0, 500.0, (-100.0, 500.0))
        
        # Apply filters
        filtered_df = df.copy()
        
        if company_search:
            if 'Company' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Company'].str.contains(company_search, case=False, na=False)]
        
        # Apply numeric filters only if columns exist
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
        
        # Reorder columns for better display
        column_order = [
            'Company', 'Price', 'Market_Cap', 'PE',
            'Sales_YOY', 'Sales_Dec25', 'Sales_Sep25', 'Sales_Dec24',
            'EBIDT_YOY', 'EBIDT_Dec25', 'EBIDT_Sep25', 'EBIDT_Dec24',
            'NetProfit_YOY', 'NetProfit_Dec25', 'NetProfit_Sep25', 'NetProfit_Dec24',
            'EPS_YOY', 'EPS_Dec25', 'EPS_Sep25', 'EPS_Dec24'
        ]
        
        # Only include columns that exist
        column_order = [col for col in column_order if col in filtered_df.columns]
        display_df = filtered_df[column_order]
        
        # Format for display
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
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="quarterly_results.csv",
            mime="text/csv"
        )

    else:
        st.info("👆 Click 'Fetch Quarterly Results' to load data")
        
    st.markdown("---")
    st.caption("Data source: Screener.in | Updates: Quarterly")
