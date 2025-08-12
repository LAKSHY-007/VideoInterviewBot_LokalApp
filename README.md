# Interview Bot - AI-Powered Interview Assistant 
## Lakshya Pendharkar



An intelligent interview bot that conducts automated interviews, records responses (text or video), and provides comprehensive evaluations. Powered by Google Gemini and Streamlit.


## Technology Stack

- **Backend:** Python 3.9+
- **Web Framework:** Streamlit
- **AI Integration:** Google Gemini API
- **Video Processing:** WebRTC, PyAV
- **Session Management:** UUID-based tracking


## Features

- Dynamic Question Generation: AI-generated questions tailored to job descriptions
- Multi-modal Responses: Answer via text or video recording
- Real-time Progress Tracking: Visual indicator of interview completion
- Comprehensive Evaluation: Detailed feedback on your performance
- Session Management: Automatic saving of interview data
- Responsive UI: Clean, intuitive interface with chat-style interaction

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/interview-bot.git
   cd interview-bot
   ```

## Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Interface Walkthrough

### Job Information Section
- Enter job title and description
- Select number of questions
- Generate customized questions

### Interview Interface
- Questions appear in chat format
- Choose text or video response for each question
- Progress bar tracks completion

### Evaluation
- Automatic generation after final question
- Detailed feedback on your responses
- Suggestions for improvement


## Project Structure

interview-bot/
├── app.py # Main application logic
├── utils.py # Helper functions for AI completions
├── config.py # Configuration parameters
├── requirements.txt # Dependencies
└── interview_data/ # Directory for saved interviews
