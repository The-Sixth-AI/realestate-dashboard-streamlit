import streamlit as st
import requests
import base64
from datetime import datetime

FASTAPI_URL = "http://152.70.74.85:5001/chat"

# Initialize chat history if not present
def get_chat_key(data_type):
    return f"chat_history_{data_type}"

def chat(data_type):

    key = get_chat_key(data_type)
    if key not in st.session_state:
        st.session_state[key] = []

    # Display chat history
    for i, chat in enumerate(st.session_state[key]):
        with st.chat_message("user"):
            st.write(f"**Data Source:** {chat['data_type']}")
            st.write(chat["user_message"])

        with st.chat_message("assistant"):
            st.write(chat["bot_response"])

            # Optional: Show image if present
            if chat.get("image_data"):
                st.image(chat["image_data"], caption="Generated Plot")
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

            # Optional: PDF download
            if chat.get("pdf_path") and chat["pdf_path"].strip():
                try:
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

    # --- Chat Input ---
    user_input = st.chat_input(placeholder="e.g., What are the most searched themes in 2024?")
    if user_input:
        user_chat = {
            "user_message": user_input,
            "data_type": data_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("SixthAI is thinking..."):
                try:
                    payload = {
                        "message": user_input,
                        "data": data_type
                    }
                    response = requests.post(FASTAPI_URL, json=payload)
                    response.raise_for_status()
                    result = response.json()

                    bot_response = result.get("message", "")
                    image_data = result.get("image")
                    pdf_path = result.get("pdf_path")

                    st.write(bot_response)

                    if image_data:
                        st.image(image_data, caption="Generated Plot")
                        try:
                            img_base64 = image_data.split(",")[1]
                            img_bytes = base64.b64decode(img_base64)
                            st.download_button(
                                label="📥 Download Image",
                                data=img_bytes,
                                file_name="plot.jpg",
                                mime="image/jpeg",
                                key="download_current_img"
                            )
                        except:
                            pass

                    if pdf_path and pdf_path.strip():
                        try:
                            pdf_response = requests.get(pdf_path)
                            pdf_response.raise_for_status()
                            st.success("📄 PDF Report Generated!")
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_response.content,
                                file_name="report.pdf",
                                mime="application/pdf",
                                key="download_current_pdf"
                            )
                        except Exception as pdf_error:
                            st.warning(f"PDF download failed: {pdf_error}")

                    user_chat.update({
                        "bot_response": bot_response,
                        "image_data": image_data,
                        "pdf_path": pdf_path
                    })
                    st.session_state[key].append(user_chat)

                except Exception as e:
                    error_message = f"Error: {e}"
                    st.error(error_message)
                    user_chat.update({
                        "bot_response": error_message,
                        "image_data": None,
                        "pdf_path": None
                    })
                    st.session_state[key].append(user_chat)
