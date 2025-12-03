from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "PDP Assessment Backend"}), 200

@app.route('/process-assessment', methods=['POST'])
def process_assessment():
    try:
        data = request.json
        
        required_fields = ['client_name', 'assessment_date', 'responses', 'api_key']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        responses_text = ""
        for q_num, response in data['responses'].items():
            responses_text += f"QUESTION {q_num}: {response}\n\n"
        
        prompt = f"""You are analyzing a STAGES developmental assessment.

Client: {data['client_name']}
Date: {data['assessment_date']}

RESPONSES:
{responses_text}

Analyze these responses and return a JSON object with:
{{
    "overallStage": "4.5",
    "stageName": "Strategist",
    "confidence": "High",
    "distribution": {{"3.5": 10, "4.0": 25, "4.5": 45, "5.0": 20}},
    "keyInsights": ["insight 1", "insight 2", "insight 3"],
    "practiceRecommendation": {{
        "layer1": "Professional support recommendation",
        "layer2": "Daily practice recommendation", 
        "layer3": "Weekly integration recommendation"
    }},
    "part6_practiceplan": {{
        "dailyPractice": "Specific daily practice with duration",
        "weeklyPractice": "Specific weekly practice",
        "implementation": "6-month implementation timeline"
    }},
    "part7_schedule": {{
        "weeklySchedule": "Complete weekly schedule",
        "timeInvestment": "Total hours per week"
    }},
    "part8_toolkit": {{
        "journalingPrompts": ["prompt 1", "prompt 2"],
        "progressIndicators": ["indicator 1", "indicator 2"],
        "resources": ["resource 1", "resource 2"]
    }}
}}

Return ONLY valid JSON, no other text."""

        client = anthropic.Anthropic(api_key=data['api_key'])
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        scoring_data = json.loads(response_text)
        scoring_data['processed'] = True
        scoring_data['timestamp'] = datetime.utcnow().isoformat()
        
        return jsonify({"success": True, "scoring": scoring_data}), 200
        
    except json.JSONDecodeError as e:
        return jsonify({"error": "Failed to parse response", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
