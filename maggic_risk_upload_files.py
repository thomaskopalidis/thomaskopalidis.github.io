import csv
import json
import os
import pandas as pd
import PyPDF2
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def load_patient_data(filename):
  patient_data = {}
  file_extension = os.path.splitext(filename)[-1].lower()

  # Read data from CSV
  if file_extension == '.csv':
    try:
      with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
          if len(row) == 2:
            key, val = row[0].strip(), row[1].strip()
            patient_data[key] = val
      if patient_data:
        return patient_data
    except Exception as e:
      print(f"Error reading CSV file: {e}")

  # Read data from TXT
  elif file_extension == '.txt':
    try:
      with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

      # Parse the first line (values) and second line (keys)
      values = lines[0].strip().split()  # Split by spaces
      keys = lines[1].strip().split()  # Split by spaces

      if len(keys) == len(values):  # Match keys with values
        patient_data = dict(zip(keys, values))
      else:
        print("Key-value mismatch in TXT file.")

      return patient_data
    except Exception as e:
      print(f"Error reading TXT file: {e}")

  # Read data from JSON
  elif file_extension == '.json':
    try:
      with open(filename, 'r', encoding='utf-8') as f:
        patient_data = json.load(f)
      return patient_data
    except Exception as e:
      print(f"Error reading JSON file: {e}")

  # Read data from Excel
  elif file_extension in ['.xls', '.xlsx']:
    try:
      df = pd.read_excel(filename, sheet_name=0)  # Ανάγνωση πρώτου φύλλου
      for _, row in df.iterrows():
        if len(row) >= 2:
          key, val = str(row[0]).strip(), str(row[1]).strip()
          patient_data[key] = val
      return patient_data
    except Exception as e:
      print(f"Error reading Excel file: {e}")

  elif file_extension == '.pdf':
    try:
      with open(filename, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
          text += page.extract_text() + "\n"

      # Split text into lines and clean them
      lines = [line.strip() for line in text.split('\n') if line.strip()]

      if len(lines) >= 2:  # Ensure there are at least two lines (values and keys)
        values = lines[0].split()  # First line contains values
        keys = lines[1].split()  # Second line contains keys

        if len(values) == len(keys):
          patient_data = dict(zip(keys, values))
        else:
          print("Warning: Key-value count mismatch in the PDF file.")
      else:
        print("Error: Insufficient data in PDF file.")

      return patient_data
    except Exception as e:
      print(f"Error reading PDF file: {e}")
      return {}
  # If the format is not supported
  else:
    print(f"Unsupported file format: {file_extension}")
    return {}
  return patient_data


def parse_patient_data(patient_data):
  parsed_data = {}
  parsed_data['age'] = int(patient_data.get('age', 0))
  gender = patient_data.get('gender', 'male').strip().lower()
  parsed_data['gender'] = gender if gender in ['male', 'female'] else 'male'
  nyha_class_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
  nyha_str = patient_data.get('nyha_class', 'I').strip().upper()
  parsed_data['nyha_class'] = nyha_class_map.get(nyha_str, 1)
  parsed_data['lvef'] = float(patient_data.get('lvef', 30))
  parsed_data['diabetes'] = patient_data.get('diabetes', 'no').strip().lower() == 'yes'
  parsed_data['smoker'] = patient_data.get('smoker', 'no').strip().lower() == 'yes'
  parsed_data['copd'] = patient_data.get('copd', 'no').strip().lower() == 'yes'
  parsed_data['sbp'] = int(patient_data.get('sbp', 120))
  parsed_data['creatinine'] = float(patient_data.get('creatinine', 1.0))
  parsed_data['bmi'] = float(patient_data.get('bmi', 24))
  parsed_data['beta_blocker'] = patient_data.get('beta_blocker', 'no').strip().lower() == 'yes'
  parsed_data['ace_arb'] = patient_data.get('ace_arb', 'no').strip().lower() == 'yes'
  parsed_data['hf_duration_less_than_18_months'] = patient_data.get('hf_duration_less_than_18_months',
                                                                    'no').strip().lower() == 'yes'
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

#SBP
#normal --> <120
#elevated --> 120 - 129
#High Blood Pressure stage 1 --> 130 - 139
#High Blood Pressure stage 2 --> >140
#Hypertensive Crisis  --> >180

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
      return round(100 * risk1[score], 2)  #  ercentage % with 2 decimal places
    return None  #


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
- Work closely with your doctor to adjust your treatment. Additional treatments or hospitalisation may be needed.
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
    print("Please select the patient's data file (CSV, TXT, JSON, Excel or PDF).")

    # Disable the main Tkinter window
    Tk().withdraw()

    filename = askopenfilename(
      title="Select Patient Data File",
      filetypes=[("Supported files", "*.csv *.txt *.json *.xls *.xlsx *.pdf"), ("All files", "*.*")]
    )

    if not filename:
      print("No file selected. Exiting.")
      return

    if not os.path.exists(filename):
      print("File does not exist. Exiting.")
      return

    # Load and process the data
    patient_data_raw = load_patient_data(filename)
    print(patient_data_raw)
    if not patient_data_raw:
      print("Failed to load patient data. Exiting.")
      return

    # Parse patient data and calculate score
    patient_data = parse_patient_data(patient_data_raw)
    score = calculate_maggic_score(patient_data)
    risk1_year = calculate_1_year_risk(score)
    risk3_year = calculate_3_year_risk(score)
    category = get_risk_category(score)
    message_for_patient = generate_health_message_patient(score)
    message_for_doctor = generate_health_message_doctor(score)

    # Print the results
    print("\n--- Results ---")
    print(f"Total Score: {score}")
    print(f"Risk Category: {category}")
    print(f"1-Year Risk: {risk1_year}%")
    print(f"3-Year Risk: {risk3_year}%")
    print(f"\nMessage for the Patient:\n{message_for_patient}")
    print(f"\nMessage for the Doctor:\n{message_for_doctor}")
    print("DEBUG: patient_data =", patient_data)

if __name__ == "__main__":
  main()
