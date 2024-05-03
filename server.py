import streamlit as st
from hackathon.csp import GCPCSP
from html_template import *

MESSAGE_HISTORY_LENGTH = 10


class Server():
    def __init__(self):
        self.csp = GCPCSP(embeddings='gcp', chat='gcp', stt='gcp')

    def main(self):
        st.set_page_config(page_title="Chat-ESG", page_icon=":teacher:", layout="wide")
        st.image("tw.png", width=200)
        st.title("Google AI Hackathon Submission")
        st.header("Talk to Abby, Your Personal Addiction Issues Counselor")

        if 'conversation' not in st.session_state:
            st.session_state.conversation = []
        if 'history' not in st.session_state:
            st.session_state.history = []
        if 'state' not in st.session_state:
            st.session_state.state = "started"

        if 'reset_input' in st.session_state and st.session_state.reset_input:
            st.session_state.question = ""
            st.session_state.reset_input = False

        user_question = st.text_input("Type your question and press enter:", key="question")

        if st.button("Send"):
            if user_question:
                st.session_state.conversation.append(f"You: {user_question}\n")

                if len(st.session_state.history) >= MESSAGE_HISTORY_LENGTH:
                    active_history = st.session_state.history[-MESSAGE_HISTORY_LENGTH:]
                    st.session_state.history = st.session_state.history[:-MESSAGE_HISTORY_LENGTH]
                else:
                    active_history = st.session_state.history.copy()
                    st.session_state.history = []

                response, updated_history, updated_state = self.csp.start_conversation(user_question, active_history, st.session_state.state)
                st.session_state.conversation.append(f"Abby: {response}\n")

                st.session_state.history = st.session_state.history + updated_history
                st.session_state.state = updated_state

        for message in reversed(st.session_state.conversation):
            st.write(message)

if __name__ == '__main__':
    Server().main()
