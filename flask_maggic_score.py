from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/calculate-risk', methods=['POST'])
def calculate_risk():
    # Λήψη δεδομένων από το front-end
    data = request.json
    score = data.get('score')

    if score is None:
        return jsonify({"error": "Score is required"}), 400

    # Υπολογισμός κινδύνου
    if score < 20:
        risk = "Low Risk"
    elif score < 30:
        risk = "Medium Risk"
    else:
        risk = "High Risk"

    # Επιστροφή αποτελέσματος
    return jsonify({"risk": risk})

if __name__ == '__main__':
    app.run(debug=True)
