import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, date, timedelta
import numpy as np

# Cache chart generators to improve performance
@st.cache_data(ttl=600, show_spinner=False)
def generate_expense_trend_chart(
    df: pd.DataFrame, 
    date_column: str = "date_incurred",
    amount_column: str = "amount",
    _cache_key: float = 0
) -> alt.Chart:
    """
    Generate a time series chart for expenses over time.
    
    Args:
        df: DataFrame with expense data
        date_column: Name of date column
        amount_column: Name of amount column
        _cache_key: Cache invalidation key
        
    Returns:
        alt.Chart: Altair chart object
    """
    if df.empty:
        # Return empty chart with message
        empty_df = pd.DataFrame({'x': [0], 'y': [0]})
        return alt.Chart(empty_df).mark_text(
            text='No data available',
            color='gray',
            fontSize=20,
            align='center'
        ).encode(x='x:Q', y='y:Q').properties(width=600, height=300)
    
    # Ensure date column is datetime
    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column])
    else:
        return alt.Chart(pd.DataFrame({'x': [0], 'y': [0]})).mark_text(
            text=f'Column {date_column} not found',
            color='red',
            fontSize=20,
            align='center'
        ).encode(x='x:Q', y='y:Q').properties(width=600, height=300)
    
    # Group by date and sum amounts
    daily_expenses = df.groupby(df[date_column].dt.date)[amount_column].sum().reset_index()
    daily_expenses.columns = ['date', 'total']
    
    # Create the time series chart
    chart = alt.Chart(daily_expenses).mark_line(point=True).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('total:Q', title='Total Expenses'),
        tooltip=['date:T', 'total:Q']
    ).properties(
        width=600,
        height=300,
        title='Daily Expense Trend'
    ).interactive()
    
    return chart

@st.cache_data(ttl=600, show_spinner=False)
def generate_category_pie_chart(
    df: pd.DataFrame, 
    category_column: str = "category", 
    amount_column: str = "amount",
    _cache_key: float = 0
) -> go.Figure:
    """
    Generate a pie chart for expenses by category.
    
    Args:
        df: DataFrame with expense data
        category_column: Name of category column
        amount_column: Name of amount column
        _cache_key: Cache invalidation key
        
    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty or category_column not in df.columns:
        # Return empty chart
        fig = go.Figure(go.Pie(
            labels=['No data'],
            values=[1],
            textinfo='none'
        ))
        fig.update_layout(
            title_text='No data available',
            showlegend=False,
            height=300,
            font=dict(color='gray')
        )
        return fig
    
    # Group by category and sum amounts
    category_totals = df.groupby(category_column)[amount_column].sum().reset_index()
    category_totals = category_totals.sort_values(amount_column, ascending=False)
    
    # Create pie chart
    fig = px.pie(
        category_totals, 
        values=amount_column, 
        names=category_column,
        title='Expenses by Category',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig

@st.cache_data(ttl=600, show_spinner=False)
def generate_weekly_comparison_chart(
    df: pd.DataFrame, 
    date_column: str = "date_incurred",
    amount_column: str = "amount",
    weeks_to_compare: int = 4,
    _cache_key: float = 0
) -> alt.Chart:
    """
    Generate a bar chart comparing weekly expenses.
    
    Args:
        df: DataFrame with expense data
        date_column: Name of date column
        amount_column: Name of amount column
        weeks_to_compare: Number of weeks to include
        _cache_key: Cache invalidation key
        
    Returns:
        alt.Chart: Altair chart object
    """
    if df.empty or date_column not in df.columns:
        # Return empty chart with message
        empty_df = pd.DataFrame({'x': [0], 'y': [0]})
        return alt.Chart(empty_df).mark_text(
            text='No data available',
            color='gray',
            fontSize=20,
            align='center'
        ).encode(x='x:Q', y='y:Q').properties(width=600, height=300)
    
    # Ensure date column is datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Get the current week's end date (last day available in data)
    latest_date = df[date_column].max()
    current_week_end = latest_date.date()
    
    # Calculate week start dates for comparison
    week_starts = []
    week_ends = []
    week_labels = []
    
    for i in range(weeks_to_compare):
        end_date = current_week_end - timedelta(days=7*i)
        start_date = end_date - timedelta(days=6)
        week_starts.append(start_date)
        week_ends.append(end_date)
        week_labels.append(f"Week {weeks_to_compare-i}")
    
    # Reverse lists to have chronological order
    week_starts.reverse()
    week_ends.reverse()
    week_labels.reverse()
    
    # Calculate weekly totals
    weekly_totals = []
    
    for i in range(len(week_starts)):
        start = week_starts[i]
        end = week_ends[i]
        mask = (df[date_column].dt.date >= start) & (df[date_column].dt.date <= end)
        weekly_total = df.loc[mask, amount_column].sum()
        weekly_totals.append({
            'week': week_labels[i],
            'total': weekly_total,
            'start_date': start.strftime('%b %d'),
            'end_date': end.strftime('%b %d')
        })
    
    weekly_df = pd.DataFrame(weekly_totals)
    
    # Create the bar chart
    chart = alt.Chart(weekly_df).mark_bar().encode(
        x=alt.X('week:N', title='Week', sort=week_labels),
        y=alt.Y('total:Q', title='Total Expenses'),
        color=alt.Color('week:N', legend=None),
        tooltip=['week:N', 'start_date:N', 'end_date:N', 'total:Q']
    ).properties(
        width=600,
        height=300,
        title='Weekly Expense Comparison'
    ).interactive()
    
    return chart

@st.cache_data(ttl=600, show_spinner=False)
def generate_month_over_month_chart(
    df: pd.DataFrame, 
    date_column: str = "date_incurred",
    amount_column: str = "amount",
    months_to_compare: int = 6,
    _cache_key: float = 0
) -> go.Figure:
    """
    Generate a line chart comparing monthly expenses.
    
    Args:
        df: DataFrame with expense data
        date_column: Name of date column
        amount_column: Name of amount column
        months_to_compare: Number of months to include
        _cache_key: Cache invalidation key
        
    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty or date_column not in df.columns:
        # Return empty chart
        fig = go.Figure()
        fig.update_layout(
            title_text='No data available',
            height=300,
            font=dict(color='gray')
        )
        return fig
    
    # Ensure date column is datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Extract month and year from date
    df['month_year'] = df[date_column].dt.strftime('%b %Y')
    df['month'] = df[date_column].dt.month
    df['year'] = df[date_column].dt.year
    
    # Group by month/year and sum expenses
    monthly_totals = df.groupby(['year', 'month', 'month_year'])[amount_column].sum().reset_index()
    
    # Sort chronologically
    monthly_totals['date'] = pd.to_datetime(monthly_totals['month_year'], format='%b %Y')
    monthly_totals = monthly_totals.sort_values('date')
    
    # Limit to the specified number of months
    if len(monthly_totals) > months_to_compare:
        monthly_totals = monthly_totals.tail(months_to_compare)
    
    # Create line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_totals['month_year'], 
        y=monthly_totals[amount_column],
        mode='lines+markers',
        name='Monthly Expenses',
        line=dict(width=3, color='#1f77b4'),
        marker=dict(size=8)
    ))
    
    # Add labels to data points
    fig.update_traces(
        texttemplate='%{y:.2f}',
        textposition='top center'
    )
    
    fig.update_layout(
        title='Monthly Expense Comparison',
        xaxis_title='Month',
        yaxis_title='Total Expenses',
        height=400,
        hovermode='x unified'
    )
    
    return fig

@st.cache_data(ttl=600, show_spinner=False)
def generate_heatmap_chart(
    df: pd.DataFrame, 
    date_column: str = "date_incurred",
    amount_column: str = "amount",
    _cache_key: float = 0
) -> go.Figure:
    """
    Generate a heatmap of expenses by day of week and week number.
    
    Args:
        df: DataFrame with expense data
        date_column: Name of date column
        amount_column: Name of amount column
        _cache_key: Cache invalidation key
        
    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty or date_column not in df.columns:
        # Return empty chart
        fig = go.Figure()
        fig.update_layout(
            title_text='No data available',
            height=300,
            font=dict(color='gray')
        )
        return fig
    
    # Ensure date column is datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Extract day of week and week of year
    df['day_of_week'] = df[date_column].dt.day_name()
    df['week_number'] = df[date_column].dt.isocalendar().week
    
    # Get unique weeks from data
    unique_weeks = sorted(df['week_number'].unique())
    
    # Map to simpler week labels
    week_mapping = {week: f"Week {i+1}" for i, week in enumerate(unique_weeks)}
    df['week_label'] = df['week_number'].map(week_mapping)
    
    # Order days of week properly
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Group by day of week and week, sum expenses
    heatmap_data = df.groupby(['day_of_week', 'week_label'])[amount_column].sum().reset_index()
    
    # Create a pivot table for the heatmap
    pivot_data = heatmap_data.pivot(index='day_of_week', columns='week_label', values=amount_column)
    
    # Reorder rows based on day_order
    pivot_data = pivot_data.reindex(day_order)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Blues',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='Expense Heatmap by Day and Week',
        height=400,
        xaxis_title='Week',
        yaxis_title='Day of Week'
    )
    
    return fig

@st.cache_data(ttl=600, show_spinner=False)
def generate_cumulative_expense_chart(
    df: pd.DataFrame, 
    date_column: str = "date_incurred",
    amount_column: str = "amount",
    _cache_key: float = 0
) -> go.Figure:
    """
    Generate a cumulative expense chart over time.
    
    Args:
        df: DataFrame with expense data
        date_column: Name of date column
        amount_column: Name of amount column
        _cache_key: Cache invalidation key
        
    Returns:
        go.Figure: Plotly figure object
    """
    if df.empty or date_column not in df.columns:
        # Return empty chart
        fig = go.Figure()
        fig.update_layout(
            title_text='No data available',
            height=300,
            font=dict(color='gray')
        )
        return fig
    
    # Ensure date column is datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Sort by date
    df_sorted = df.sort_values(by=date_column)
    
    # Group by date
    daily_expenses = df_sorted.groupby(df_sorted[date_column].dt.date)[amount_column].sum().reset_index()
    daily_expenses.columns = ['date', 'total']
    
    # Calculate cumulative sum
    daily_expenses['cumulative'] = daily_expenses['total'].cumsum()
    
    # Create figure
    fig = go.Figure()
    
    # Add daily expense bars
    fig.add_trace(go.Bar(
        x=daily_expenses['date'],
        y=daily_expenses['total'],
        name='Daily Expenses',
        marker_color='lightblue'
    ))
    
    # Add cumulative line
    fig.add_trace(go.Scatter(
        x=daily_expenses['date'],
        y=daily_expenses['cumulative'],
        name='Cumulative Expenses',
        mode='lines+markers',
        line=dict(color='darkblue', width=3),
        marker=dict(size=4)
    ))
    
    fig.update_layout(
        title='Cumulative Expenses Over Time',
        xaxis_title='Date',
        yaxis_title='Amount',
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def render_dashboard(df: pd.DataFrame, metadata: Dict, start_date: date, end_date: date, cache_key: float = 0) -> None:
    """
    Render a comprehensive dashboard with multiple charts.
    
    Args:
        df: DataFrame with expense data
        metadata: Metadata about the expenses
        start_date: Start date for filtering
        end_date: End date for filtering
        cache_key: Cache invalidation key
    """
    if df.empty:
        st.warning("No expense data available for the selected period.")
        return
    
    # Display total expenses
    total_expenses = df['amount'].sum()
    avg_expense = df['amount'].mean()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Expenses", f"${total_expenses:.2f}")
    
    with col2:
        st.metric("Number of Expenses", f"{len(df)}")
    
    with col3:
        st.metric("Average Expense", f"${avg_expense:.2f}")
    
    # Display trend chart in first row
    st.subheader("Expense Trends")
    trend_chart = generate_expense_trend_chart(df, _cache_key=cache_key)
    st.altair_chart(trend_chart, use_container_width=True)
    
    # Display category breakdown and weekly comparison in second row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Category Breakdown")
        if 'category_name' in df.columns:
            pie_chart = generate_category_pie_chart(df, category_column='category_name', _cache_key=cache_key)
            st.plotly_chart(pie_chart, use_container_width=True)
        else:
            st.warning("Category data not available.")
    
    with col2:
        st.subheader("Weekly Comparison")
        weekly_chart = generate_weekly_comparison_chart(df, _cache_key=cache_key)
        st.altair_chart(weekly_chart, use_container_width=True)
    
    # Display cumulative and monthly comparison in third row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Cumulative Expenses")
        cumulative_chart = generate_cumulative_expense_chart(df, _cache_key=cache_key)
        st.plotly_chart(cumulative_chart, use_container_width=True)
    
    with col2:
        st.subheader("Monthly Comparison")
        monthly_chart = generate_month_over_month_chart(df, _cache_key=cache_key)
        st.plotly_chart(monthly_chart, use_container_width=True)
    
    # Display expense heatmap
    st.subheader("Expense Heatmap")
    heatmap_chart = generate_heatmap_chart(df, _cache_key=cache_key)
    st.plotly_chart(heatmap_chart, use_container_width=True)

# Add missing wrapper functions needed by dashboard.py
def create_expense_by_category_chart(expenses: List[Dict], title: str = "Expenses by Category") -> go.Figure:
    """
    Create a pie chart showing expense distribution by category.
    
    Args:
        expenses: List of expense dictionaries from API
        title: Chart title
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Handle empty data case
    if not expenses:
        fig = go.Figure()
        fig.update_layout(
            title=title,
            template="plotly_white",
            height=400,
            annotations=[{
                'text': 'No data available',
                'showarrow': False,
                'font': {'size': 20, 'color': 'gray'},
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5
            }]
        )
        return fig
    
    # Convert expenses list to DataFrame
    df = pd.DataFrame(expenses)
    
    # Check if we have the necessary columns
    if "category_name" not in df.columns:
        if "category_id" in df.columns and "category_name" not in df.columns:
            # If we have category_id but not category_name, we can't create a meaningful pie chart
            fig = go.Figure()
            fig.update_layout(
                title=title,
                template="plotly_white",
                height=400,
                annotations=[{
                    'text': 'Category name data unavailable',
                    'showarrow': False,
                    'font': {'size': 20, 'color': 'gray'},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }]
            )
            return fig
    
    # Use the existing chart generator
    fig = generate_category_pie_chart(df, category_column="category_name", amount_column="amount")
    
    # Update title and ensure layout properties are explicitly set
    fig.update_layout(
        title_text=title,
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_expense_trend_chart(expenses: List[Dict], time_unit: str = "day", title: str = "Expense Trend") -> go.Figure:
    """
    Create a line chart showing expense trends over time.
    
    Args:
        expenses: List of expense dictionaries from API
        time_unit: Time unit for aggregation ('day', 'week', 'month')
        title: Chart title
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Handle empty data case
    if not expenses:
        fig = go.Figure()
        fig.update_layout(
            title=title,
            template="plotly_white",
            height=400,
            xaxis_title="Date",
            yaxis_title="Amount",
            annotations=[{
                'text': 'No data available',
                'showarrow': False,
                'font': {'size': 20, 'color': 'gray'},
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5
            }]
        )
        return fig
    
    try:
        # Convert expenses list to DataFrame
        df = pd.DataFrame(expenses)
        
        # Check for required columns
        if "date_incurred" not in df.columns or "amount" not in df.columns:
            fig = go.Figure()
            fig.update_layout(
                title=title,
                template="plotly_white",
                height=400,
                xaxis_title="Date",
                yaxis_title="Amount",
                annotations=[{
                    'text': 'Required data fields missing',
                    'showarrow': False,
                    'font': {'size': 20, 'color': 'gray'},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }]
            )
            return fig
        
        # Convert date column to datetime
        df["date_incurred"] = pd.to_datetime(df["date_incurred"], errors='coerce')
        
        # Remove rows with invalid dates
        df = df.dropna(subset=["date_incurred"])
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                title=title,
                template="plotly_white",
                height=400,
                xaxis_title="Date",
                yaxis_title="Amount",
                annotations=[{
                    'text': 'No valid date data available',
                    'showarrow': False,
                    'font': {'size': 20, 'color': 'gray'},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }]
            )
            return fig
        
        # Group by time unit
        if time_unit == "day":
            df["time_group"] = df["date_incurred"].dt.date
        elif time_unit == "week":
            df["time_group"] = df["date_incurred"].dt.isocalendar().week
            df["week_label"] = df["date_incurred"].dt.strftime("Week %U")
        elif time_unit == "month":
            df["time_group"] = df["date_incurred"].dt.strftime("%Y-%m")
            df["month_label"] = df["date_incurred"].dt.strftime("%b %Y")
        
        # Group and sum
        grouped = df.groupby("time_group")["amount"].sum().reset_index()
        
        # Check if we have data after grouping
        if grouped.empty:
            fig = go.Figure()
            fig.update_layout(
                title=title,
                template="plotly_white",
                height=400,
                xaxis_title="Date",
                yaxis_title="Amount",
                annotations=[{
                    'text': 'No data available after grouping',
                    'showarrow': False, 
                    'font': {'size': 20, 'color': 'gray'},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }]
            )
            return fig
        
        # Create figure
        fig = go.Figure()
        
        # Add trace
        fig.add_trace(
            go.Scatter(
                x=grouped["time_group"],
                y=grouped["amount"],
                mode="lines+markers",
                name="Expenses",
                line=dict(width=3, color="#1f77b4"),
                marker=dict(size=8)
            )
        )
        
        # Explicitly set all layout properties
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Amount",
            template="plotly_white",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor="rgba(0,0,0,0.1)"),
            yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor="rgba(0,0,0,0.1)")
        )
        
        return fig
    except Exception as e:
        # Handle any unexpected errors
        fig = go.Figure()
        fig.update_layout(
            title=f"{title} (Error)",
            template="plotly_white",
            height=400,
            xaxis_title="Date",
            yaxis_title="Amount",
            annotations=[{
                'text': f'Error creating chart: {str(e)}',
                'showarrow': False,
                'font': {'size': 16, 'color': 'red'},
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5
            }]
        )
        return fig

def create_category_comparison_chart(expenses: List[Dict], title: str = "Category Comparison") -> go.Figure:
    """
    Create a bar chart comparing expenses across categories.
    
    Args:
        expenses: List of expense dictionaries from API
        title: Chart title
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Handle empty data case
    if not expenses:
        fig = go.Figure()
        fig.update_layout(
            title=title,
            template="plotly_white",
            height=400,
            annotations=[{
                'text': 'No data available',
                'showarrow': False,
                'font': {'size': 20, 'color': 'gray'},
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5
            }]
        )
        return fig
    
    # Convert expenses list to DataFrame
    df = pd.DataFrame(expenses)
    
    # Check if the category column exists
    if "category_name" in df.columns:
        category_col = "category_name"
    elif "category_id" in df.columns:
        category_col = "category_id"
    else:
        # No category column available
        fig = go.Figure()
        fig.update_layout(
            title=title,
            template="plotly_white",
            height=400,
            annotations=[{
                'text': 'Category data unavailable',
                'showarrow': False,
                'font': {'size': 20, 'color': 'gray'},
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5
            }]
        )
        return fig
        
    # Group by category and sum
    category_totals = df.groupby(category_col)["amount"].sum().reset_index()
    
    # Make sure we have data after grouping
    if category_totals.empty:
        fig = go.Figure()
        fig.update_layout(
            title=title,
            template="plotly_white",
            height=400,
            annotations=[{
                'text': 'No category data available',
                'showarrow': False,
                'font': {'size': 20, 'color': 'gray'},
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5
            }]
        )
        return fig
    
    # Sort values - handling empty DataFrame possibility
    category_totals = category_totals.sort_values("amount", ascending=True)
    
    # Create figure
    fig = go.Figure()
    
    # Add trace
    fig.add_trace(
        go.Bar(
            y=category_totals[category_col],
            x=category_totals["amount"],
            orientation="h",
            marker=dict(color="#2ca02c")
        )
    )
    
    # Explicitly set all layout properties
    fig.update_layout(
        title=title,
        xaxis_title="Total Amount",
        yaxis_title="Category",
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor="rgba(0,0,0,0.1)"),
        yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor="rgba(0,0,0,0.1)")
    )
    
    return fig
