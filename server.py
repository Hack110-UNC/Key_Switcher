from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta
import os
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)

def create_key_dict():
    key_dict = {}
    base_time = datetime(year=2025, month=4, day=5, hour=10, minute=0, second=0)
    for i in range(36):
        key_dict[base_time + timedelta(minutes=30 * i)] = f"OPENAIKEY_{i}"
    return key_dict

key_dict_ref = create_key_dict()
times = list(key_dict_ref.keys())

@app.route("/Add_user", methods=["POST"])
def add_user():
    data = request.json
    Name = data.get("Name")
    PID = data.get("PID")

    if not Name or not PID:
        return jsonify({"error": "Missing parameters"}), 400

    supabase.table("HACK110").insert({"user": Name, "pid": PID, "calls": 0}).execute()
    return jsonify({"message": "User added successfully"}), 201

@app.route("/Temp_Key", methods=["GET"])
def temp_key():
    PID = request.args.get("PID")

    if not PID:
        return jsonify({"error": "Missing PID"}), 400

    response = supabase.table("HACK110").select("calls").eq("pid", PID).execute()
    user_data = response.data

    if not user_data:
        return jsonify({"error": "User not found"}), 404

    current_calls = user_data[0]["calls"]

    for i in times:
        if datetime.now() >= i:
            supabase.table("HACK110").update({"calls": current_calls + 1}).eq("pid", PID).execute()
            return jsonify({"key": os.environ.get(key_dict_ref[i])})

    return jsonify({"error": "No available key"}), 400

@app.route("/Simple_Prompt", methods=["POST"])
def simple_prompt():
    data = request.json
    query = data.get("query")
    PID = data.get("PID")

    if not query or not PID:
        return jsonify({"error": "Missing parameters"}), 400

    response = supabase.table("HACK110").select("calls").eq("pid", PID).execute()
    user_data = response.data

    if not user_data:
        return jsonify({"error": "User not found"}), 404

    current_calls = user_data[0]["calls"]
    supabase.table("HACK110").update({"calls": current_calls + 1}).eq("pid", PID).execute()

    client = OpenAI(api_key=os.environ.get("PROXY_KEY"))
    openai_response = client.responses.create(
        model="gpt-4o",
        input=query
    )

    return jsonify({"response": openai_response}), 200

if __name__ == "__main__":
    app.run(debug=True)
