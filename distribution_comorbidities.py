import matplotlib.pyplot as plt
from collections import Counter

def generate_comorbidities_chart(results, output_path="comorbidities_chart.png"):
    # Initialize counters for comorbidities
    comorbidities_count = Counter({
        "Diabetes": 0,
        "COPD": 0,
        "Smoker": 0
    })

    # Count comorbidities across patients
    for result in results:
        patient_data = result['patient_data']
        if patient_data['diabetes']:
            comorbidities_count["Diabetes"] += 1
        if patient_data['copd']:
            comorbidities_count["COPD"] += 1
        if patient_data['smoker']:
            comorbidities_count["Smoker"] += 1

    # Create a bar chart
    labels = list(comorbidities_count.keys())
    values = list(comorbidities_count.values())
    plt.figure(figsize=(8, 6))
    plt.bar(labels, values, color=['#4caf50', '#f44336', '#ff9800'])
    plt.title('Comorbidities Distribution')
    plt.ylabel('Number of Patients')
    plt.xlabel('Comorbidities')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return output_path
