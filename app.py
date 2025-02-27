import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for scores and players
players = {}
current_question = None
time_started = None
question_index = 0
game_started = False

game_questions = [
    {
        "question": "Which of the following is a key principle of compliance programs in organizations?",
        "options": ["Encouraging workplace gossip", "Ignoring regulatory updates", "Promoting ethical behavior and accountability", "Avoiding transparency in reporting"],
        "answer": "Promoting ethical behavior and accountability",
        "image": "https://www.eqs.com/assets/2021/03/EQS-Blog_Compliance-Management-1024x576.jpg"
    },
    
    {
        "question": "What is the capital of Canada?",
        "options": ["Toronto", "Vancouver", "Ottawa", "Montreal"],
        "answer": "Ottawa",
        "image": "https://upload.wikimedia.org/wikipedia/commons/2/22/Parliament-Ottawa.jpg"
    },
    {
        "question": "Which of the following laws governs data privacy and protection in the European Union?",
        "options": ["HIPAA", "GDPR", "CCPA", "PCI-DSS"],
        "answer": "GDPR",
        "image": "https://www.enzuzo.com/hubfs/%E2%80%9CData-Privacy%E2%80%9D-M-2.jpg"
    },
    
    {
        "question": "Who developed the theory of relativity?",
        "options": ["Isaac Newton", "Albert Einstein", "Galileo Galilei", "Nikola Tesla"],
        "answer": "Albert Einstein",
        "image": "https://www.crystalinks.com/isaac-newton2.jpg"
    },
    {
        "question": "What does PCI-DSS ensure compliance for?",
        "options": ["Handling of customer health records", "Secure processing of credit card transactions", "Anti-money laundering policies", "Corporate tax regulations"],
        "answer": "Secure processing of credit card transactions",
        "image": "https://www.paynetworx.co.uk/wp-content/uploads/2023/03/paynetworx-1.png"
    },
    
    {
        "question": "Which element has the chemical symbol ‘K’?",
        "options": ["Krypton", "Potassium", "Calcium", "Magnesium"],
        "answer": "Potassium",
        "image": "https://content.health.harvard.edu/wp-content/uploads/2023/09/c0256936-e37b-4d4d-b244-5420273e79f7.jpg"
    },
    {
        "question": "What does HIPAA primarily regulate?",
        "options": ["Financial transactions", "Health information privacy", "Workplace safety", "Environmental protection"],
        "answer": "Health information privacy",
        "image": "https://compliancy-group.com/wp-content/uploads/2023/09/hipaa-compliance-1.png"
    },
    
    {
        "question": "What year did the first human land on the Moon?",
        "options": ["1965", "1969", "1972", "1959"],
        "answer": "1969",
        "image": "https://d31nhj1t453igc.cloudfront.net/cloudinary/2022/Apr/08/8y8xQ0LrSBPfDOQFjbpC.jpg"
    },
    {
        "question": "Which country is the largest producer of coffee?",
        "options": ["Vietnam", "Colombia", "Brazil", "Ethiopia"],
        "answer": "Brazil",
        "image": "https://upload.wikimedia.org/wikipedia/commons/e/e4/Latte_and_dark_coffee.jpg"
    },
    {
        "question": "What is the main goal of Anti-Money Laundering (AML) regulations?",
        "options": ["Encouraging cryptocurrency use", "Preventing financial fraud and illegal transactions", "Reducing corporate taxes", "Increasing government spending"],
        "answer": "Preventing financial fraud and illegal transactions",
        "image": "https://i0.wp.com/authme.com/wp-content/uploads/2024/07/shutterstock_2438582797.jpg"
    }
]

def start_new_question():
    global current_question, time_started, question_index
    if question_index < len(game_questions):
        current_question = game_questions[question_index]
        time_started = time.time()
        socketio.emit("new_question", current_question)
        threading.Timer(30, show_scores).start()  # Show scores after 60 sec

    else:
        #socketio.emit("game_over", {"message": "Game Over!"})
        handle_game_over()  # Call game over function

def show_scores():
    global question_index
    socketio.emit("show_scores", players)
    question_index += 1
    if (question_index==len(game_questions)):
        handle_game_over()
    else:
        threading.Timer(5, start_new_question).start()  # Show scores for 30 sec

@app.route('/')
def index():
    return render_template("index.html")

@socketio.on("join")
def handle_join(data):
    username = data["username"]
    if username not in players:
        players[username] = 0
        print(username+" has joined!")  # Debugging output
    if len(players) == 1:
        emit("assign_host",{"username": username},broadcast=True)
    emit("player_joined", {"players": list(players.keys())}, broadcast=True)

@socketio.on("start_game")
def handle_start_game():
    global game_started
    if not game_started:
        game_started = True
        print("Game has started!")  # Debugging output
        start_new_question()

@socketio.on("answer")
def handle_answer(data):
    global time_started
    username = data["username"]
    answer = data["answer"]
    
    if current_question is None:
        return
    
    elapsed_time = time.time() - time_started
    score = max(100 - int(elapsed_time), 70)  # Min 70 points for answering

    if answer == current_question["answer"]:
        players[username] += score
    #emit("update_scores", players, broadcast=True)

@socketio.on("game_over")
def handle_game_over():
    if players:
        # Determine the winner (highest score)
        winner = max(players, key=players.get)
        final_scores = {"scores": players, "winner": winner}
    else:
        final_scores = {"scores": {}, "winner": "No players"}

    # Emit game over event with the winner's name
    global game_started
    game_started = False
    socketio.emit("game_over", final_scores)

@socketio.on("restart_game")
def handle_restart_game():
    global game_started, players, question_index
    game_started = False
    question_index = 0
    players = {}  # Reset players

    emit("game_reset", broadcast=True)  # Notify clients to reset their UI

if __name__ == '__main__':
    socketio.run(app, host = '0.0.0.0',debug=True)
