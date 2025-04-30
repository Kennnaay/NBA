from flask import Flask, redirect, render_template, request, url_for, send_file 
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd
from flask import Response 
import io 
from io import BytesIO
import sqlite3 as sl
from sklearn.ensemble import HistGradientBoostingRegressor
import base64


app = Flask(__name__)

# ---------------- Load and prepare CSV ---------------- #
df = pd.read_csv("players.csv")
numeric_cols = df.select_dtypes(include="number").columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
df = df[df["Player"].notnull()] # Drop rows with missing names
df["Player"] = df["Player"].astype(str)
df = df[df["Year"] >= 2005] # Cap years
all_players = sorted(df["Player"].unique())

# ---------------- Training Function ---------------- #
def train_stat_model(stat):
    features = ["G", "MP", "FG%", "3P%", "FTA"] # Stats
    training_data = df[df["G"] > 15] # Cap seasons to seasons with over 15 games played
    X = training_data[features]

    # Different stat options
    if stat == "ppg":
        y = training_data["PTS"] / training_data["G"]
    elif stat == "apg":
        y = training_data["AST"] / training_data["G"]
    elif stat == "rpg":
        y = training_data["TRB"] / training_data["G"]
    else:
        raise ValueError("Unknown stat type")

    # Use HistGradientBoostingRegressor to train
    model = HistGradientBoostingRegressor(max_iter=200, max_depth=6, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    return model

# ---------------- Predictor Function ---------------- #
def predict_stat(model, player_name, stat, include_prediction=False):
    player_rows = df[df["Player"] == player_name]
    player_rows = player_rows[player_rows["G"] > 15] # Cap seasons to seasons with over 15 games played

    features = ["G", "MP", "FG%", "3P%", "FTA"]
    X = player_rows[features]

    # Different stat options
    if stat == "ppg":
        y = player_rows["PTS"] / player_rows["G"]
    elif stat == "apg":
        y = player_rows["AST"] / player_rows["G"]
    elif stat == "rpg":
        y = player_rows["TRB"] / player_rows["G"]
    else:
        raise ValueError("Unknown stat type")

    y_pred = model.predict(X).tolist()
    years = player_rows["Year"].tolist()

    # Create prediction
    if include_prediction:
        recent = player_rows.sort_values("Year").tail(3)
        if len(recent) > 0:
            avg_features = recent[features].mean().values.reshape(1, -1)
            future_stat = model.predict(avg_features)[0]
            future_year = recent["Year"].max() + 1

            y_pred.append(future_stat)
            years.append(future_year)

    return years, y_pred


# ---------------- Creating Figure Function ---------------- #
def create_stat_figure(years, predicted, player_name, stat_name, include_prediction=False):
    fig = Figure()
    ax = fig.subplots()
    ax.plot(years, predicted, marker='o')
    ax.set_title(f"{player_name} - Predicted {stat_name}")
    ax.set_xlabel("Year")
    ax.set_ylabel(stat_name)
    ax.set_xticks(sorted(set(int(y) for y in years)))

    if include_prediction:
        ax.plot(years[-1], predicted[-1], 'ro', label='Predicted Next Season')
        ax.legend()

    return fig



# ---------------- Home Page ---------------- #
@app.route("/")
def home():
    return render_template(
        "home.html",
        players=all_players,
        graph={
            "Points Per Game": "ppg",
            "Assists Per Game": "apg",
            "Rebounds Per Game": "rpg"
        },
        message="Predict stats",
        selected_graph=None,
        selected_player=None
    )

# ---------------- Stat Page ---------------- #
@app.route("/analyze_player", methods=["POST"])
def analyze_player():
    selected_player = request.form["player"]
    selected_graph = request.form["graph"]
    include_prediction = request.form.get("predict") == "true" # Check if checkbox was selected
    mode = request.form.get("mode", "season")  

    stat_map = {
        "Points Per Game": ("ppg", "Points Per Game"),
        "Assists Per Game": ("apg", "Assists Per Game"),
        "Rebounds Per Game": ("rpg", "Rebounds Per Game")
    }

    stat_code, stat_label = stat_map[selected_graph]
    model = train_stat_model(stat_code)

    # ============================ Season prediction ============================ #
    if mode == "season":
        years, predicted = predict_stat(model, selected_player, stat_code, include_prediction)
        fig = create_stat_figure(years, predicted, selected_player, stat_label, include_prediction)
    # ============================ Game prediction ============================ #
    elif mode == "game":
        # Grab the most recent healthy season
        player_rows = df[(df["Player"] == selected_player) & (df["G"] > 15)]
        latest = player_rows.sort_values("Year").iloc[-1]
        features = ["G", "MP", "FG%", "3P%", "FTA"]
        X = latest[features].values.reshape(1, -1)
        prediction = model.predict(X)[0]
        fig = create_game_prediction_figure(selected_player, stat_label, prediction)

    # Convert to image and render
    img = io.BytesIO()
    fig.savefig(img, format="png")
    img.seek(0)
    fig_data = base64.b64encode(img.getvalue()).decode()

    return render_template("stats.html", fig=fig_data, selected_player=selected_player)


def create_game_prediction_figure(player_name, stat_label, value):
    fig = Figure()
    ax = fig.subplots()
    ax.bar([stat_label], [value], color="orange")
    ax.set_title(f"{player_name} - Next Game Predicted {stat_label}")
    ax.set_ylim(0, max(value * 1.5, 10))  
    return fig


if __name__ == "__main__":
    app.run(debug=True)