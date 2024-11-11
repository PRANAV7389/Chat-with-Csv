import streamlit as st
import pandas as pd
import plotly.express as px
import sweetviz as sv
from pandasai import SmartDataframe
from pandasai.llm import BambooLLM
import warnings
warnings.filterwarnings("ignore", category=VisibleDeprecationWarning)

# Set page config for Streamlit app
st.set_page_config(page_title='Unlock Data Insights', layout='centered')

# Add gradient background and improve accessibility
st.markdown("""
    <style>
        /* General styling */
        body, .main, .block-container {
            background: linear-gradient(135deg, #5D8AA8, #F2D7D9);
            color: #333;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Sidebar Styling */
        .css-1d391kg {
            background-color: #2C3E50;
            color: white;
        }

        .css-1d391kg .sidebar-content {
            background: #34495E;
        }

        .sidebar .sidebar-content {
            color: #FFFFFF;
            padding: 15px;
        }

        .sidebar h3 {
            color: #FFFFFF;
            font-size: 22px;
            text-align: center;
        }

        /* Headers and Paragraphs */
        h1, h2, h3, p {
            color: #333;
            font-weight: bold;
        }

        /* Styling of buttons and links */
        .stButton button, .stDownloadButton button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }

        .stButton button:hover, .stDownloadButton button:hover {
            background-color: #2980b9;
        }

        .stTextInput input {
            background-color: #ecf0f1;
            border-radius: 5px;
            padding: 10px;
        }

        .stTextArea textarea {
            background-color: #ecf0f1;
            border-radius: 5px;
            padding: 10px;
        }

        /* Inputs and Select Boxes */
        .stSelectbox, .stMultiselect {
            background-color: #ecf0f1;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        }

        /* Add more visual spacing between elements */
        .stSlider, .stFileUploader, .stCheckbox {
            margin-bottom: 20px;
        }

        /* Style the table (Data preview section) */
        .dataframe {
            border: 1px solid #ccc;
            border-radius: 10px;
            overflow: hidden;
        }
        .dataframe th {
            background-color: #3498db;
            color: white;
            padding: 12px;
        }
        .dataframe td {
            padding: 10px;
            border-top: 1px solid #ccc;
        }

        /* Style expanders */
        .stExpander {
            background-color: #ecf0f1;
            border-radius: 5px;
            padding: 15px;
        }

        .stExpander header {
            font-weight: bold;
            font-size: 18px;
        }

    </style>
""", unsafe_allow_html=True)

# Title of the app
st.title('Data Visualizer with PandasAI')

# Sidebar navigation buttons with improved appearance
st.sidebar.markdown("<h3 style='color: white;'>Navigation</h3>", unsafe_allow_html=True)
menu = st.sidebar.radio("Select an option", ["Upload Data", "Generate Plot", "Chat with Data"])

# File uploader for data upload
if menu == "Upload Data":
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file is not None:
        # Store uploaded file in session state
        st.session_state.uploaded_file = uploaded_file

        # Load the CSV file into a DataFrame
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df  # Save df to session state

        # Section Header
        st.markdown("### Uploaded File Information", unsafe_allow_html=True)
        st.write("**File Name:**", uploaded_file.name)
        st.write("**File Size:**", f"{round(uploaded_file.size / 1024, 2)} KB")
        st.markdown("---")

        # Data Preview with Row Selection
        st.markdown("### Data Preview")
        num_rows = st.slider("Number of Rows to Preview:", min_value=5, max_value=50, value=5)
        st.write(df.head(num_rows))

        # Interactive Data Filtering Section
        st.markdown("### Interactive Data Filtering")
        st.write("Use the filters below to refine the data preview based on unique column values.")

        # Filter Data by Unique Values in Each Column
        filtered_df = df.copy()
        for column in df.columns:
            unique_values = df[column].dropna().unique()
            if len(unique_values) <= 50:
                selected_values = st.multiselect(f"{column}:", options=unique_values, default=unique_values)
                filtered_df = filtered_df[filtered_df[column].isin(selected_values)]

        # Display filtered data preview
        st.write("**Filtered Data Preview:**")
        st.write(filtered_df.head(num_rows))
        st.markdown("---")

        # Collapsible Section for Data Statistics and Column Details
        with st.expander("Dataset Statistics and Column Details", expanded=False):
            st.markdown("### Data Statistics")
            st.write(df.describe())
            st.markdown("### Column Data Types")
            st.write(df.dtypes)
            st.markdown("### Missing Values Overview")
            missing_values = df.isnull().sum()
            st.write(missing_values[missing_values > 0])

        # Generate Sweetviz Report
        with st.expander("Generate Data Profiling Report", expanded=False):
            st.write("This option generates a comprehensive report of your dataset using Sweetviz.")
            if st.checkbox("Generate Sweetviz Report"):
                report = sv.analyze(df)
                report.show_html('sweetviz_report.html')
                st.markdown("You can download the generated report [here](sweetviz_report.html).")

        # Clear Uploaded File Option
        if st.button("Clear Uploaded File"):
            st.session_state.pop("uploaded_file", None)
            st.session_state.pop("df", None)
            st.experimental_rerun()

    else:
        # Information if file was uploaded previously
        if 'uploaded_file' in st.session_state:
            st.info("You've already uploaded a file. You can proceed to the other sections.")
        else:
            st.info("Please upload a CSV file to proceed.")

# Generate Plot Page
elif menu == "Generate Plot":
    if 'df' not in st.session_state:
        st.warning("Please upload data first in the 'Upload Data' section.")
    else:
        df = st.session_state.df  # Get df from session state

        # Columns for Data Preview and Plot Options
        col1, col2 = st.columns(2)
        columns = df.columns.tolist()

        with col1:
            st.write("**Data Preview**")
            st.write(df.head())  # Show preview of data

        with col2:
            x_axis = st.selectbox('Select the X-axis', options=columns + ["None"])
            y_axis = st.selectbox('Select the Y-axis', options=columns + ["None"])

            # Aggregation options
            aggregation = st.selectbox("Select Aggregation", ["None", "Sum", "Average", "Count"])

            # Available plot types
            plot_list = ['Line Plot', 'Bar Chart', 'Scatter Plot', 'Distribution Plot', 'Count Plot', 'Box Plot', 'Heatmap']
            plot_type = st.selectbox('Select the type of plot', options=plot_list)

            # Customization options for plot
            color = st.color_picker('Select Plot Color', '#00f900')
            plot_title = st.text_input('Enter Plot Title', f"{y_axis} vs {x_axis}")
            x_axis_label = st.text_input('Enter label for X-axis', x_axis)
            y_axis_label = st.text_input('Enter label for Y-axis', y_axis)

        # Aggregating data based on selection
        if aggregation != "None":
            if aggregation == "Sum":
                df = df.groupby(x_axis)[y_axis].sum().reset_index()
            elif aggregation == "Average":
                df = df.groupby(x_axis)[y_axis].mean().reset_index()
            elif aggregation == "Count":
                df = df.groupby(x_axis)[y_axis].count().reset_index()

        # Generating Plot dynamically
        if x_axis != "None" and y_axis != "None":
            if plot_type == 'Line Plot':
                fig = px.line(df, x=x_axis, y=y_axis, title=plot_title, color_discrete_sequence=[color])
            elif plot_type == 'Bar Chart':
                fig = px.bar(df, x=x_axis, y=y_axis, title=plot_title, color_discrete_sequence=[color])  # Fixed here
            elif plot_type == 'Scatter Plot':
                fig = px.scatter(df, x=x_axis, y=y_axis, title=plot_title, color_discrete_sequence=[color])  # Same here
            elif plot_type == 'Distribution Plot':
                fig = px.histogram(df, x=y_axis, title=plot_title, color_discrete_sequence=[color])  # Changed here
            elif plot_type == 'Count Plot':
                fig = px.histogram(df, x=x_axis, title=plot_title, color_discrete_sequence=[color])  # Changed here
            elif plot_type == 'Box Plot':
                fig = px.box(df, x=x_axis, y=y_axis, title=plot_title, color_discrete_sequence=[color])  # Changed here
            elif plot_type == 'Heatmap':
                fig = px.imshow(df.corr(), title=plot_title)  # Changed for heatmap

            # Display plot
            st.plotly_chart(fig)



# Chat with Data Page
elif menu == "Chat with Data":
    if 'df' not in st.session_state:
        st.warning("Please upload data first in the 'Upload Data' section.")
    else:
        df = st.session_state.df  # Get df from session state

        # Section Header
        st.subheader("Chat with Data using PandasAI")

        # Data Preview of the first 5 rows
        st.write("**Data Preview:**")
        st.write(df.head())  # Display the first 5 rows of the DataFrame

        # Bamboo API Key Input
        bamboo_api_key = st.text_input("Enter your Bamboo API Key", type="password")
        
        if bamboo_api_key:
            # Initialize the LLM with the provided API key
            llm = BambooLLM(api_key=bamboo_api_key)
            df_chat = SmartDataframe(df, config={"llm": llm})

            # Text Area for user query
            prompt = st.text_area("Enter your query:")

            # Button to generate the response
            if st.button("Generate Response"):
                if prompt:
                    try:
                        # Get the response from PandasAI
                        response = df_chat.chat(prompt)
                        st.write(f"**Response:** {response}")
                    except Exception as e:
                        st.error(f"Error generating response: {e}")
                else:
                    st.warning("Please enter a prompt to chat with the data!")
        else:
            st.info("You can get your free API key by signing up at [PandasAI](https://pandabi.ai).")


# Footer Section with your name and LinkedIn link
st.markdown("---")
st.markdown("### Created by [Pranav Sharma](https://www.linkedin.com/in/pranav-sharma-7b45531b8)")
st.markdown(
    """
    <a href="https://www.linkedin.com/in/pranav-sharma-7b45531b8" target="_blank">
        <img src="https://img.icons8.com/?size=100&id=13930&format=png&color=000000" alt="LinkedIn" width="30"/>
    </a>
    """,
    unsafe_allow_html=True
)

