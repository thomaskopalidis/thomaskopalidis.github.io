import csv
import json
import os
import pandas as pd
import PyPDF2
from tkinter import Tk
from tkinter.filedialog import askopenfilename


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
          extracted_text = page.extract_text()
          if extracted_text:
            text += extracted_text + "\n"

      lines = [line.strip() for line in text.split('\n') if line.strip()]
      headers = lines[0].split(',')
      for line in lines[1:]:
        values = line.split(',')
        patient_data = dict(zip(headers, values))
        patient_data_list.append(patient_data)
    except Exception as e:
      print(f"Error reading PDF file: {e}")

  else:
    print(f"Unsupported file format: {file_extension}")
    return

  # Process each patient
  results = []
  output_file = "patient_descriptions.txt"

  with open(output_file, 'w', encoding='utf-8') as txt_file:
    for idx, raw_data in enumerate(patient_data_list):
      try:
        patient_data = parse_patient_data(raw_data, idx + 1)
        patient_id = patient_data['name'] if patient_data['name'] else f"Patient {idx + 1}"
        score = calculate_maggic_score(patient_data)
        risk1_year = calculate_1_year_risk(score)
        risk3_year = calculate_3_year_risk(score)
        category = get_risk_category(score)
        patient_message = generate_health_message_patient(score)
        doctor_message = generate_health_message_doctor(score)

        # Generate detailed description
        detailed_description = generate_patient_description(patient_id, patient_data, score, category, risk1_year,
                                                            risk3_year)

        # Save to results and write to file
        results.append({
          "patient_id": patient_id,
          "detailed_description": detailed_description,
          "score": score,
          "risk1_year": risk1_year,
          "risk3_year": risk3_year,
          "category": category,
          "patient_message": patient_message,
          "doctor_message": doctor_message
        })

        txt_file.write(f"\n--- {patient_id} ---\n")
        txt_file.write(detailed_description + "\n")
        txt_file.write(f"Score: {score}\n")
        txt_file.write(f"Risk Category: {category}\n")
        txt_file.write(f"1-Year Risk: {risk1_year}%\n")
        txt_file.write(f"3-Year Risk: {risk3_year}%\n")
        txt_file.write("Message for Patient:\n")
        txt_file.write(patient_message + "\n\n")
        txt_file.write("Message for Doctor:\n")
        txt_file.write(doctor_message + "\n\n")

      except Exception as e:
        print(f"Error processing patient data: {e}")

  print(f"Patient descriptions saved to {output_file}")

def parse_patient_data(patient_data, default_patient_no):
    parsed_data = {}

    # Handle possible different key names with case insensitivity
    def get_value(keys, default):
        for key in keys:
            if key in patient_data:
                return patient_data[key]
        return default

    # Extract 'Name' field (assumed to be the first column)
    name = get_value(['Name', 'name', 'Patient Name', 'PatientName'], None)
    if not name:
        # Fallback: Extract the first column's value
        first_key = list(patient_data.keys())[0]
        name = patient_data[first_key]
        print(f"Warning: 'name' field not found. Using first column '{first_key}' value '{name}' as patient name.")

    parsed_data['name'] = name

    try:
        parsed_data['age'] = int(get_value(['age', 'Age'], 0))
    except ValueError:
        print(f"Invalid age value '{get_value(['age', 'Age'], 0)}'. Defaulting to 0.")
        parsed_data['age'] = 0

    gender = get_value(['gender', 'Gender'], 'male').strip().lower()
    parsed_data['gender'] = gender if gender in ['male', 'female'] else 'male'

    nyha_str = get_value(['nyha_class', 'NYHA Class'], 'I').strip().upper()
    nyha_class_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
    parsed_data['nyha_class'] = nyha_class_map.get(nyha_str, 1)

    try:
        parsed_data['lvef'] = float(get_value(['lvef', 'LVEF'], 30))
    except ValueError:
        print(f"Invalid LVEF value '{get_value(['lvef', 'LVEF'], 30)}'. Defaulting to 30.")
        parsed_data['lvef'] = 30.0

    diabetes_input = get_value(['diabetes', 'Diabetes'], 'no').strip().lower()
    parsed_data['diabetes'] = True if diabetes_input == 'yes' else False

    smoker_input = get_value(['smoker', 'Smoker'], 'no').strip().lower()
    parsed_data['smoker'] = True if smoker_input == 'yes' else False

    copd_input = get_value(['copd', 'COPD'], 'no').strip().lower()
    parsed_data['copd'] = True if copd_input == 'yes' else False

    try:
        parsed_data['sbp'] = int(get_value(['sbp', 'SBP'], 120))
    except ValueError:
        print(f"Invalid SBP value '{get_value(['sbp', 'SBP'], 120)}'. Defaulting to 120.")
        parsed_data['sbp'] = 120

    try:
        parsed_data['creatinine'] = float(get_value(['creatinine', 'Creatinine'], 1.0))
    except ValueError:
        print(f"Invalid creatinine value '{get_value(['creatinine', 'Creatinine'], 1.0)}'. Defaulting to 1.0.")
        parsed_data['creatinine'] = 1.0

    try:
        parsed_data['bmi'] = float(get_value(['bmi', 'BMI'], 24))
    except ValueError:
        print(f"Invalid BMI value '{get_value(['bmi', 'BMI'], 24)}'. Defaulting to 24.")
        parsed_data['bmi'] = 24.0

    beta_blocker_input = get_value(['beta_blocker', 'Beta Blocker'], 'no').strip().lower()
    parsed_data['beta_blocker'] = True if beta_blocker_input == 'yes' else False

    ace_arb_input = get_value(['ace_arb', 'ACE_ARB', 'ACE Inhibitors or ARBs'], 'no').strip().lower()
    parsed_data['ace_arb'] = True if ace_arb_input == 'yes' else False

    hf_duration_input = get_value(['hf_duration_less_than_18_months', 'HF Duration <18 months'], 'no').strip().lower()
    parsed_data['hf_duration_less_than_18_months'] = True if hf_duration_input == 'yes' else False

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


# SBP Categories
# Normal --> <120
# Elevated --> 120 - 129
# High Blood Pressure stage 1 --> 130 - 139
# High Blood Pressure stage 2 --> >140
# Hypertensive Crisis  --> >180

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


def generate_patient_description(patient_id, patient_data, score, category, risk1_year, risk3_year):
    """Generate a detailed description for the patient with added information."""

    # Gender description
    gender = "male" if patient_data['gender'] == 'male' else "female"

    # NYHA Class and associated AHA Stage
    nyha_class = patient_data['nyha_class']
    nyha_class_str = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}.get(nyha_class, 'I')

    # AHA Stages descriptions
    aha_stages = {
        'I': (
            "At risk for heart failure.\n"
            "In this class, people are at risk for heart failure but do not yet have symptoms or structural or functional heart disease.\n"
            "Risk factors include hypertension, coronary vascular disease, diabetes, obesity, exposure to cardiotoxic agents, "
            "genetic variants for cardiomyopathy, and family history of cardiomyopathy.\n"
        ),
        'II': (
            "Pre-heart failure.\n"
            "In this class, people without current or previous symptoms of heart failure but with either structural heart disease, "
            "increased filling pressures in the heart or other risk factors.\n"
        ),
        'III': (
            "Symptomatic heart failure.\n"
            "People in this class have a marked limitation of physical activity; they are comfortable at rest; less than ordinary activity causes fatigue, palpitation, or dyspnea.\n"
        ),
        'IV': (
            "Advanced heart failure.\n"
            "In this class, people have heart failure symptoms that interfere with daily life functions or lead to repeated hospitalizations.\n"
        )
    }

    # Get the corresponding AHA stage message based on NYHA class
    aha_stage_message = aha_stages.get(nyha_class_str, "")

    # LVEF classification based on ACC guidelines
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

    # Diabetes explanation if positive
    diabetes_info = ""
    if patient_data['diabetes']:
        diabetes_info = (
            "the patient has been diagnosed with diabetes.\n"
            "Diabetes is a chronic disease that occurs either when the pancreas does not produce enough insulin or when the body cannot\n"
            "effectively use the insulin it produces. Insulin is a hormone that regulates blood glucose. Hyperglycemia, also called raised blood glucose,\n"
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
        sbp_condition = "140 or higher systolic pressure OR 90 or higher diastolic pressure"
    else:
        sbp_category = "Hypertensive Crisis"
        sbp_condition = "Higher than 180 systolic pressure"

    sbp_info = (
        "Blood Pressure Category:\n"
        "Normal: Less than 120 systolic pressure\n"
        "Elevated: 120 to 129 systolic pressure\n"
        "High Blood Pressure Stage 1: 130 to 139 systolic pressure\n"
        "High Blood Pressure Stage 2: 140 or higher systolic pressure OR 90 or higher diastolic pressure\n"
        "Hypertensive Crisis: Higher than 180 systolic pressure\n"
    )

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

    # Creatinine and BMI
    creatinine = patient_data['creatinine']
    bmi = patient_data['bmi']

    # Creatinine categorization based on gender
    if creatinine < 0.6 and gender == 'male':
        creatinine_category = "Low"
        creatinine_condition = "< 0.6 mg/dL"
    elif creatinine < 0.5 and gender == 'female':
        creatinine_category = "Low"
        creatinine_condition = "< 0.5 mg/dL"
    elif 0.6 <= creatinine <= 1.2 and gender == 'male':
        creatinine_category = "Normal"
        creatinine_condition = "0.6 to 1.2 mg/dL"
    elif 0.5 <= creatinine <= 1.1 and gender == 'female':
        creatinine_category = "Normal"
        creatinine_condition = "0.5 to 1.1 mg/dL"
    elif creatinine > 1.2 and gender == 'male':
        creatinine_category = "High"
        creatinine_condition = "above 1.2 mg/dL"
    elif creatinine > 1.1 and gender == 'female':
        creatinine_category = "High"
        creatinine_condition = "above 1.1 mg/dL"
    else:
        creatinine_category = "Unknown"
        creatinine_condition = "N/A"

    # BMI categorization
    if bmi < 18.5:
        bmi_category = "Underweight"
    elif 18.5 <= bmi <= 24.9:
        bmi_category = "Normal"
    elif 25 <= bmi <= 29.9:
        bmi_category = "Overweight"
    elif bmi >= 30:
        bmi_category = "Obesity"
    else:
        bmi_category = "Unknown"

    # Construct the detailed description
    description = (
        f"We have patient {patient_id}, whose age is {patient_data['age']} years, and the gender is {gender}, with the following medical characteristics:\n"
        f"Regarding the NYHA class, the patient belongs to Class {nyha_class_str}.\n"
        f"Based on the American Heart Association (AHA) and in collaboration with the American College of Cardiology (ACC), "
        f"Class {nyha_class_str} has the following characteristics:\n{aha_stage_message}"
        f"(Source: https://www.heart.org/en/health-topics/heart-failure/what-is-heart-failure/classes-of-heart-failure,\n"
        f"https://www.mdcalc.com/calc/3987/new-york-heart-association-nyha-functional-classification-heart-failure).\n"
        f"Also, the left ventricular ejection fraction (LVEF) is {lvef:.1f}%.\nAccording to the American College of Cardiology (ACC), the patient has {lvef_category}.\n"
        f"For information, Left ventricular ejection fraction (LVEF) is the central measure of left ventricular systolic function. LVEF is the fraction of chamber volume ejected in systole (stroke volume) in relation to the volume of the blood in the ventricle at the end of diastole (end-diastolic volume).\n"
        f"(Source: https://www.ncbi.nlm.nih.gov/books/NBK459131/).\n"
        f"Regarding diabetes, {diabetes_info}"
        f"The patient's systolic pressure is {sbp} mm Hg and is characterized as '{sbp_category}' ({sbp_condition}).\n"
        f"Regarding heart failure medications, {beta_blocker_text} Moreover, {ace_arb_text}\n"
        f"The patient has a creatinine level of {creatinine} mg/dL and is categorized as {creatinine_category} ({creatinine_condition}).\n"
        f"Source: https://www.healthline.com/health/low-creatinine#creatinine-levels.\n"
        f"The Body Mass Index (BMI) of the patient is {bmi}.\n"
        f"Body mass index (BMI) is a measure of body fat based on height and weight that applies to adult men and women.\n"
        f"So, based on the existing scientific literature, the patient with this BMI can be characterized as '{bmi_category}'.\n"
        f"Source: https://www.nhlbi.nih.gov/health/educational/lose_wt/BMI/bmicalc.htm.\n"
        f"Finally, patient {patient_id} {hf_duration_status} heart failure diagnosed within the past 18 months.\n"
        f"Based on all the above characteristics, patient's {patient_id} MAGGIC score is {score} and this MAGGIC score is categorized as {category}.\n"
        f"The predicted mortality for 1-Year is {risk1_year}%.\n"
        f"The predicted mortality for 3-Year is {risk3_year}%.\n"
    )

    return description


def get_user_input():
    patient_data = {}
    try:
        # Age
        age = int(input("Enter the patient's age (18–110 years): "))
        patient_data['age'] = age

        # Gender
        gender = input("Enter the patient's gender (male/female): ").strip().lower()
        while gender not in ['male', 'female']:
            gender = input("Please enter 'male' or 'female': ").strip().lower()
        patient_data['gender'] = gender

        # NYHA Class
        nyha_class_input = input("Enter the NYHA class (I-IV): ").strip().upper()
        while nyha_class_input not in ['I', 'II', 'III', 'IV']:
            nyha_class_input = input("Please enter one of the options: I, II, III, IV: ").strip().upper()
        nyha_class_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
        nyha_class = nyha_class_map[nyha_class_input]
        patient_data['nyha_class'] = nyha_class

        # LVEF
        lvef = float(input("Enter the Left Ventricular Ejection Fraction (LVEF, 0–95%): "))
        patient_data['lvef'] = lvef

        # Diabetes
        diabetes = input("Does the patient have diabetes? (yes/no): ").strip().lower()
        while diabetes not in ['yes', 'no']:
            diabetes = input("Please enter 'yes' or 'no': ").strip().lower()
        patient_data['diabetes'] = True if diabetes == 'yes' else False

        # Smoking
        smoker = input("Is the patient a smoker? (yes/no): ").strip().lower()
        while smoker not in ['yes', 'no']:
            smoker = input("Please enter 'yes' or 'no': ").strip().lower()
        patient_data['smoker'] = True if smoker == 'yes' else False

        # COPD
        copd = input("Does the patient have COPD? (yes/no): ").strip().lower()
        while copd not in ['yes', 'no']:
            copd = input("Please enter 'yes' or 'no': ").strip().lower()
        patient_data['copd'] = True if copd == 'yes' else False

        # Systolic Blood Pressure
        sbp = int(input("Enter the systolic blood pressure (SBP, 50–250 mmHg): "))
        patient_data['sbp'] = sbp

        # Serum Creatinine
        creatinine = float(input("Enter the serum creatinine levels in mg/dL (0.1–15 mg/dL): "))
        patient_data['creatinine'] = creatinine

        # BMI
        bmi = float(input("Enter the Body Mass Index (BMI, 10–50 kg/m²): "))
        patient_data['bmi'] = bmi

        # Beta-Blocker Use
        beta_blocker = input("Is the patient on beta-blockers? (yes/no): ").strip().lower()
        while beta_blocker not in ['yes', 'no']:
            beta_blocker = input("Please enter 'yes' or 'no': ").strip().lower()
        patient_data['beta_blocker'] = True if beta_blocker == 'yes' else False

        # ACE Inhibitors or ARBs
        ace_arb = input("Is the patient on ACE Inhibitors or ARBs? (yes/no): ").strip().lower()
        while ace_arb not in ['yes', 'no']:
            ace_arb = input("Please enter 'yes' or 'no': ").strip().lower()
        patient_data['ace_arb'] = True if ace_arb == 'yes' else False

        # Heart Failure Duration
        hf_duration_input = input("Was heart failure first diagnosed less than 18 months ago? (yes/no): ").strip().lower()
        while hf_duration_input not in ['yes', 'no']:
            hf_duration_input = input("Please enter 'yes' or 'no': ").strip().lower()
        patient_data['hf_duration_less_than_18_months'] = True if hf_duration_input == 'yes' else False

    except ValueError:
        print("Invalid input. Please try again.")
        return get_user_input()

    return patient_data


def main():
    print("MAGGIC Risk Calculator")
    print("Please select the patient's data file (CSV, TXT, JSON, Excel, or PDF).")
    Tk().withdraw()  # Hide the Tkinter GUI window

    filename = askopenfilename(
        title="Select Patient Data File",
        filetypes=[("Supported files", "*.csv *.txt *.json *.xls *.xlsx *.pdf"), ("All files", "*.*")]
    )

    if filename:
        process_file_and_calculate(filename)
    else:
        print("No file selected. Exiting.")


if __name__ == "__main__":
    main()
