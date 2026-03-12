import logging
import logging.config
import streamlit as st
from pair_engineer import PairEngineer

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "ERROR",
        "handlers": ["console"],
    },
})
logger = logging.getLogger(__name__)

SAMPLE_CODE = '''\
def create_user(name, email):
    db = connect_db()
    user = {"name": name, "email": email}
    db.insert(user)
    send_welcome_email(email)
    return user'''

st.set_page_config(page_title="AI Pair Engineer", page_icon="👨‍💻", layout="wide")

st.markdown(
    """
    <style>
    .stTextArea textarea { font-family: 'Courier New', monospace; font-size: 14px; }
    .stSpinner { text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI Pair Engineer")

st.markdown("**Try it out**, click below to load sample code, or paste your own.")
if st.button("📋 Load Sample Code"):
    st.session_state["code"] = SAMPLE_CODE

code = st.text_area(
    "Paste your Python code here",
    value=st.session_state.get("code", ""),
    height=300,
    placeholder="Paste your Python code here...",
)

context = st.text_input(
    "What are you trying to build? (optional)",
    placeholder="e.g. A REST API endpoint for user registration with email verification",
)

clicked = st.button("🔍 Pair Review", type="primary", use_container_width=True)
spinner_placeholder = st.empty()

if clicked:
    if not code.strip():
        st.warning("Paste some code first!")
    else:
        try:
            engineer = PairEngineer()
        except ValueError:
            logger.error("API key is not configured. Please set up your .env file.")
            st.error("Something went wrong. Please try again later.")
            st.stop()
        except Exception as e:
            logger.error("Failed to initialize PairEngineer: %s", e)
            st.error("Something went wrong. Please try again later.")
            st.stop()

        error_msg = None
        with spinner_placeholder.container():
            with st.spinner("🔍 Analyzing your code..."):
                try:
                    raise Exception("test")
                    result = engineer.analyze(code, context)
                except RuntimeError:
                    error_msg = "Our AI provider is currently experiencing capacity issues. Please try again in a few moments."
                except Exception as e:
                    logger.error("Unexpected error during analysis: %s", e)
                    error_msg = "Something went wrong. Please try again later."
        spinner_placeholder.empty()

        if error_msg:
            st.error(error_msg)
            st.stop()

        score = result.get("score", "N/A")
        st.metric("Code Quality Score", f"{score} / 10")

        with st.expander("🏗️ Design Analysis", expanded=True):
            st.markdown(result.get("design_analysis", ""))

        with st.expander("🧪 Generated Tests", expanded=True):
            st.markdown(result.get("generated_tests", ""))

        with st.expander("🔄 Refactored Code", expanded=True):
            st.markdown(result.get("refactored_code", ""))

        with st.expander("📝 Pair Engineer Notes", expanded=True):
            st.markdown(result.get("pair_notes", ""))
