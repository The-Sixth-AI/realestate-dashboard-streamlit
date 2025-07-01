import streamlit as st
import requests
import base64
from datetime import datetime

FASTAPI_URL = "http://152.70.74.85:5001/chat"

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def check_data_type(data_type):
    if data_type == "Brand Led Analysis":
        return "brand led analysis"
    elif data_type == "Search Trends":
        return "trends"
    elif data_type == "Consumer Led Analysis":
        return "cla"
    else:
        return None

def chat(data_type):
    print(f"Data type: {data_type}")

    key = f"chat_history_{data_type}"

    if key not in st.session_state:
        st.session_state[key] = []

    # if "chat_history" not in st.session_state:
    #     st.session_state.chat_history = []

    # Main chat interface
    chat_container = st.container()

    # Display chat history
    with chat_container:
        for i, chat in enumerate(st.session_state[key]):
            # User message
            with st.chat_message("user"):
                st.write(f"**Data Source:** {chat['data_type']}")
                st.write(chat["user_message"])
            
            # Bot response
            with st.chat_message("assistant"):
                st.write(chat["bot_response"])
                
                # Display image if available
                if chat.get("image_data"):
                    st.image(chat["image_data"], caption="Generated Plot")
                    
                    # Download button for image
                    try:
                        img_base64 = chat["image_data"].split(",")[1]
                        img_bytes = base64.b64decode(img_base64)
                        st.download_button(
                            label="📥 Download Image",
                            data=img_bytes,
                            file_name=f"plot_{i+1}.jpg",
                            mime="image/jpeg",
                            key=f"download_img_{i}"
                        )
                    except:
                        pass
                
                # Display PDF download if available
                if chat.get("pdf_path") and chat["pdf_path"].strip():
                    try:
                        # Fetch PDF from the server
                        pdf_response = requests.get(chat["pdf_path"])
                        pdf_response.raise_for_status()
                        
                        st.success("📄 PDF Report Available")
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_response.content,
                            file_name=f"report_{i+1}.pdf",
                            mime="application/pdf",
                            key=f"download_pdf_{i}"
                        )
                    except Exception as pdf_error:
                        st.warning(f"PDF no longer available: {pdf_error}")

    # Chat input at the bottom
    user_input = st.chat_input(placeholder="e.g., What are the most searched real estate themes in 2024?")

    if user_input:
        # Add user message to chat history immediately
        user_chat = {
            "user_message": user_input,
            "data_type": data_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Display user message
        with st.chat_message("user"):
            # st.write(f"**Data Source:** {data_type}")
            st.write(user_input)
        
        # Show typing indicator
        with st.chat_message("assistant"):
            with st.spinner("SixthAI is thinking..."):
                try:
                    # Prepare payload
                    payload = {
                        "message": user_input,
                        "data": data_type
                    }
                    
                    # Make API request
                    response = requests.post(FASTAPI_URL, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    
                    # Extract response data
                    bot_response = result.get("message", "")
                    image_data = result.get("image")
                    pdf_path = result.get("pdf_path")
                    
                    # Display bot response
                    st.write(bot_response)
                    
                    # Display image if available
                    if image_data:
                        st.image(image_data, caption="Generated Plot")
                        
                        # Download button for image
                        try:
                            img_base64 = image_data.split(",")[1]
                            img_bytes = base64.b64decode(img_base64)
                            st.download_button(
                                label="📥 Download Image",
                                data=img_bytes,
                                file_name="plot.jpg",
                                mime="image/jpeg",
                                key=f"download_current_img"
                            )
                        except:
                            pass
                    
                    # Display PDF download if available
                    if pdf_path and pdf_path.strip():
                        try:
                            # Fetch PDF from the server
                            pdf_response = requests.get(pdf_path)
                            pdf_response.raise_for_status()
                            
                            st.success("📄 PDF Report Generated!")
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_response.content,
                                file_name="report.pdf",
                                mime="application/pdf",
                                key=f"download_current_pdf"
                            )
                        except Exception as pdf_error:
                            st.warning(f"PDF download failed: {pdf_error}")
                    
                    # Add complete interaction to chat history
                    user_chat.update({
                        "bot_response": bot_response,
                        "image_data": image_data,
                        "pdf_path": pdf_path
                    })
                    
                    st.session_state[key].append(user_chat)
                    
                except Exception as e:
                    error_message = f"Error: {e}"
                    st.error(error_message)
                    
                    # Add error to chat history
                    user_chat.update({
                        "bot_response": error_message,
                        "image_data": None,
                        "pdf_path": None
                    })
                    
                    st.session_state[key].append(user_chat)

    # Custom styling for better appearance
    st.markdown("""
    <style>
        .stChatMessage {
            margin-bottom: 1rem;
        }
        
        /* Remove white border and background from chat input */
        div[data-testid="stChatInput"] {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }
        
        div[data-testid="stChatInput"] > div {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }
        
        /* Style the actual input field */
        .stChatInput input {
            background-color: #f8f9fa !important;
            border: 2px solid #e9ecef !important;
            border-radius: 12px !important;
            font-size: 18px !important;
            font-weight: 500 !important;
            height: auto !important;
            min-height: 56px !important;
            padding: 16px 24px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
            transition: all 0.2s ease !important;
            line-height: 1.5 !important;
            vertical-align: middle !important;
            display: flex !important;
            align-items: center !important;
        }
        
        /* Input focus state */
        .stChatInput input:focus {
            border-color: #007bff !important;
            box-shadow: 0 2px 12px rgba(0,123,255,0.15) !important;
            outline: none !important;
        }
        
        /* Placeholder text styling */
        .stChatInput input::placeholder {
            color: #6c757d !important;
            font-weight: 500 !important;
            font-size: 17px !important;
        }
        
        /* Hide Streamlit menu and footer for cleaner look */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)