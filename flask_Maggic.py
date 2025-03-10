# app.py
import os
import csv
import json
import pandas as pd
import PyPDF2
from flask import Flask, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Αντικατάστησε με ένα ασφαλές κλειδί
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt', 'json', 'xls', 'xlsx', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Δημιουργία του φακέλου uploads αν δεν υπάρχει
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_patient_data(patient_data):
    parsed_data = {}

    # Handle possible different key names with case insensitivity
    def get_value(keys, default):
        for key in keys:
            if key in patient_data:
                return patient_data[key]
        return default

    try:
        parsed_data['Patient No'] = int(get_value(['Patient No'], 1))
    except ValueError:
        parsed_data['Patient No'] = 1

    try:
        parsed_data['age'] = int(get_value(['age', 'Age'], 0))
    except ValueError:
        parsed_data['age'] = 0

    gender = get_value(['gender', 'Gender'], 'male').strip().lower()
    parsed_data['gender'] = gender if gender in ['male', 'female'] else 'male'

    nyha_str = get_value(['nyha_class', 'NYHA Class'], 'I').strip().upper()
    nyha_class_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
    parsed_data['nyha_class'] = nyha_class_map.get(nyha_str, 1)

    try:
        parsed_data['lvef'] = float(get_value(['lvef', 'LVEF'], 30))
    except ValueError:
        parsed_data['lvef'] = 30.0

    parsed_data['diabetes'] = get_value(['diabetes', 'Diabetes'], 'no').strip().lower() == 'yes'
    parsed_data['smoker'] = get_value(['smoker', 'Smoker'], 'no').strip().lower() == 'yes'
    parsed_data['copd'] = get_value(['copd', 'COPD'], 'no').strip().lower() == 'yes'

    try:
        parsed_data['sbp'] = int(get_value(['sbp', 'SBP'], 120))
    except ValueError:
        parsed_data['sbp'] = 120

    try:
        parsed_data['creatinine'] = float(get_value(['creatinine', 'Creatinine'], 1.0))
    except ValueError:
        parsed_data['creatinine'] = 1.0

    try:
        parsed_data['bmi'] = float(get_value(['bmi', 'BMI'], 24))
    except ValueError:
        parsed_data['bmi'] = 24.0

    parsed_data['beta_blocker'] = get_value(['beta_blocker', 'Beta Blocker'], 'no').strip().lower() == 'yes'
    parsed_data['ace_arb'] = get_value(['ace_arb', 'ACE_ARB', 'ACE Inhibitors or ARBs'], 'no').strip().lower() == 'yes'
    parsed_data['hf_duration_less_than_18_months'] = get_value(['hf_duration_less_than_18_months', 'HF Duration <18 months'], 'no').strip().lower() == 'yes'

    return parsed_data

def calculate_efr(ef):
    if ef == 0 or ef is None:
        return None
    elif ef < 20:
        return 7
    elif ef < 25:
        return 6
    elif ef < 30:
        return 5
    elif ef < 35:
        return 3
    elif ef < 40:
        return 2
    else:
        return 0

def calculate_efar(age, ef, _efr):
    if age < 18 or age > 110 or age is None:
        return None
    elif _efr is not None:
        if age < 55:
            return 0
        elif age < 60:
            if ef < 30:
                return 1
            elif ef < 40:
                return 2
            else:
                return 3
        elif age < 65:
            if ef < 30:
                return 2
            elif ef < 40:
                return 4
            else:
                return 5
        elif age < 70:
            if ef < 30:
                return 4
            elif ef < 40:
                return 6
            else:
                return 7
        elif age < 75:
            if ef < 30:
                return 6
            elif ef < 40:
                return 8
            else:
                return 9
        elif age < 80:
            if ef < 30:
                return 8
            elif ef < 40:
                return 10
            else:
                return 12
        else:
            if ef < 30:
                return 10
            elif ef < 40:
                return 13
            else:
                return 15
    else:
        return None

def calculate_sbpr(sbp, ef):
    if ef < 1 or ef > 95 or sbp < 50 or sbp > 250:
        return None
    else:
        if sbp < 110:
            if ef < 30:
                return 5
            elif ef < 40:
                return 3
            else:
                return 2
        elif sbp < 120:
            if ef < 30:
                return 4
            elif ef < 40:
                return 2
            else:
                return 1
        elif sbp < 130:
            if ef < 30:
                return 3
            elif ef < 40:
                return 1
            else:
                return 1
        elif sbp < 140:
            if ef < 30:
                return 2
            elif ef < 40:
                return 1
            else:
                return 0
        elif sbp < 150:
            if ef < 30:
                return 1
            else:
                return 0
        else:
            return 0

def calculate_bmir(bmi):
    if bmi < 10 or bmi > 50:
        return None
    else:
        if bmi < 15:
            return 6
        elif bmi < 20:
            return 5
        elif bmi < 25:
            return 3
        elif bmi < 30:
            return 2
        else:
            return 0

def calculate_crtnr(creatinine):
    if creatinine < 20 or creatinine > 1400:
        return None
    else:
        if creatinine < 90:
            return 0
        elif creatinine < 110:
            return 1
        elif creatinine < 130:
            return 2
        elif creatinine < 150:
            return 3
        elif creatinine < 170:
            return 4
        elif creatinine < 210:
            return 5
        elif creatinine < 250:
            return 6
        else:
            return 8

def calculate_gender_points(gender):
    if gender.lower() == 'female':
        return -3
    else:
        return 0

def calculate_nyha_points(nyha_class):
    nyha_points = {1: 0, 2: 3, 3: 6, 4: 8}
    return nyha_points.get(nyha_class, 0)

def calculate_smoker_points(smoker):
    return 1 if smoker else 0

def calculate_diabetes_points(diabetes):
    return 3 if diabetes else 0

def calculate_copd_points(copd):
    return 2 if copd else 0

def calculate_hf_points(hf_duration_less_than_18_months):
    return 2 if hf_duration_less_than_18_months else 0

def calculate_blocker_points(beta_blocker):
    return 5 if not beta_blocker else 0

def calculate_acei_points(acei_arb):
    return 3 if not acei_arb else 0

def calculate_maggic_score(patient_data):
    age = patient_data['age']
    lvef = patient_data['lvef']
    ef = lvef  # For consistency with TypeScript code
    sbp = patient_data['sbp']
    bmi = patient_data['bmi']
    creatinine_mg_dl = patient_data['creatinine']
    creatinine = creatinine_mg_dl * 88.4  # Convert mg/dL to μmol/L

    _efr = calculate_efr(ef)
    _efar = calculate_efar(age, ef, _efr)
    _sbpr = calculate_sbpr(sbp, ef)
    _bmir = calculate_bmir(bmi)
    _crtnr = calculate_crtnr(creatinine)

    gender_points = calculate_gender_points(patient_data['gender'])
    nyha_points = calculate_nyha_points(patient_data['nyha_class'])
    smoker_points = calculate_smoker_points(patient_data['smoker'])
    diabetes_points = calculate_diabetes_points(patient_data['diabetes'])
    copd_points = calculate_copd_points(patient_data['copd'])
    hf_points = calculate_hf_points(patient_data['hf_duration_less_than_18_months'])
    blocker_points = calculate_blocker_points(patient_data['beta_blocker'])
    acei_points = calculate_acei_points(patient_data['ace_arb'])

    # Sum all the points
    score = (
        (_efr or 0) +
        (_efar or 0) +
        (_sbpr or 0) +
        (_bmir or 0) +
        (_crtnr or 0) +
        gender_points +
        nyha_points +
        smoker_points +
        diabetes_points +
        copd_points +
        hf_points +
        blocker_points +
        acei_points
    )

    return score

def calculate_1_year_risk(score):
    risk1 = [
        0.015, 0.016, 0.018, 0.02, 0.022, 0.024, 0.027, 0.029, 0.032, 0.036,
        0.039, 0.043, 0.048, 0.052, 0.058, 0.063, 0.07, 0.077, 0.084, 0.093,
        0.102, 0.111, 0.122, 0.134, 0.147, 0.16, 0.175, 0.191, 0.209, 0.227,
        0.248, 0.269, 0.292, 0.316, 0.342, 0.369, 0.398, 0.427, 0.458, 0.49,
        0.523, 0.557, 0.591, 0.625, 0.659, 0.692, 0.725, 0.757, 0.787, 0.816,
        0.842
    ]
    if 0 <= score < len(risk1):
        return round(100 * risk1[score], 2)  # Percentage % with 2 decimal places
    return None

def calculate_3_year_risk(score):
    risk3 = [
        0.039, 0.043, 0.048, 0.052, 0.058, 0.063, 0.07, 0.077, 0.084, 0.092,
        0.102, 0.111, 0.122, 0.134, 0.146, 0.16, 0.175, 0.191, 0.209, 0.227,
        0.247, 0.269, 0.292, 0.316, 0.342, 0.369, 0.397, 0.427, 0.458, 0.49,
        0.523, 0.556, 0.59, 0.625, 0.658, 0.692, 0.725, 0.756, 0.787, 0.815,
        0.842, 0.866, 0.889, 0.908, 0.926, 0.941, 0.953, 0.964, 0.973, 0.98, 0.985
    ]
    if 0 <= score < len(risk3):
        return round(100 * risk3[score], 2)   # Percentage % with 2 decimal places
    return None

def get_risk_category(score):
    if score <= 20:
        return 'Low Risk'
    elif score <= 30:
        return 'Medium Risk'
    else:
        return 'High Risk'

def generate_health_message_patient(score):
    category = get_risk_category(score)
    if category == 'Low Risk':
        return """Your prognosis is favorable. By continuing your current treatment and healthy habits, you can maintain a good quality of life.
Recommendations:
- Continue to take your medication as directed by your doctor.
- Maintain a healthy lifestyle: a balanced diet, regular exercise suitable for you and avoid smoking.
- Keep your check-up appointments (e.g. every 6-12 months or as directed by your doctor) and report any changes in your symptoms in a timely manner."""
    elif category == 'Medium Risk':
        return """There is a moderate risk to your health. With certain adjustments, your prognosis can improve.
Recommendations:
- Talk to your doctor about possible changes to your treatment.
- Talk to your doctor about your treatment and discuss your options with your doctor."""
    else:  # High Risk
        return """The condition is serious, with increased risk to your health. However, measures can be taken to improve the situation.
Recommendations:
- Work closely with your doctor to adjust your treatment. Additional treatments or hospitalization may be needed.
- Adopt healthy habits more strictly: stop smoking, control your weight, manage other conditions such as diabetes."""

def generate_health_message_doctor(score):
    category = get_risk_category(score)
    if category == 'Low Risk':
        return """Recommendations:
- Continue with the current treatment.
- Regular check-ups are recommended to maintain the low level of risk.
- Encourage the patient to continue healthy habits and remain aware of his/her condition."""
    elif category == 'Medium Risk':
        return """Recommendations:
- Review the treatment plan.
- Increase the frequency of check-ups to monitor the patient's condition.
- Provide additional information and support to encourage compliance."""
    else:  # High Risk
        return """Recommendations:
- Intensive therapeutic management is required. Consider adding or enhancing medication, referral to specialists, or implementation of advanced therapies.
- Schedule frequent and possibly multidisciplinary visits for close follow-up.
- Collaborate with other health professionals (cardiologists, nutritionists, psychologists) for holistic care.
- Provide detailed information about the severity of the condition and the importance of strict adherence."""

def generate_patient_description(patient_id, patient_data, score, risk1_year, risk3_year, category):
    """Generate a detailed description for the patient with added information."""

    # Gender description
    gender = "male" if patient_data['gender'] == 'male' else "female"

    # NYHA Class and associated AHA Stage
    nyha_class = patient_data['nyha_class']
    nyha_class_str = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}.get(nyha_class, 'I')

    # AHA Stages descriptions
    aha_stages = {
        'I': (
            "At risk for heart failure\n"
            "In this class, belong people who are at risk for heart failure but do not yet have symptoms or structural or functional heart disease.\n"
            "Risk factors include hypertension, coronary vascular disease, diabetes, obesity, exposure to cardiotoxic agents, "
            "genetic variants for cardiomyopathy, and family history of cardiomyopathy.\n"
        ),
        'II': (
            "Pre-heart failure\n"
            "In this class, people without current or previous symptoms of heart failure but with either structural heart disease, "
            "increased filling pressures in the heart or other risk factors.\n"
        ),
        'III': (
            "Symptomatic heart failure\n"
            "In this class, the people consider that marked limitation of physical activity; comfortable at rest; less than ordinary activity causes fatigue, palpitation, or dyspnea.\n"
        ),
        'IV': (
            "Advanced heart failure\n"
            "In this class, people with heart failure symptoms that interfere with daily life functions or lead to repeated hospitalizations.\n"
        )
    }

    # Get the corresponding AHA stage message based on NYHA class
    aha_stage_message = aha_stages.get(nyha_class_str, "")

    # LVEF classification
    lvef = patient_data['lvef']
    if lvef > 70:
        lvef_category = "Hyperdynamic (LVEF > 70%)"
    elif 50 <= lvef <= 70:
        lvef_category = "Normal (LVEF 50% to 70%)"
    elif 40 <= lvef < 50:
        lvef_category = "Mild dysfunction (LVEF 40% to 49%)"
    elif 30 <= lvef < 40:
        lvef_category = "Moderate dysfunction (LVEF 30% to 39%)"
    else:
        lvef_category = "Severe dysfunction (LVEF < 30%)"

    # Diabetes explanation
    if patient_data['diabetes']:
        diabetes_info = (
            "the patient has been diagnosed with diabetes.\n"
            "Diabetes is a chronic disease that occurs either when the pancreas does not produce enough insulin or when the body cannot\n"
            "effectively use the insulin it produces. Insulin is a hormone that regulates blood glucose. Hyperglycaemia, also called raised blood glucose,\n"
            "is a common effect of uncontrolled diabetes and over time leads to serious damage to many of the body's systems, especially the nerves and blood vessels.\n"
        )
    else:
        diabetes_info = "the patient has not been diagnosed with diabetes.\n"

    # Systolic Blood Pressure details
    sbp = patient_data['sbp']
    if sbp < 120:
        sbp_category = "Normal"
        sbp_condition = "Less than 120 systolic pressure"
    elif 120 <= sbp <= 129:
        sbp_category = "Elevated"
        sbp_condition = "120 to 129 systolic pressure"
    elif 130 <= sbp <= 139:
        sbp_category = "High Blood Pressure Stage 1"
        sbp_condition = "130 to 139 systolic pressure"
    elif 140 <= sbp <= 180:
        sbp_category = "High Blood Pressure Stage 2"
        sbp_condition = "140 or higher systolic pressure"
    else:
        sbp_category = "Hypertensive Crisis"
        sbp_condition = "Higher than 180 systolic pressure"

    # Beta-blocker and ACE/ARB therapy descriptions
    if patient_data['beta_blocker']:
        beta_blocker_text = "the patient is taking beta blockers therapy."
    else:
        beta_blocker_text = "the patient doesn't take beta blockers therapy."

    if patient_data['ace_arb']:
        ace_arb_text = "is taking ACE inhibitors or ARBs therapy."
    else:
        ace_arb_text = "doesn't take ACE inhibitors or ARBs therapy."

    # Heart Failure Duration status
    hf_duration_status = "has" if patient_data['hf_duration_less_than_18_months'] else "does not have"

    description = (
        f"We have patient {patient_id}, whose age is {patient_data['age']} years, and the gender is {gender}, with the following medical characteristics:\n"
        f"Regarding the NYHA class, the patient belongs to Class {nyha_class_str}.\n"
        f"Based on the American Heart Association (AHA) and in collaboration with the American College of Cardiology (ACC), Class {nyha_class_str} has the following characteristics:\n{aha_stage_message}"
        f"(Source: https://www.heart.org/en/health-topics/heart-failure/what-is-heart-failure/classes-of-heart-failure, https://www.mdcalc.com/calc/3987/new-york-heart-association-nyha-functional-classification-heart-failure).\n"
        f"Also, the left ventricular ejection fraction (LVEF) is {lvef:.1f}%.\nAccording to the American College of Cardiology (ACC), the patient has {lvef_category}.\n"
        f"For information, Left ventricular ejection fraction (LVEF) is the central measure of left ventricular systolic function. LVEF is the fraction of chamber volume ejected in systole\n"
        f"(stroke volume) in relation to the volume of the blood in the ventricle at the end of diastole (end-diastolic volume).\n"
        f"(Source: https://www.ncbi.nlm.nih.gov/books/NBK459131/).\n"
        f"Regarding diabetes, {diabetes_info}"
        f"The patient's systolic pressure is {sbp} mm Hg and is characterized as '{sbp_category}' ({sbp_condition}).\n"
    )

    # Creatinine levels
    creatinine = patient_data['creatinine']
    if creatinine < 0.6 and gender == 'male':
        creatinine_category = "Low"
        creatinine_condition = "< 0.6 mg/dL"
    elif creatinine < 0.5 and gender == 'female':
        creatinine_category = "Low"
        creatinine_condition = "< 0.5 mg/dL"
    elif 0.6 < creatinine < 1.2 and gender == 'male':
        creatinine_category = "Normal"
        creatinine_condition = "0.6 to 1.2 mg/dL"
    elif 0.5 < creatinine < 1.1 and gender == 'female':
        creatinine_category = "Normal"
        creatinine_condition = "0.5 to 1.1 mg/dL"
    elif creatinine > 1.2 and gender == 'male':
        creatinine_category = "High"
        creatinine_condition = "above 1.2 mg/dL"
    else:
        creatinine_category = "High"
        creatinine_condition = "above 1.1 mg/dL"

    # BMI
    bmi = patient_data['bmi']
    if bmi < 18.5:
        bmi_category = "Underweight"
    elif 18.5 <= bmi <= 24.9:
        bmi_category = "Normal"
    elif 25 <= bmi <= 29.9:
        bmi_category = "Overweight"
    elif bmi >= 30:
        bmi_category = "Obesity"

    description += (
        f"The patient has a creatinine level of {creatinine} mg/dL and is categorized as {creatinine_category} ({creatinine_condition}).\n"
        f"Source: https://www.healthline.com/health/low-creatinine#creatinine-levels.\n"
        f"The Body Mass Index (BMI) of the patient is {bmi}. Body mass index (BMI) is a measure of body fat based on height and weight that applies to adult men and women.\n"
        f"So, based on the existing scientific literature, the patient with this BMI can be characterized as '{bmi_category}'.\n"
        f"Source: https://www.nhlbi.nih.gov/health/educational/lose_wt/BMI/bmicalc.htm.\n"
        f"Doctors usually prescribe to patients with heart failure drugs such as Beta-blockers.\n"
        f"So, {beta_blocker_text}\n"
        f"Beta-blockers are one of the most widely prescribed classes of drugs to treat hypertension (high blood pressure) and are a mainstay treatment\n"
        f"of congestive heart failure. Beta-blockers work by blocking the effects of epinephrine (adrenaline) and slowing the heart's rate, thereby decreasing\n"
        f"the heart’s demand for oxygen. So, beta-blockers help manage chronic heart failure.\n"
        f"Source: https://www.webmd.com/heart-disease/beta-blocker-therapy.\n"
        f"The other therapy that doctors use for patients is ACE inhibitors or ARBs.\n"
        f"So, the patient {ace_arb_text}\n"
        f"Finally, this patient {hf_duration_status} heart failure diagnosed within the past 18 months.\n"
        f"Based on all the above characteristics, there is a MAGGIC score of {score} categorized as {category}.\n"
        f"The predicted mortality for 1-Year is {risk1_year}%.\n"
        f"The predicted mortality for 3-Year is {risk3_year}%.\n"
    )

    return description

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Process the file
        results = process_file(file_path)
        # Μετακινήστε το αρχείο ή διαγράψτε το αν δεν χρειάζεται πλέον
        os.remove(file_path)
        return render_template('results.html', results=results)
    else:
        flash('Unsupported file type')
        return redirect(request.url)

def process_file_and_calculate(filename):
    patient_data_list = []
    file_extension = os.path.splitext(filename)[-1].lower()

    if file_extension == '.csv':
        # Handle CSV files
        try:
            df = pd.read_csv(filename)
            patient_data_list = df.to_dict(orient='records')  # Convert rows to dictionaries
        except Exception as e:
            print(f"Error reading CSV file: {e}")

    elif file_extension == '.txt':
        # Handle TXT files
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            headers = lines[0].strip().split(',')  # Assume first line contains headers
            for line in lines[1:]:
                values = line.strip().split(',')
                patient_data = dict(zip(headers, values))
                patient_data_list.append(patient_data)
        except Exception as e:
            print(f"Error reading TXT file: {e}")

    elif file_extension == '.json':
        # Handle JSON files
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                patient_data_list = data
            else:
                patient_data_list = [data]
        except Exception as e:
            print(f"Error reading JSON file: {e}")

    elif file_extension in ['.xls', '.xlsx']:
        # Handle Excel files
        try:
            df = pd.read_excel(filename, sheet_name=0)
            patient_data_list = df.to_dict(orient='records')  # Convert rows to dictionaries
        except Exception as e:
            print(f"Error reading Excel file: {e}")

    elif file_extension == '.pdf':
        # Handle PDF files
        try:
            with open(filename, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if not lines:
                return []

            # Assuming structured data for multiple patients with headers in the first line
            headers = lines[0].split(',')
            for line in lines[1:]:
                values = line.split(',')
                if len(values) != len(headers):
                    # Αν οι γραμμές δεν έχουν τον ίδιο αριθμό στηλών, παραλείψτε τις
                    continue
                patient_data = dict(zip(headers, values))
                patient_data_list.append(patient_data)
        except Exception as e:
            print(f"Error reading PDF file: {e}")

    # Process each patient
    results = []
    for idx, raw_data in enumerate(patient_data_list):
        try:
            patient_data = parse_patient_data(raw_data)
            score = calculate_maggic_score(patient_data)
            risk1_year = calculate_1_year_risk(score)
            risk3_year = calculate_3_year_risk(score)
            category = get_risk_category(score)
            patient_message = generate_health_message_patient(score)
            doctor_message = generate_health_message_doctor(score)

            detailed_description = generate_patient_description(
                patient_id=idx + 1,
                patient_data=patient_data,
                score=score,
                risk1_year=risk1_year,
                risk3_year=risk3_year,
                category=category
            )

            results.append({
                "patient_data": patient_data,
                "detailed_description": detailed_description,
                "score": score,
                "risk1_year": risk1_year,
                "risk3_year": risk3_year,
                "category": category,
                "patient_message": patient_message,
                "doctor_message": doctor_message
            })
        except Exception as e:
            print(f"Error processing patient data: {e}")

    return results

def process_file(file_path):
    return process_file_and_calculate(file_path)

if __name__ == "__main__":
    app.run(debug=True)
