import streamlit as st
import requests
import base64


FASTAPI_URL = "http://152.70.74.85:5001/chat"

def check_data_type(data_type):
    if data_type == "Brand Led Analysis":
        return "instagram"
    elif data_type == "Search Trends":
        return "trends"
    elif data_type == "Consumer Led Analysis":
        return "cla"
    else:
        return None

def chat(data_type):
    chat_container = st.container()
    messages = chat_container.container(border=True)

    # Input bar at the bottom
    user_input = st.chat_input(placeholder="e.g., What are the most searched real estate themes in 2024?")

    if user_input:
        # Display user message
        messages.chat_message("human").write("You:")
        messages.write(user_input)

        if user_input.strip() == "":
            st.warning("Please enter a message.")
        else:

            payload = {
                "message": user_input,
                "data": data_type
            }


        with st.spinner("SixthAI is thinking..."):
            try:
                response = requests.post(FASTAPI_URL, json=payload)
                response.raise_for_status()
                result = response.json()


                # Show AI message
                messages.chat_message("ai").write("SixthAI:")
                messages.write(result.get("message", ""))


                image_data = result.get("image")
                if image_data:

                    messages.chat_message("ai").write("SixthAI:")
                    messages.image(image_data, caption="Generated Image", use_column_width=True)


                    img_base64 = image_data.split(",")[1]
                    img_bytes = base64.b64decode(img_base64)
                    st.download_button(
                        label="Download Image",
                        data=img_bytes,
                        file_name="plot.jpg",
                        mime="image/jpeg"
                    )
            except Exception as e:
                st.error(f"Error: {e}")
