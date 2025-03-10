# maggic_model.py
import os
import json
import pandas as pd
import PyPDF2

def parse_patient_data(patient_data, default_patient_no):
  parsed_data = {}

  # Handle possible different key names with case insensitivity
  def get_value(keys, default):
    for key in keys:
      if key in patient_data:
        return patient_data[key]
    return default

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
  parsed_data['hf_duration_less_than_18_months'] = get_value(
    ['hf_duration_less_than_18_months', 'HF Duration <18 months'], 'no').strip().lower() == 'yes'

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
    return round(100 * risk3[score], 2)  # Percentage % with 2 decimal places
  return None


def get_risk_category(score):
  if score <= 19:
    return 'Low Risk'
  elif score <= 30:
    return 'Medium Risk'
  else:
    return 'High Risk'


def generate_health_message_patient(score, patient_data):
  """Generate health message for the patient based on their MAGGIC score and data."""
  category = get_risk_category(score)
  main_message = ""
  recommendations = []

  # Base recommendations based on risk category
  if category == 'Low Risk':
     main_message = "Your prognosis is favorable. By continuing your current treatment and healthy habits, you can maintain a good quality of life."
  #   recommendations = [
  #     "Continue your prescribed medication regimen as the doctor will suggest, i.e., ACE inhibitors (e.g., enalapril) or ARBs (e.g., losartan) to protect heart function and reduce strain.",
  #     "Maintain a heart-healthy diet rich in vegetables, fruits, whole grains, and lean proteins. Replace saturated with unsaturated fats and reduce salt intake.",
  #     "Engage in regular physical activity, such as walking, swimming, or yoga, for at least 150 minutes per week.",
  #     "Keep your check-up appointments (e.g., every 6-12 months or as directed by your doctor) and report any changes in your symptoms in a timely manner."
  #   ]
  elif category == 'Medium Risk':
     main_message = "There is a moderate risk to your health. With certain adjustments, your prognosis can improve. By taking proactive steps and following your doctor’s instructions, you can reduce your risk and improve your quality of life."
  #   recommendations = [
  #     "Follow a tailored exercise program under the supervision of a fitness instructor or physiotherapist to improve functional capacity.",
  #     "Monitor your symptoms daily (e.g., weight gain, swelling, breathlessness) and report any changes to your healthcare provider immediately.",
  #     "Discuss possible adjustments to your medication regimen with your doctor to further optimize your treatment plan.",
  #     "Adopt a heart-healthy diet tailored to your needs. Focus on reducing sodium intake to manage blood pressure and cholesterol levels, choosing whole grains, lean proteins, and fresh fruits and vegetables.",
  #     "Schedule more regular check-ups (e.g., every 3-6 months) and discuss with your doctor if treatment optimization is needed (e.g., adding MRA, changing to ARNI)."
   # ]
  else:  # High Risk
     main_message = "The condition is serious, with increased risk to your health. However, measures can be taken to improve the situation."
  #   recommendations = [
  #     "Avoid intense physical activity and save energy. Talk to your doctor about light activities, such as sitting exercises.",
  #     "Seek emotional and psychological support from counseling or support groups to manage the stress and anxiety associated with high-risk heart failure.",
  #     "Adopt a highly structured and personalized diet plan aimed at reducing sodium intake, managing fluid retention, and optimizing nutrient balance to support cardiac function.",
  #     "Adopt healthy habits more strictly: stop smoking and alcohol intake, control your weight, manage other conditions such as diabetes.",
  #     "Discuss advanced therapeutic options with your healthcare provider.",
  #     "Schedule more frequent regular checks (e.g., every 1-3 months or as directed by your healthcare provider) to monitor your condition closely and adjust treatments as needed."
  #   ]

  # Additional recommendations based on patient-specific data

  lvef = patient_data['lvef']
  if lvef < 40:
    recommendations.append(
      "Since your low ejection fraction is low (LVEF < 40), you can follow instructions that will help to  "
      "improve your injection fraction."
      "The average American consumes nearly 3,400 mg of sodium per day, "
      "which is more than double the recommended amount."
      " Aim to reduce salt consumption to align with recommended levels. Check food labels and avoid processed or high-sodium foods."
      " Discuss with your cardiologist the appropriate amount of fluids you should consume daily. Also, engage in physical activity for at least 30 minutes per day, three days a week."
      " (Source: https://www.pennmedicine.org/updates/blogs/heart-and-vascular-blog/2022/april/ejection-fraction-what-the-numbers-mean.)"
    )
    # Smoking-specific recommendation
  if patient_data['smoker']:
     recommendations.append(
        "Quitting smoking is one of the most impactful steps you can take to improve your health. Smoking increases the risk of serious illnesses like heart disease and lung cancer. "
        "Start by setting a quit date within the next two weeks to stay focused and committed. Seek support through counseling and consider using nicotine replacement therapies "
        "like patches or gums to ease withdrawal symptoms. Your healthcare provider can also recommend medications to help you quit. "
        "Creating a smoke-free environment and identifying triggers can make a big difference in your journey "
        "(Source: https://cdphe.colorado.gov/prevention-and-wellness/smoking-and-tobacco/quit-tobacco/recommendations-for-reducing-tobacco-use)."
     )
  else:
    recommendations.append(
         "Avoid smoking as this can increase your risk of cardiovascular diseases."
     )

  if patient_data['diabetes']:
    recommendations.append(
      "Managing diabetes involves a healthy lifestyle and a personalized care plan. A balanced diet is essential, focusing on nutrient-rich foods such as non-starchy vegetables, lean proteins, whole grains, and healthy fats. "
      "Limit refined sugars and simple carbohydrates, manage your carbohydrate intake, and choose foods with a low glycemic index. "
      "Regular physical activity is vital,  for at least 30 minutes or more of moderate physical activity most days of the week, or at "
      "least 150 minutes of moderate physical activity a week. Bouts of activity can be a few minutes during the day. If you haven't been active for a while, "
      "start slowly and build up slowly. Also avoid sitting for too long. Try to get up and move "
      "if you've been sitting for more than 30 minutes. (Source: https://www.mayoclinic.org/diseases-conditions/diabetes/diagnosis-treatment/drc-20371451.)   "
      "Monitor blood sugar levels regularly, understand how food, exercise, and medication affect them, and react appropriately to high or low levels. "
      "Consult your doctor about whether you should take diabetes medication (e.g., insulin, oral medication). Manage stress with techniques such as meditation or yoga, as stress can affect blood sugar. "
      "Regular check-ups and preventative care are vital to identify and manage complications such as eye, kidney, nerve, or heart problems "
      "(Source: https://www.niddk.nih.gov/health-information/diabetes/overview/healthy-living-with-diabetes)."
    )
  if patient_data['sbp'] > 130:
    recommendations.append(
      "Since your systolic blood pressure is high, focus on eating colorful fruits and vegetables, since their high potassium content can help lower blood pressure. "
      "Choose whole grains whenever possible, and limit white flours such as those found in white bread and pasta. "
      "Avoid drinking sweetened drinks like juice and soda, and watch for salt in processed foods and canned items. "
      "Limit intake of saturated fat by choosing lean meats like skinless chicken and turkey. "
      "Choose low-fat or nonfat dairy items "
      "(Source: https://www.verywellhealth.com/how-to-lower-systolic-blood-pressure-5202628)."
    )
  if not patient_data['beta_blocker']:
    recommendations.append(
      "Consult your doctor if beta blocker therapy is necessary."
    )
  if not patient_data['ace_arb']:
    recommendations.append(
      "Consult your doctor if ACE inhibitors or ARBs therapy is necessary."
    )

  creatinine = patient_data['creatinine']
  gender = patient_data['gender'].lower()
  if (gender == 'male' and creatinine > 1.2) or (gender == 'female' and creatinine > 1.1):
    recommendations.append(
      "The patient has high creatinine levels. High creatinine levels may indicate that your kidneys aren’t filtering your blood properly.  "
      "Consult your doctor to tell you what you should do to decrease your creatinine levels to normal levels."
      " (Source: https://www.healthline.com/health/low-creatinine#treatment.)."
    )

    # copd and smoker
  if patient_data['copd'] and patient_data['smoker']:
    recommendations.append("As you are a smoker and have COPD, it is critical to quit smoking immediately."
                           " Smoking exacerbates COPD symptoms, "
        "causes further damage to your lungs, and worsens your overall condition."
    )
  elif patient_data['copd']:
    recommendations.append(
      "You have COPD, so you need to avoiding triggers such as dust, fumes, "
      "and extreme temperatures can minimize flare-ups. Also, vaccinations against flu, pneumonia, and COVID-19 are essential "
      "to prevent infections that could worsen the condition.  Breathing techniques, like pursed-lip breathing,"
      " and physical activity help improve lung function and stamina "
      " (Source: https://www.nhs.uk/conditions/chronic-obstructive-pulmonary-disease-copd/living-with/)."
    )


  creatinine = patient_data['creatinine']
  gender = patient_data['gender'].lower()
  if (gender == 'male' and creatinine < 0.6) or (gender == 'female' and creatinine < 0.5):
    recommendations.append(
      "The patient has low creatinine levels. Low creatinine may "
      "indicate an issue to the body of the patient is having in the production of creatine, such as muscle wasting or a liver problem. "
      "Consult your doctor to tell you what you should do to increase your creatinine levels."
      " (Source: https://www.healthline.com/health/low-creatinine#treatment.)."
    )

  if 25 <= patient_data['bmi'] < 30 :
    recommendations.append(
      "Since you are diagnosed as overweight person, it’s important to follow their recommendations of your doctor for losing weight."
      " Health professionals recommend losing 5% to 10% of your initial weight over the course of about 6 months. "
      "But a loss of just 3% to 5% of your "
      "current weight can lower triglycerides and glucose levels in your blood, as well as your risk of developing type 2 diabetes."
      " Losing more than 3% to 5% of your weight can improve blood pressure readings, lower “bad” LDL cholesterol, and increase"
      " “good” HDL cholesterol. "
      "(Source: https://www.nhlbi.nih.gov/heart-truth/maintain-a-healthy-weight)."
    )

  if patient_data['bmi'] < 18.5:
    recommendations.append(
      "Since you are diagnosed as underweight person, it’s important to follow their recommendations of your doctor for gaining weight."
      " The aim is to gain weight gradually by eating healthy foods."
      " Even if you are underweight, try to avoid foods with a lot of added"
      " sugar, fat and salt, like cakes, takeaway foods and sugary drinks. "
      "The Australian dietary guidelines can help you learn about the amount"
      " and kinds of foods that you need to eat for health and wellbeing. "
      "By following the dietary patterns recommended in the guidelines,"
      " you will get enough of the nutrients essential for good health,"
      " and also help reduce your risk of long-term health problems."
      "You can put on weight by eating small meals frequently throughout the day. "
      "Try to snack on healthy, high-energy foods like cheese, nuts, milk-based smoothies and dried fruit. "
      "Specifically, some guidelines for gaining weight include using full cream milk in coffee, tea or with meals, "
      "healthy fats like olive oil or avocado in your meals, "
      "sprinkling some grated cheese on cooked food, "
      "adding milk powder to soups, stews and drinks, "
      "adding protein powder to milkshakes, "
      "replacing black tea or coffee with milky drinks and "
      "doing some light exercise to increase your appetite "
      "(Source: https://www.healthdirect.gov.au/what-to-do-if-you-are-underweight)."
    )
  if patient_data['bmi'] > 29.9:
    recommendations.append(
      "Since you are diagnosed as obesity person, it’s important to follow their recommendations of your doctor for losing weight."
      " Health professionals recommend losing 5% to 10% of your initial weight over the course of about 6 months. "
      "But a loss of just 3% to 5% of your "
      "current weight can lower triglycerides and glucose levels in your blood, as well as your risk of developing type 2 diabetes."
      " Losing more than 3% to 5% of your weight can improve blood pressure readings, lower “bad” LDL cholesterol, and increase"
      " “good” HDL cholesterol "
      "(Source: https://www.nhlbi.nih.gov/heart-truth/maintain-a-healthy-weight)."
    )

  if 18.5 < patient_data['bmi'] < 25:
    recommendations.append(
        "Your BMI is in the normal range, which is great for your overall health. "
        "Focus on maintaining your current weight and healthy habits."
    )

  return main_message, recommendations


def generate_health_message_doctor(score, patient_data):
  category = get_risk_category(score)
  main_message = ""
  recommendations = []
  if category == 'Low Risk':
   main_message = "The patient has a favorable prognosis. Continuing current management and preventive strategies is key to maintaining health."
  #   recommendations = [
  #     "Reinforce the importance of lifestyle modifications to the patient, including dietary changes and physical activity.",
  #     "Explain to the patient which exercises are safe and which to avoid (e.g., vigorous aerobic activities may not be safe). For information, physical activity help to strengthen the heart (improves the heart's efficacy in pumping blood),"
  #     " lower blood pressure (helps to reduce the high blood pressure), "
  #     "improve cholesterol levels (HDL and LDL improving lipid profiles), "
  #     "it helps to maintain a healthy weight (which reduces strain on the heart), "
  #     "improves circulation (enhances blood flow, reducing the risk of clots and improving oxygen delivery to tissues), "
  #     "reduce stress etc. ",
  #     "Schedule check-ups to monitor the patient's progress.",
  #     "Provide educational resources to the patient about early symptoms of heart failure decompensation (e.g., weight gain, dyspnea) and clarify clear action steps."
  #   ]
  elif category == 'Medium Risk':
     main_message = "The patient is at moderate risk. Review and optimize the treatment plan to address potential risks effectively."
  #   recommendations = [
  #     "Reassess the current treatment strategy and consider adjustments, including medications or dosages.",
  #     "Increase the frequency of follow-up visits to monitor the patient’s condition more closely.",
  #     "Collaborate with a multidisciplinary team (e.g., cardiologists, dietitians) to address comorbidities and risk factors.",
  #     "Educate the patient about the importance of compliance with therapy and lifestyle modifications.",
  #     "Provide guidance on managing symptoms and when to seek immediate medical attention."
  #   ]
  else:  # High Risk
     main_message = "The patient is at high risk and requires intensive management. Comprehensive and multidisciplinary care is critical."
  #   recommendations = [
  #     "Adjust or intensify the treatment plan, including consideration of advanced therapies.",
  #     "Collaborate with a multidisciplinary team, including heart failure specialists, dietitians, and palliative care providers, to ensure holistic and patient-centered care.",
  #     "Schedule frequent follow-ups to assess the effectiveness of interventions and monitor progress.",
  #     "Educate the patient and caregivers on recognizing warning signs and symptoms that warrant urgent attention.",
  #     "Discuss potential advanced therapeutic options, such as device therapy or hospitalization, if applicable."
  #   ]
  lvef = patient_data['lvef']
  if lvef > 70:
    recommendations.append(
      "The patient has a high ejection fraction (LVEF > 70). "
      "As a doctor, you may consider the following treatment options for improving heart function:\n"
      " Angiotensin converting enzyme (ACE) inhibitors, angiotensin II receptor blockers (ARBs), or beta-blockers: These medications can reduce the amount of hormones that weaken your heart muscle and slow the progression of heart disease.\n"
      " Diuretics: These drugs can help eliminate excess fluid, reducing swelling and shortness of breath.\n"
      " Eplerenone or spironolactone: These medications help eliminate excess fluid and decrease heart stiffening.\n"
      " Hydralazine/nitrate: This combination lowers blood pressure in patients who still have symptoms when taking ACE inhibitors, ARBs, or beta-blockers.\n"
      " Angiotensin receptor-neprilysin inhibitor (ARNI): A combination of sacubitril and valsartan that reduces blood pressure and strain on the heart.\n"
      " Sodium-glucose cotransporter 2 (SGLT2) inhibitors: Particularly beneficial for patients with type 2 diabetes to reduce heart failure risk and kidney complications.\n"
      " Biventricular pacemaker: Helps synchronize the contractions of the left and right ventricles to improve heart efficiency.\n"
      " Implantable cardiac defibrillator: A device implanted into the chest that sends small electrical triggers to maintain a regular heart rhythm "
      "(Source: https://www.healthline.com/health/ejection-fraction#treatment.)"
    )
  elif lvef < 40:
    recommendations.append(
      "The patient has a low ejection fraction (LVEF < 40). "
      "Υou may suggest treatments such as an implantable "
      "cardioverter defibrillator (ICD) or a pacemaker to help regulate "
      "the heart rhythm and prevent sudden cardiac arrest (Source: https://www.healthline.com/health/ejection-fraction#low-ef-causes.)"
    )

  if patient_data['smoker']:
     recommendations.append(
        "Recommend quit-smoking medications to patients, including nicotine replacement therapies (such as nicotine patches, "
        "lozenges, gum, oral inhalers, and nasal sprays) and"
        " prescription medications like varenicline and bupropion SR "
        "(Source: https://www.cdc.gov/tobacco/campaign/tips/quit-smoking/quit-smoking-medications/how-to-use-quit-smoking-medicines/index.html)."
     )
  else:
    recommendations.append(
         "Advise the patient to avoid smoking, as it increases the risk of cardiovascular diseases."
     )
  if patient_data['diabetes']:
    recommendations.append(
      "The patient has diabetes. Υou can provide the following guidelines to help the patient manage their diabetes effectively:\n"
      " Perform a comprehensive medical evaluation to classify diabetes, and evaluate for complications or comorbidities.\n"
      " Review prior treatment history and risk factor control to identify gaps in management.\n"
      " Develop an individualized care plan that includes therapeutic goals, lifestyle changes, and ongoing monitoring.\n"
      " At follow-up visits, reassess overall health, diabetes complications, cardiovascular risk, and hypoglycemia risk.\n"
      " Use shared decision-making to set and adjust therapeutic goals, ensuring the patient is engaged in their care.\n"
      " Promote healthy lifestyle habits such as a nutrient-dense diet, regular physical activity, weight management, and stress reduction techniques.\n"
      " Regularly monitor blood glucose levels and HbA1c to assess treatment efficacy and identify complications early.\n"
      " Recommend preventive care, including regular eye exams, foot care, and kidney function monitoring\n"
      "(Source: https://www.mayoclinic.org/diseases-conditions/diabetes/diagnosis-treatment/drc-20371451)."
    )
  if patient_data['copd'] and patient_data['smoker']:
    recommendations.append(
      "The patient has COPD. There are various treatment options to discuss with the patient, "
      "such as quitting smoking, using inhalers (the first treatment used are short-acting bronchodilator inhalers (beta-2 agonist inhalers such as salbutamol and terbutaline"
      " and antimuscarinic inhalers such as ipratropium. The next phase if  the patient experience symptoms regularly or have flare-ups (exacerbations) despite using short-acting bronchodilators,"
      " a long-acting bronchodilator inhaler may be recommended i.e. beta-2 agonist inhalers – such as salmeterol, formoterol and indacaterol"
      " and antimuscarinic inhalers – such as tiotropium, glycopyronium and aclidinium.), steroid inhalers "
      "if the long-acting bronchodilator inhaler didn't make any difference to the symptoms consider tablets (Source: https://www.nhs.uk/conditions/chronic-obstructive-pulmonary-disease-copd/treatment/)"
    )
  elif patient_data['copd']:
    recommendations.append(
      "The patient has COPD. There are various treatment options to discuss with the patient, "
      " such as using inhalers (the first treatment used are short-acting bronchodilator inhalers (beta-2 agonist inhalers such as salbutamol and terbutaline"
      " and antimuscarinic inhalers such as ipratropium. The next phase if  the patient experience symptoms regularly or have flare-ups (exacerbations) despite using short-acting bronchodilators,"
      " a long-acting bronchodilator inhaler may be recommended i.e. beta-2 agonist inhalers – such as salmeterol, formoterol and indacaterol"
      " and antimuscarinic inhalers – such as tiotropium, glycopyronium and aclidinium),  "
      "if the long-acting bronchodilator inhaler didn't make any difference to the symptoms consider steroid inhalers and if the "
      "symptopms of the patients are not controlled with inhalers, recommend taking tablets or capsules as well. "
      " (Source: https://www.nhs.uk/conditions/chronic-obstructive-pulmonary-disease-copd/treatment/)."
    )
  #else patient_data['copd']:
   # recommendations.append(
     # "The patient has COPD. There are various treatment options that can discuss with the patient "
     # "such as stopping smoking "
    #  "As you are a smoker and have COPD, it is critical to quit smoking immediately."
    #  " Smoking exacerbates COPD symptoms, "
     # "causes further damage to your lungs, and worsens your overall condition."
    #)

  if patient_data['sbp'] > 130:
    recommendations.append(
      "Since the systolic blood pressure is high, consider prescribing one of the following medications"
      ", which are effective at reducing blood pressure: 1. diuretics such as Hygroton (chlorthalidone), Microzide (hydrochlorothiazide). "
      "2. Calcium channel Blocker such as Norvasc (amlodipine) and Adalat CC (nifedipine). "
      "Also, advise the patient to avoid the following substances, which can negatively impact blood pressure management i.e. "
      " Over-the-counter 'decongestant' cold medications that contain pseudoephedrine or phenylephrine, like Sudafed, chronic use of NSAIDs (nonsteroidal anti-inflammatory medications), like Motrin (ibuprofen), Advil (ibuprofen),"
      " and Aleve (naproxen). Also, black licorice and cocaine "
      "(Source: https://www.verywellhealth.com/how-to-lower-systolic-blood-pressure-5202628)."
    )
  if not patient_data['beta_blocker']:
    recommendations.append(
      "Consider administering Beta blocker therapy (Bisoprolol (Zebeta), Carvedilol (Coreg), Metoprolol (Toprol))  to the patient, if necessary. Also, the goal is to convince the patient not "
      "to neglect taking Beta blocker therapy since they are very important (Source: https://www.webmd.com/heart-disease/heart-failure/heart-failure-beta-blocker) ."
    )
  if not patient_data['ace_arb']:
    recommendations.append(
      "Consider administering ACE inhibitors (e.g. enalapril) or ARBs therapy (e.g. losartan) to the patient, if necessary. Also, the goal is to convince the patient not "
      "to neglect taking ACE inhibitors or ARB since they are very important."
    )
  creatinine = patient_data['creatinine']
  gender = patient_data['gender'].lower()
  if (gender == 'male' and creatinine > 1.2) or (gender == 'female' and creatinine > 1.1):
    recommendations.append(
      "The patient has high creatinine levels. As a doctor, you can recommend to the patient to follow a healthy lifestyle,"
      " make changes to the patient's diet to avoid stress on patient's kidneys,"
      " cut back on strenuous exercise, avoid creatine supplements "
      " and discuss to the patient the medications that can have i.e. over-the-counter medicine."
      " (Source: https://www.freseniuskidneycare.com/thrive-central/what-are-high-creatinine-levels)."
    )
  creatinine = patient_data['creatinine']
  gender = patient_data['gender'].lower()
  if (gender == 'male' and creatinine < 0.6) or (gender == 'female' and creatinine < 0.5):
    recommendations.append(
      "The patient has low creatinine levels. As a doctor, you can use multiple tests to check creatinine levels, including:\n"
      " Serum (blood) creatinine test, also known as creatine clearance test and"
      " Creatinine urine test.\n"
      "Although these tests help indicate abnormal creatinine levels, you can usually use other tests to confirm a diagnosis of underlying health conditions, such as kidney disease.\n\n"
      "These tests may include i.e. estimated glomerular filtration rate (eGFR),  "
      "comprehensive or basic metabolic panel,  muscle biopsy or muscle enzyme test. "
      "As treatment, you can recommend taking creatine supplements (especially for vegan or vegeterian) to help boost the muscle mass. Also, to eat a well-balanced diet and more high protein foods"
      " like meat and fish may help increase low creatinine levels caused by malnutrition (Source: https://www.healthline.com/health/low-creatinine#treatment.)."
    )

  if patient_data['bmi'] < 18.5:
    recommendations.append(
      "The patient has been diagnosed as underweight,  recommend a gradual, healthy weight gain strategy focusing on nutrient-dense foods. "
      "Advise against high-sugar, high-fat, and high-salt foods. Explain the reasons to take small, frequent meals"
      " and high-energy snacks such as cheese, nuts etc. Suggest strategies such as using full-cream milk, incorporating healty fats"
      " (olive oil, avocado) etc."
    )
  if patient_data['bmi'] > 29.9:
    recommendations.append(
      "The patient has been diagnosed with obesity, suggest the patient to follow some instructions to lose weight "
      " such as reducing consumption of fast foods, reducing portion sizes and reducing soda consumption "
      "(Source: https://www.jabfm.org/content/22/2/115#abstract-1)."
    )

  if 25 <= patient_data['bmi'] < 30:
    recommendations.append(
      "The patient has been diagnosed as overweight, suggest the patient to follow some instructions to lose weight "
      " such as reducing consumption of fast foods, reducing portion sizes and reducing soda consumption "
      "(Source: https://www.jabfm.org/content/22/2/115#abstract-1)."
    )

  if 18.5 < patient_data['bmi'] < 25:
    recommendations.append(
      "The patient has a normal BMI, which is a positive indicator of overall health. Encourage the patient to maintain their "
      "current weight and healthy lifestyle habits."
    )


  return main_message, recommendations


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
      "At risk for heart failure.\n"
      "In this class, belong people who are at risk for heart failure but do not yet have symptoms or structural or functional heart disease.\n"
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
      "In this class, the people consider that marked limitation of physical activity; comfortable at rest; less than ordinary activity causes fatigue, palpitation, or dyspnea.\n"
    ),
    'IV': (
      "Advanced heart failure.\n"
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
    lvef_category = "Mild dysfunction (LVEF 40% to 49%). It could be a sign of heart damage, perhaps from " \
                    "a heart condition or a previous heart attack"
  elif 30 <= lvef < 40:
    lvef_category = "Moderate dysfunction (LVEF 30% to 39%). It can also be due to cardiomyopathy, which is when the patient's  " \
                    "heart muscle weakens, making the patient's heart less effective at pumping blood to the rest of the patient's body. "
  else:
    lvef_category = "Severe dysfunction (LVEF < 30%)"

  # Diabetes explanation
  if patient_data['diabetes']:
    diabetes_info = (
      f"the patient {patient_data['name']} has been diagnosed with diabetes.\n"
      "Diabetes is a chronic disease that occurs either when the pancreas does not produce enough insulin or when the body cannot\n"
      "effectively use the insulin it produces. Insulin is a hormone that regulates blood glucose. Hyperglycaemia, also called raised blood glucose,\n"
      "is a common effect of uncontrolled diabetes and over time leads to serious damage to many of the body's systems, especially the nerves and blood vessels.\n"
    )
  else:
    diabetes_info = f"the patient {patient_data['name']} has not been diagnosed with diabetes.\n"

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

  # Smoking status
  if patient_data['smoker']:
    smoking_status = f" The patient {patient_id} is a smoker."
  else:
    smoking_status = f"The patient {patient_id} doesn't smoke."

  # COPD status
  if patient_data['copd']:
    copd_status = f" The patient {patient_id} has COPD disease. For Information, chronic obstructive pulmonary disease (COPD) is the name for a group of lung conditions that cause breathing difficulties. " \
                    "It includes: emphysema – damage to the air sacs in the lungs or chronic bronchitis – long-term inflammation of the airways. " \
                    "COPD is a common condition that mainly affects middle-aged or older adults who smoke. Many people do not realise they have it." \
                    "The breathing problems tend to get gradually worse over time and can limit your normal activities, although treatment can help " \
                    "keep the condition under control."
  else:
    copd_status = "The patient hasn't COPD disease."


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
  description = (
    f"We have patient {patient_id}, whose age is {patient_data['age']} years, and the gender is {gender}, with the following medical characteristics:\n"
    f"Regarding the NYHA class, the patient {patient_id}  belongs to Class {nyha_class_str}.\n"
    f"Based on the American Heart Association (AHA) and in collaboration with the American College of Cardiology (ACC), "
    f"Class {nyha_class_str} has the following characteristics:\n{aha_stage_message}"
    f"(Source: https://www.heart.org/en/health-topics/heart-failure/what-is-heart-failure/classes-of-heart-failure,\n"
    f"https://www.mdcalc.com/calc/3987/new-york-heart-association-nyha-functional-classification-heart-failure).\n"
    f"Also, the left ventricular ejection fraction (LVEF) of the patient {patient_id}  is {lvef:.1f}%.\nAccording to the American College of Cardiology (ACC), the patient has {lvef_category} \n"
    f"For information, Left ventricular ejection fraction (LVEF) is the central measure of left ventricular systolic function. LVEF is the fraction of chamber volume ejected in systole (stroke volume) in relation to the volume of the blood in the ventricle at the end of diastole (end-diastolic volume).\n"
    f"(Source: https://www.healthline.com/health/ejection-fraction#ejection-fraction-results, https://www.ncbi.nlm.nih.gov/books/NBK459131/).\n"
    f"Regarding diabetes, {diabetes_info}"
    f"{smoking_status}\n"  # Add smoking status
    f"{copd_status}\n"  # Add COPD status
    f"The patient's {patient_id} systolic pressure is {sbp} mm Hg and is characterized as '{sbp_category}' ({sbp_condition}).\n"
    f"Regarding heart failure medications, {beta_blocker_text} Moreover, {ace_arb_text}\n"
    f"The patient {patient_id} has a creatinine level of {creatinine} mg/dL and is categorized as {creatinine_category} ({creatinine_condition}).\n"
    f"(Source: https://www.healthline.com/health/low-creatinine#creatinine-levels.)\n"
    f"The Body Mass Index (BMI) of the patient {patient_id} is {bmi}.\n"
    f"Body mass index (BMI) is a measure of body fat based on height and weight that applies to adult men and women.\n"
    f"So, based on the existing scientific literature, the patient {patient_id} with this BMI can be characterized as '{bmi_category}'.\n"
    f"(Source: https://www.nhlbi.nih.gov/health/educational/lose_wt/BMI/bmicalc.htm.).\n"
    f"Finally, patient {patient_id} {hf_duration_status} heart failure diagnosed within the past 18 months.\n"
    f"Based on all the above characteristics, patient's {patient_id} MAGGIC score is {score} and this MAGGIC score is categorized as {category}.\n"
    f"The predicted mortality of the patient {patient_id} for 1-Year is {risk1_year}%. Namely, there is a {risk1_year}% change that the patient may not survive "
    f"within the next year due to heart-related conditions.\n"
    f"The predicted mortality of the patient {patient_id} for 3-Year is {risk3_year}%. Namely, there is a {risk3_year}% change that the patient may not survive "
    f"within the next three years due to heart-related conditions.\n"
  )

  return description


def process_file_and_calculate(filename):
  patient_data_list = []
  file_extension = os.path.splitext(filename)[-1].lower()
  output_file = "patient_descriptions.txt"

  # Handle files based on their type
  if file_extension == '.csv':
    try:
      df = pd.read_csv(filename)
      patient_data_list = df.to_dict(orient='records')
    except Exception as e:
      print(f"Error reading CSV file: {e}")

  elif file_extension == '.txt':
    try:
      with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
      headers = lines[0].strip().split(',')
      for line in lines[1:]:
        values = line.strip().split(',')
        patient_data = dict(zip(headers, values))
        patient_data_list.append(patient_data)
    except Exception as e:
      print(f"Error reading TXT file: {e}")

  elif file_extension == '.json':
    try:
      with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
      if isinstance(data, list):
        patient_data_list = data
      elif isinstance(data, dict):
        patient_data_list = [data]
      else:
        raise ValueError("Invalid JSON format: Expected a list or a dictionary.")
    except json.JSONDecodeError as e:
      print(f"Error decoding JSON file: {e}")
    except Exception as e:
      print(f"Error reading JSON file: {e}")

  elif file_extension in ['.xls', '.xlsx']:
    try:
      df = pd.read_excel(filename, sheet_name=0)
      patient_data_list = df.to_dict(orient='records')
    except Exception as e:
      print(f"Error reading Excel file: {e}")

  elif file_extension == '.pdf':
    try:
      with open(filename, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
          page_text = page.extract_text()
          if page_text:
            text += page_text + "\n"

      lines = [line.strip() for line in text.split('\n') if line.strip()]
      if lines:
        headers = lines[0].split(',')
        for line in lines[1:]:
          values = line.split(',')
          if len(values) == len(headers):
            patient_data = dict(zip(headers, values))
            patient_data_list.append(patient_data)
    except Exception as e:
      print(f"Error reading PDF file: {e}")

  # Process patient data and write to output file
  results = []
  with open(output_file, 'w', encoding='utf-8') as output:
    for idx, raw_data in enumerate(patient_data_list):
      try:
        # Parse patient data
        patient_data = parse_patient_data(raw_data, idx + 1)
        patient_id = patient_data['name'] if patient_data['name'] else f"Patient {idx + 1}"
        score = calculate_maggic_score(patient_data)
        risk1_year = calculate_1_year_risk(score)
        risk3_year = calculate_3_year_risk(score)
        category = get_risk_category(score)

        # Generate messages for the patient and doctor
        patient_main_message, patient_recommendations = generate_health_message_patient(score, patient_data)
        doctor_main_message, doctor_recommendations = generate_health_message_doctor(score, patient_data)

        # Generate detailed description for the patient
        detailed_description = generate_patient_description(
          patient_id=patient_id,
          patient_data=patient_data,
          score=score,
          risk1_year=risk1_year,
          risk3_year=risk3_year,
          category=category
        )

        # Write to the patient_descriptions.txt file
        output.write(f"{patient_id}\n")
        output.write(f"{detailed_description}\n")
        output.write("MESSAGE FOR PATIENT:\n")
        output.write(f"{patient_main_message}\n")
        output.write(f"RECOMMENDATIONS FOR PATIENT {patient_id}:\n")
        for rec in patient_recommendations:
          output.write(f"- {rec}\n")
        output.write("\nMESSAGE FOR DOCTOR:\n")
        output.write(f"{doctor_main_message}\n")
        output.write(f"RECOMMENDATIONS FOR DOCTOR TO PATIENT {patient_id}:\n")
        for rec in doctor_recommendations:
          output.write(f"- {rec}\n")
        output.write("\n" + "-" * 80 + "\n")

        # Add result to the results list
        results.append({
          "patient_id": patient_id,
          "patient_data": patient_data,
          "detailed_description": detailed_description,
          "score": score,
          "risk1_year": risk1_year,
          "risk3_year": risk3_year,
          "category": category,
          "patient_message": (patient_main_message, patient_recommendations),
          "doctor_message": (doctor_main_message, doctor_recommendations)
        })
      except Exception as e:
        print(f"Error processing patient data for {patient_id}: {e}")

  print(f"Patient descriptions have been saved to {output_file}")
  return results


def run_model(file_path):
  return process_file_and_calculate(file_path)

