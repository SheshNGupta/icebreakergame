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
        "question": "Which planet is known as the Red Planet?",
        "options": ["Mars", "Venus", "Jupiter", "Mercury"],
        "answer": "Mars",
        "image": "https://upload.wikimedia.org/wikipedia/commons/0/02/OSIRIS_Mars_true_color.jpg"
    },
    {
        "question": "What is the primary purpose of the Sarbanes-Oxley Act (SOX)?",
        "options": ["Regulate healthcare", "Ensure corporate financial transparency", "Manage environmental policies", "Oversee international trade"],
        "answer": "Ensure corporate financial transparency",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSZhKAVGgaRdRFUv2pHxOCMBY-WRZ_RFec34w&s"
    },
    {
        "question": "Which organ in the human body is responsible for filtering blood?",
        "options": ["Liver", "Kidney", "Lungs", "Heart"],
        "answer": "Kidney",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgCGUkT5TXQ8VM7aOUHIipJEXS6mTZYcm_pA&s"
    },
    {
        "question": "Which country gifted the Statue of Liberty to the United States?",
        "options": ["France", "Spain", "Italy", "Germany"],
        "answer": "France",
        "image": "https://upload.wikimedia.org/wikipedia/commons/a/a1/Statue_of_Liberty_7.jpg"
    },
    {
        "question": "What does the Basel III framework primarily regulate?",
        "options": ["Banking capital and liquidity standards", "Trade tariffs", "Cryptocurrency exchanges", "Corporate taxation"],
        "answer": "Banking capital and liquidity standards",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGZL8LsI76Z9J43aIyoFHKtnJqlvULrDYZPg&s"
    },
    {
        "question": "Who painted the Mona Lisa?",
        "options": ["Vincent van Gogh", "Leonardo da Vinci", "Pablo Picasso", "Michelangelo"],
        "answer": "Leonardo da Vinci",
        "image": "https://upload.wikimedia.org/wikipedia/commons/6/6a/Mona_Lisa.jpg"
    },
    {
        "question": "Which gas do humans primarily exhale after breathing?",
        "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"],
        "answer": "Carbon Dioxide",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCuNw_aEbq_KIZmwm3qj2v-6Ncp5-W8uh39g&s"
    },
    {
        "question": "What is the world’s largest ocean?",
        "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
        "answer": "Pacific Ocean",
        "image": "https://upload.wikimedia.org/wikipedia/commons/0/05/Pacific_Ocean_-_en.png"
    },
    {
        "question": "Which financial law requires institutions to report large cash transactions to prevent money laundering?",
        "options": ["Bank Secrecy Act", "SOX", "GDPR", "FCPA"],
        "answer": "Bank Secrecy Act",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTQi1RCr5WbO_t1YS1b4Z0ci0biO6d-bGXwZw&s"
    },
    {
        "question": "Which is the largest mammal in the world?",
        "options": ["African Elephant", "Blue Whale", "Giraffe", "Humpback Whale"],
        "answer": "Blue Whale",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShn5CVb4UJIdJE8nGFpvcBXJ9vPfAIRIV03g&s"
    },
    {
        "question": "What is the chemical symbol for gold?",
        "options": ["Au", "Ag", "Gd", "Go"],
        "answer": "Au",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSGJSSF-L49T0YwP761T-awID7VW_KQjpCrYw&s"
    },
    {
        "question": "Which financial regulation focuses on preventing bribery of foreign officials?",
        "options": ["FCPA", "AML", "Dodd-Frank", "GDPR"],
        "answer": "FCPA",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ_GKEGDOtC4SAlag3Gcoq8JIrN7oJ2VNnnDw&s"
    },
    {
        "question": "What is the hardest natural substance on Earth?",
        "options": ["Steel", "Diamond", "Quartz", "Granite"],
        "answer": "Diamond",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhuCj1gq-LSSGO-zYvwAuj5p-0qnkbyc5ljw&s"
    },
    {
        "question": "Which U.S. agency enforces securities laws and protects investors?",
        "options": ["SEC", "FINRA", "FDIC", "OCC"],
        "answer": "SEC",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTXopHWQDjXaLrPwdobwwFJzsxt18uf6-QeQ&s"
    },
    {
        "question": "Which natural disaster is measured using the Richter scale?",
        "options": ["Hurricanes", "Earthquakes", "Tornadoes", "Floods"],
        "answer": "Earthquakes",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT5yLsO-TqA0a1opiyeJ1L8q1oDtY5rh2MbtA&s"
    }
]

def start_new_question():
    global current_question, time_started, question_index
    if question_index < len(game_questions):
        current_question = game_questions[question_index]
        time_started = time.time()
        socketio.emit("new_question", current_question)
        threading.Timer(20, show_scores).start()  # Show scores after 60 sec

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
    score = max(100 - int(elapsed_time), 80)  # Min 80 points for answering

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
