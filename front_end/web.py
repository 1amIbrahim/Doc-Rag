import streamlit as st
from streamlit_option_menu import option_menu
import base64

# Function to set background image with dark grey feature box
def set_background(image_url):
    # Encode the image URL for CSS
    background_style = f"""
    <style>
    .stApp {{
        background-image: url("{image_url}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.95;
    }}
    .content {{
        background-color: rgba(255, 255, 255, 0.85);
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }}
    h1, h2, h3 {{
        color: #ffffff;
    }}
    .feature-box {{
        background-color: #2c3e50;  /* Dark grey */
        color: white;  /* White text for contrast */
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }}
    .nav-bar {{
        background-color: #3498db;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }}
    </style>
    """
    st.markdown(background_style, unsafe_allow_html=True)


# Background image URL from Unsplash (free to use)
#BACKGROUND_IMAGE = "https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80"
BACKGROUND_IMAGE = "https://www.ismartcom.com/hubfs/Privacy-age-AI.jpg"
# Set up navigation
def main():
    set_background(BACKGROUND_IMAGE)

    # Horizontal navigation bar
    with st.sidebar:
        page = option_menu(
            "IntelliRetrieve",
            ["Home", "About Us", "Doc Rag System", "Contact Us"],
            icons=["house", "info-circle", "file-text", "envelope"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "5px", "background-color": "#3498db"},
                "icon": {"color": "white", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "color": "white", "--hover-color": "#2980b9"},
                "nav-link-selected": {"background-color": "#2980b9"},
            }
        )

    # Page routing
    if page == "Home":
        home_page()
    elif page == "About Us":
        about_us_page()
    elif page == "Doc Rag System":
        doc_rag_system_page()
    elif page == "Contact Us":
        contact_us_page()

# Home Page
def home_page():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.title("Enhance Productivity with AI")
    st.subheader("Welcome to IntelliRetrieve")
    st.write("Get Started with Privacy-Focused AI-Powered Document Retrieval")

    # Steps Section
    st.markdown("## Add Your Form in 3 Easy Steps")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### STEP 1")
        st.write("Choose a third-party form to embed.")
    with col2:
        st.markdown("### STEP 2")
        st.write("Create and customize your form using the selected platform.")
    with col3:
        st.markdown("### STEP 3")
        st.write("Input the form link into the setting bar and click Confirm.")

    # Key Features
    st.markdown("## Key Features")
    st.markdown("### Why Choose IntelliRetrieve?")
    features = [
        ("Privacy-First Design", "Built with privacy at its core, ensuring your data is always protected."),
        ("AI-Powered Retrieval", "Leverage advanced AI to quickly and accurately find the documents you need."),
        ("Secure Collaboration", "Collaborate with confidence, knowing your data is safeguarded."),
        ("Customizable Workflows", "Tailor workflows to fit your unique needs and enhance efficiency."),
        ("Continuous Updates", "Stay ahead with regular updates and the latest AI advancements."),
        ("24/7 Support", "Access expert support whenever you need it, ensuring smooth operations.")
    ]
    for title, desc in features:
        st.markdown(f"<div class='feature-box'><h3>{title}</h3><p>{desc}</p></div>", unsafe_allow_html=True)

    # By the Numbers
    st.markdown("## By the Numbers")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Users Worldwide", "500k+")
    with col2:
        st.metric("Documents Processed", "10M+")
    with col3:
        st.metric("Data Security", "99.9%")

    # How It Works
    st.markdown("## How It Works")
    steps = [
        ("01 Upload Your Documents", "Securely upload your documents to the IntelliRetrieve platform."),
        ("02 Retrieve with AI", "Use our AI-powered tools to quickly find the information you need."),
        ("03 Collaborate Securely", "Share and collaborate on documents with confidence, knowing your data is protected.")
    ]
    for step, desc in steps:
        st.markdown(f"<h3>{step}</h3><p>{desc}</p>", unsafe_allow_html=True)

    # Testimonials
    st.markdown("## What Our Users Say")
    st.write(
        '"IntelliRetrieve has revolutionized how we handle documents. The privacy features are unmatched, and the AI retrieval is incredibly accurate." - Sarah Johnson, CTO of InnovateTech')
    st.write(
        '"Our workflows have never been smoother. IntelliRetrieve\'s AI tools have saved us countless hours, and the security is top-notch." - Michael Lee, CEO of SecureSolutions')

    # Call to Action
    st.markdown("## Ready to Transform Your Workflow?")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Sign Up")
    with col2:
        st.button("Learn More")

    st.markdown("</div>", unsafe_allow_html=True)

# About Us Page
def about_us_page():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.title("About IntelliRetrieve")
    st.subheader("Privacy-Focused AI for Smarter Document Retrieval")

    # Intro
    st.markdown("## Empower Your Workflow with Secure AI Document Retrieval")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Document Retrieval Accuracy", "99.8%")
    with col2:
        st.metric("Average Response Time", "0.2s")
    with col3:
        st.metric("Data Privacy Guaranteed", "100%")

    # Team
    st.markdown("## Meet the Innovators Behind IntelliRetrieve")
    team = [
        ("Dr. Emily Zhang", "Chief AI Scientist"),
        ("Michael O'Connor", "Head of Privacy Engineering"),
        ("Sarah Patel", "Product Strategy Lead"),
        ("David Kim", "Chief Technology Officer")
    ]
    for name, role in team:
        st.markdown(f"<div class='feature-box'><h3>{name}</h3><p>{role}</p></div>", unsafe_allow_html=True)

    # Core Principles
    st.markdown("## Our Core Principles")
    st.write("At IntelliRetrieve, we believe that innovation should never compromise privacy. Our AI-powered solutions are designed to respect and protect user data at every step.")
    st.write("We're committed to building trust through transparency, ensuring our users understand exactly how their data is processed and protected.")

    # Stats
    st.markdown("## By the Numbers")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Founded", "2022")
    with col2:
        st.metric("Protected Documents", "10M+")
    with col3:
        st.metric("Global Users", "50K+")
    with col4:
        st.metric("Privacy Certifications", "3")

    # Technological Expertise
    st.markdown("## Our Technological Expertise")
    expertise = [
        ("Natural Language Processing", "Advanced NLP techniques for precise document understanding."),
        ("Data Encryption", "State-of-the-art encryption methods to ensure complete data security."),
        ("Machine Learning", "Sophisticated ML models that continuously improve retrieval accuracy."),
        ("Privacy Compliance", "Expertise in GDPR, CCPA, and other global privacy regulations.")
    ]
    for title, desc in expertise:
        st.markdown(f"<div class='feature-box'><h3>{title}</h3><p>{desc}</p></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Doc Rag System Page
def doc_rag_system_page():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.title("Welcome to the Doc Rag System")
    st.subheader("Experience the future of document processing")

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Documents Processed", "1M+")
    with col2:
        st.metric("Supported Formats", "20+")
    with col3:
        st.metric("Response Time", "<1s")
    with col4:
        st.metric("Data Security", "Military-grade")

    # How It Works
    st.markdown("## How the Doc Rag System Works")
    steps = [
        ("Step 1: Upload Documents", "Easily upload your documents in various formats."),
        ("Step 2: AI Processing", "Our AI analyzes and extracts key information with precision."),
        ("Step 3: Retrieve & Answer", "Quickly access processed documents and get accurate answers.")
    ]
    for step, desc in steps:
        st.markdown(f"<h3>{step}</h3><p>{desc}</p>", unsafe_allow_html=True)

    # Supported Formats
    st.markdown("## Supported Document Formats")
    formats = ["PDF", "Word", "Excel", "Text"]
    for fmt in formats:
        st.markdown(f"<div class='feature-box'><h3>{fmt}</h3><p>Process and analyze {fmt} documents with ease.</p></div>", unsafe_allow_html=True)

    # AI Capabilities
    st.markdown("## AI Capabilities")
    capabilities = [
        ("Natural Language Processing", "Understand and process human language with advanced NLP."),
        ("Data Extraction", "Accurately extract key information from complex documents."),
        ("Data Security", "Ensure the highest level of data protection with military-grade encryption.")
    ]
    for title, desc in capabilities:
        st.markdown(f"<div class='feature-box'><h3>{title}</h3><p>{desc}</p></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Contact Us Page
def contact_us_page():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.title("Contact Us")
    st.write("Ready to Enhance Your Document Workflow?")
    st.write("Monday-Friday, 8:00 am to 7:00 pm")
    st.write("Send Us Your Inquiry: *contact@intelliretrieve.com*")

    # Social Media Links
    st.markdown("## Follow Us")
    socials = ["LinkedIn", "Twitter", "GitHub", "Medium", "YouTube", "Facebook"]
    for social in socials:
        st.write(f"- {social}")

    st.markdown("</div>", unsafe_allow_html=True)

# Footer
def footer():
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        © 2024 IntelliRetrieve. All Rights Reserved. Privacy-focused AI-powered document retrieval and answering system.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    footer()