import uuid
import streamlit as st
from streamlit_chat import message
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils import get_completion, get_questions
from config import Parameters


class InterviewBot:
    def __init__(self) -> None:
        self._init_session_state()
        st.set_page_config(
            page_title="Interview Bot",
            page_icon="💼",
            layout="wide"
        )

    def _init_session_state(self) -> None:
        defaults = {
            'questions': [],
            'answers': [],
            'interview_step': 0,
            'interview_complete': False,
            'evaluation': None,
            'role_data': None,
            'video_responses': {},
            'current_recording': None,
            'transcripts': {},
            'session_id': str(uuid.uuid4()),
            'start_time': datetime.now().isoformat()
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
        self.state = st.session_state

    def _generate_uuid(self) -> str:
        return str(uuid.uuid4())

    def prepare_interview(self) -> None:
        with st.expander("📝 Job Information", expanded=True):
            with st.form("job_form"):
                job_title = st.text_input("Job Title", value=Parameters.DEFAULT_JOB_TITLE)
                job_description = st.text_area(
                    "Job Description",
                    value=Parameters.DEFAULT_JOB_DESCRIPTION,
                    height=200
                )
                num_questions = st.slider(
                    "Number of Questions",
                    Parameters.MIN_QUESTIONS,
                    Parameters.MAX_QUESTIONS,
                    Parameters.DEFAULT_NUM_QUESTIONS
                )

                if st.form_submit_button("Generate Questions"):
                    self.state['role_data'] = {
                        'title': job_title,
                        'description': job_description
                    }
                    self._generate_questions(job_title, job_description, num_questions)
                    st.rerun()

    def _generate_questions(self, title: str, description: str, num_questions: int) -> None:
        prompt = Parameters.QUESTIONS_PROMPT.format(
            job_title=title,
            job_description=description,
            num_questions=num_questions
        )
        with st.spinner("Creating questions..."):
            try:
                response = get_completion(prompt)
                questions = get_questions(response)
                self.state['questions'] = [(q, self._generate_uuid()) for q in questions]
                self.state['interview_step'] = 0
                self.state['interview_complete'] = False
                self.state['evaluation'] = None
            except Exception as e:
                st.error(f"Could not generate questions: {str(e)}")
                self.state['questions'] = [
                    ("Error generating questions. Please try again.", str(uuid.uuid4()))
                ]

    def video_recorder(self, question_idx: int) -> Optional[WebRtcMode]:
        def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        return webrtc_streamer(
            key=f"video_{question_idx}",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": True},
            desired_playing_state=True
        )

    def get_answer(self, question_idx: int) -> None:
        st.subheader("Your Answer")
        response_type = st.radio(
            "Choose format:",
            ["Text", "Video"],
            key=f"response_type_{question_idx}"
        )

        if response_type == "Text":
            answer = st.text_area("Type here:", key=f"text_answer_{question_idx}", height=150)
        else:
            st.info("Please allow access to camera and microphone")
            video_ctx = self.video_recorder(question_idx)
            answer = "video_response" if video_ctx and video_ctx.state.playing else None

        if st.button("Submit", key=f"submit_{question_idx}"):
            if answer:
                self.state['answers'].append((answer, self._generate_uuid()))
                self.state['interview_step'] += 1
                if response_type == "Video":
                    self.state['video_responses'][question_idx] = {
                        'timestamp': datetime.now().isoformat(),
                        'type': 'video'
                    }
                st.rerun()

    def display_progress(self) -> None:
        if len(self.state['questions']) > 0:
            progress = self.state['interview_step'] / len(self.state['questions'])
            st.progress(progress)
            st.caption(
                f"Question {self.state['interview_step'] + 1} of {len(self.state['questions'])}  "
                f"|  Session ID: {self.state['session_id']}"
            )

    def display_qa_history(self) -> None:
        with st.expander("📜 Previous Q&A", expanded=False):
            for i in range(self.state['interview_step']):
                q_text, q_key = self.state['questions'][i]
                message(q_text, key=q_key)
                if i < len(self.state['answers']):
                    a_text, a_key = self.state['answers'][i]
                    if isinstance(a_text, str) and a_text.startswith("video_response"):
                        st.video("placeholder.mp4")
                        message("(Video response)", is_user=True, key=a_key)
                    else:
                        message(a_text, is_user=True, key=a_key)

    def evaluate_interview(self) -> None:
        if not self.state['evaluation'] and self.state['role_data']:
            with st.spinner("Evaluating..."):
                interview_text = "\n".join(
                    f"Q: {q}\nA: {a}\n"
                    for (q, _), (a, _) in zip(self.state['questions'], self.state['answers'])
                )
                prompt = Parameters.EVALUATION_PROMPT.format(
                    job_title=self.state['role_data']['title'],
                    job_description=self.state['role_data']['description'],
                    interview_text=interview_text
                )
                try:
                    self.state['evaluation'] = get_completion(prompt)
                    self.state['interview_complete'] = True
                    self._save_interview_data()
                except Exception as e:
                    st.error(f"Evaluation failed: {str(e)}")
                    self.state['evaluation'] = "Could not generate evaluation."

        if self.state['evaluation']:
            st.subheader("📊 Summary")
            st.markdown(self.state['evaluation'])

    def _save_interview_data(self) -> None:
        data = {
            'session_id': self.state['session_id'],
            'start_time': self.state['start_time'],
            'end_time': datetime.now().isoformat(),
            'role_data': self.state['role_data'],
            'questions': self.state['questions'],
            'answers': self.state['answers'],
            'evaluation': self.state['evaluation']
        }
        output_dir = Path("interview_data")
        output_dir.mkdir(exist_ok=True)
        filename = output_dir / f"interview_{self.state['session_id']}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def reset_interview(self) -> None:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    def execute_interview(self) -> None:
        if self.state['role_data']:
            st.header(f"Interview: {self.state['role_data']['title']}")

        if not self.state['questions']:
            self.prepare_interview()
            return

        self.display_progress()
        self.display_qa_history()

        if self.state['interview_step'] < len(self.state['questions']):
            current_q, q_key = self.state['questions'][self.state['interview_step']]
            message(current_q, key=q_key)
            self.get_answer(self.state['interview_step'])
        elif not self.state['interview_complete']:
            self.evaluate_interview()

        if self.state['questions'] and not self.state['interview_complete']:
            if st.button("🔄 Restart Interview"):
                self.reset_interview()


def main():
    st.title("💼 Interview Bot")
    st.markdown("""
        Conducts an automated interview and provides feedback at the end.
        Fill in job details, answer the questions, and get a summary.
    """)
    bot = InterviewBot()
    bot.execute_interview()
    st.markdown("---")
    st.caption("Interview Bot v2.0 | Powered by Google Gemini")


if __name__ == "__main__":
    main()
