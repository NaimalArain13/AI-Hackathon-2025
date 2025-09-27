import streamlit as st
import json
import os
import uuid
import asyncio
from template import generate_template, save_template_file
from profile_reader import parse_docx_to_raw_text, extract_structured_profile

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Roommate Preference Form System",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Function to run async task safely in Streamlit
def run_async(func, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(func(*args))

def parse_docx_profile(file_path: str):
    """
    Parse a DOCX file to extract raw text and convert to structured JSON using agent.

    Args:
        file_path: Path to the DOCX file

    Returns:
        tuple: (raw_text, structured_json)
    """
    if not DOCX_AVAILABLE:
        return (
            "Error: python-docx library not available. Please install it with: pip install python-docx",
            None,
        )

    try:
        # Step 1: Parse to raw text
        raw_text = parse_docx_to_raw_text(file_path)
        if raw_text is None:
            return "Error extracting raw text from DOCX", None

        # Step 2: Extract structured data using agent
        profile_id = str(uuid.uuid4())
        structured_data = run_async(extract_structured_profile, raw_text, profile_id)

        return raw_text, structured_data
    except Exception as e:
        return f"Error processing DOCX file: {str(e)}", None

def main():
    # App header
    st.title("🏠 Roommate Preference Form System")
    st.markdown("---")

    # Initialize session state
    if "parsed_data" not in st.session_state:
        st.session_state.parsed_data = None
    if "raw_text" not in st.session_state:
        st.session_state.raw_text = None

    # Sidebar for navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.selectbox(
        "Choose an option:",
        [
            "🏠 Home",
            "📥 Download Template",
            "📤 Upload & Parse",
            "📊 Results",
            "ℹ️ Help",
        ],
    )

    if page == "🏠 Home":
        show_home_page()
    elif page == "📥 Download Template":
        show_download_page()
    elif page == "📤 Upload & Parse":
        show_upload_page()
    elif page == "📊 Results":
        show_results_page()
    elif page == "ℹ️ Help":
        show_help_page()

def show_home_page():
    st.header("Welcome to the Roommate Preference Form System!")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            """
        ### 🎯 What this system does:
        - Creates downloadable PDF templates
        - Processes filled DOCX forms
        - Extracts structured data automatically
        - Converts preferences to JSON format
        """
        )

        st.success(
            """
        ### 📋 Template includes fields for:
        - City and Area/Neighborhood
        - Budget in PKR
        - Sleep Schedule preferences
        - Cleanliness standards
        - Noise tolerance levels
        - Study habits and patterns
        - Food preferences
        - Additional requirements
        """
        )

    with col2:
        st.warning(
            """
        ### 🔄 Simple 4-Step Process:
        1. **Download** the PDF template
        2. **Convert** it to .docx format
        3. **Fill** out your preferences
        4. **Upload** and get structured JSON
        """
        )

        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            st.sidebar.selectbox(
                "Choose an option:", ["📥 Download Template"], key="nav_override"
            )
            st.rerun()

def show_download_page():
    st.header("📥 Download Template")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(
            """
        ### 📋 Your template will include all necessary fields:
        
        **Personal Preferences:**
        - City and Area/Neighborhood
        - Budget range in PKR
        - Sleep schedule preferences
        
        **Living Style:**
        - Cleanliness standards
        - Noise tolerance levels
        - Study habits and patterns
        
        **Food & Lifestyle:**
        - Food preferences (veg/non-veg/halal)
        - Additional requirements and preferences
        """
        )

    with col2:
        st.markdown("### 🔄 Next Steps:")
        st.markdown(
            """
        1. Click download button
        2. Convert PDF to .docx
        3. Fill out the form
        4. Upload for parsing
        """
        )

    # Download button
    if st.button(
        "📥 Generate & Download Template", type="primary", use_container_width=True
    ):
        try:
            with st.spinner("Generating your template..."):
                # Generate the PDF template
                file_path = save_template_file()

                # Read the file content
                with open(file_path, "rb") as f:
                    pdf_content = f.read()

                st.success("✅ Template generated successfully!")

                # Provide download button
                st.download_button(
                    label="📥 Download PDF Template",
                    data=pdf_content,
                    file_name="roommate_preference_template.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

                st.info(
                    """
                ### 📝 After downloading:
                1. Use an online converter (SmallPDF, ILovePDF, etc.) to convert PDF to DOCX
                2. Open the DOCX file in Microsoft Word
                3. Fill in all your preferences
                4. Save the file and come back to upload it
                """
                )

                # Clean up temporary file
                try:
                    os.remove(file_path)
                except:
                    pass

        except Exception as e:
            st.error(f"❌ Error generating template: {str(e)}")

def show_upload_page():
    st.header("📤 Upload & Parse Your Form")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(
            """
        ### 📁 Upload Instructions:
        Make sure you have:
        1. Downloaded the PDF template
        2. Converted it to .docx format  
        3. Filled it out completely in Microsoft Word
        4. Saved it as a .docx file
        """
        )

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose your filled DOCX file",
            type=["docx"],
            help="Upload your completed roommate preference form in DOCX format",
        )

        if uploaded_file is not None:
            try:
                # Ensure uploads directory exists inside the project
                uploads_dir = os.path.join(os.getcwd(), "uploads")
                os.makedirs(uploads_dir, exist_ok=True)

                # Build a safe, non-colliding destination path
                original_name = os.path.basename(uploaded_file.name)
                base, ext = os.path.splitext(original_name)
                dest_path = os.path.join(uploads_dir, original_name)
                idx = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(uploads_dir, f"{base}_{idx}{ext}")
                    idx += 1

                # Save uploaded file to uploads folder
                with open(dest_path, "wb") as out:
                    out.write(uploaded_file.getvalue())
                print("Saved uploaded file to:", dest_path)

                # Parse and extract using agent
                with st.spinner("Processing your file with AI agent..."):
                    print("parsing fill calling ")
                    raw_text, structured_data = parse_docx_profile(dest_path)
                    print(
                        "parsing fill calling 2",
                        bool(raw_text),
                        structured_data is not None,
                    )

                if structured_data is None:
                    st.error(f"❌ Error processing file: {raw_text}")
                else:
                    # Store in session state
                    st.session_state.parsed_data = structured_data
                    st.session_state.raw_text = raw_text

                    st.success(f"✅ Successfully processed: {uploaded_file.name}")
                    st.info(
                        "📊 Your data has been parsed! Check the 'Results' page to view the structured output."
                    )

                    # Show preview
                    st.markdown("### 📋 Quick Preview:")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("City", structured_data.get("city", "Not found"))
                        st.metric(
                            "Budget",
                            (
                                f"{structured_data.get('budget_PKR', 'Not found')} PKR"
                                if structured_data.get("budget_PKR")
                                else "Not found"
                            ),
                        )
                        st.metric(
                            "Sleep Schedule",
                            structured_data.get("sleep_schedule", "Not found"),
                        )
                        st.metric(
                            "Cleanliness",
                            structured_data.get("cleanliness", "Not found"),
                        )

                    with col_b:
                        st.metric("Area", structured_data.get("area", "Not found"))
                        st.metric(
                            "Noise Tolerance",
                            structured_data.get("noise_tolerance", "Not found"),
                        )
                        st.metric(
                            "Study Habits",
                            structured_data.get("study_habits", "Not found"),
                        )
                        st.metric(
                            "Food Preference",
                            structured_data.get("food_pref", "Not found"),
                        )

            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")

    with col2:
        st.markdown("### 🔍 What happens next?")
        st.markdown(
            """
        - File is parsed automatically
        - Text content is extracted
        - Data is structured into JSON
        - Results are saved in session
        - View results in 'Results' tab
        """
        )

        if st.session_state.parsed_data:
            st.success("✅ Data ready!")
            if st.button("📊 View Results", use_container_width=True):
                st.sidebar.selectbox(
                    "Choose an option:", ["📊 Results"], key="nav_override_results"
                )
                st.rerun()

def show_results_page():
    st.header("📊 Parsed Results")

    if st.session_state.parsed_data is None:
        st.warning("⚠️ No data found. Please upload a DOCX file first.")
        if st.button("📤 Go to Upload Page"):
            st.sidebar.selectbox(
                "Choose an option:", ["📤 Upload & Parse"], key="nav_override_upload"
            )
            st.rerun()
        return

    # Display results
    st.success("✅ Your roommate preferences have been successfully parsed!")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Structured Data", "📝 Raw Text", "💾 Export"])

    with tab1:
        st.markdown("### 🏠 Extracted Preferences:")

        # Display structured data in a nice format
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📍 Location & Budget")
            st.info(
                f"**City:** {st.session_state.parsed_data.get('city', 'Not found')}"
            )
            st.info(
                f"**Area:** {st.session_state.parsed_data.get('area', 'Not found')}"
            )
            st.info(
                f"**Budget:** {st.session_state.parsed_data.get('budget_PKR', 'Not found')} PKR"
                if st.session_state.parsed_data.get("budget_PKR")
                else "**Budget:** Not found"
            )

            st.markdown("#### 🛌 Living Preferences")
            st.info(
                f"**Sleep Schedule:** {st.session_state.parsed_data.get('sleep_schedule', 'Not found')}"
            )
            st.info(
                f"**Cleanliness:** {st.session_state.parsed_data.get('cleanliness', 'Not found')}"
            )

        with col2:
            st.markdown("#### 🔊 Environment & Habits")
            st.info(
                f"**Noise Tolerance:** {st.session_state.parsed_data.get('noise_tolerance', 'Not found')}"
            )
            st.info(
                f"**Study Habits:** {st.session_state.parsed_data.get('study_habits', 'Not found')}"
            )

            st.markdown("#### 🍽️ Food Preferences")
            st.info(
                f"**Food Preference:** {st.session_state.parsed_data.get('food_pref', 'Not found')}"
            )

        # JSON display
        st.markdown("### 📋 Complete JSON Output:")
        json_output = json.dumps(
            st.session_state.parsed_data, indent=2, ensure_ascii=False
        )
        st.json(st.session_state.parsed_data)

    with tab2:
        st.markdown("### 📝 Raw Extracted Text:")
        if st.session_state.raw_text:
            st.text_area(
                "Original text from your DOCX file:",
                st.session_state.raw_text,
                height=300,
                disabled=True,
            )
        else:
            st.info("No raw text available.")

    with tab3:
        st.markdown("### 💾 Export Your Data")

        col1, col2 = st.columns(2)

        with col1:
            # Download as JSON
            json_output = json.dumps(
                st.session_state.parsed_data, indent=2, ensure_ascii=False
            )
            st.download_button(
                label="📥 Download as JSON",
                data=json_output,
                file_name="roommate_preferences.json",
                mime="application/json",
                use_container_width=True,
            )

        with col2:
            # Copy to clipboard button
            if st.button("📋 Copy JSON to Clipboard", use_container_width=True):
                st.code(json_output, language="json")
                st.success("✅ JSON displayed above - you can select and copy it!")

def show_help_page():
    st.header("ℹ️ Help & Instructions")

    tab1, tab2, tab3 = st.tabs(["🚀 Getting Started", "❓ FAQ", "🔧 Troubleshooting"])

    with tab1:
        st.markdown(
            """
        ## 🚀 How to Use This System
        
        ### Step 1: Download Template
        1. Go to the "Download Template" page
        2. Click "Generate & Download Template"
        3. Save the PDF file to your computer
        
        ### Step 2: Convert & Fill
        1. Use an online converter to convert PDF to DOCX:
           - SmallPDF (smallpdf.com)
           - ILovePDF (ilovepdf.com)
           - PDF24 (pdf24.org)
        2. Open the DOCX file in Microsoft Word
        3. Fill in all your preferences completely
        4. Save the file
        
        ### Step 3: Upload & Parse
        1. Go to "Upload & Parse" page
        2. Upload your completed DOCX file
        3. Wait for processing to complete
        
        ### Step 4: View Results
        1. Go to "Results" page
        2. Review your structured data
        3. Export as JSON if needed
        """
        )

    with tab2:
        st.markdown(
            """
        ## ❓ Frequently Asked Questions
        
        **Q: What file formats are supported?**
        A: Currently only DOCX files are supported for upload. The template is provided as PDF.
        
        **Q: Why do I need to convert PDF to DOCX?**
        A: DOCX files are easier to parse and extract structured data from compared to PDFs.
        
        **Q: What if some fields are not detected?**
        A: Make sure to use clear keywords like "budget", "city", "area" etc. in your responses.
        
        **Q: Can I upload multiple files?**
        A: Currently, only one file at a time is supported.
        
        **Q: Is my data stored anywhere?**
        A: No, all processing happens locally in your browser session. Data is not stored permanently.
        """
        )

    with tab3:
        st.markdown(
            """
        ## 🔧 Troubleshooting
        
        **File Upload Issues:**
        - Ensure file is in DOCX format
        - Check file size is under 10MB
        - Make sure file is not corrupted
        
        **Parsing Issues:**
        - Use clear, descriptive text in your responses
        - Include specific keywords for better detection
        - Avoid special characters or formatting
        
        **Missing Data:**
        - Check if you filled all template fields
        - Use standard terms (e.g., "Karachi" instead of "KHI")
        - Include units for budget (e.g., "15000 PKR" or "15k")
        
        **Still Having Issues?**
        - Try re-downloading and filling the template again
        - Ensure you're using the latest version of Microsoft Word
        - Check your internet connection for upload issues
        """
        )

if __name__ == "__main__":
    main()