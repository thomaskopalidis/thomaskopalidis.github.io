For the Project of AI4f

Medical decision support tool (maggic risk, maggic risk+ etc.)
General description
This project is a computational health risk assessment tool designed to calculate patient health risks using the MAGGIC Risk Model initially, and in the future, additional models such as the improved MAGGIC Risk Plus Model. The system is implemented in a user-friendly, web-based environment where users can upload patient data files and receive analytical results.
_______________________________________
Functionality
1.	Upload Patient Data
Users can upload patient data files containing clinical information in various formats, such as CSV, TXT, JSON, Excel, or PDF.
The system reads the uploaded file and validates it by checking the file extension to ensure it is one of the supported formats and the content structure to verify that required fields, such as age, gender, and clinical parameters, are included. 
If the file is invalid, the interface displays an error message to notify the user.
2.	Model selection
Users select the model to be used for risk assessment.
The models include between the basic MAGGIC Risk model or choose another model such as MAGGIC Risk Plus model (currently under development and includes additional parameters and refined scoring mechanisms. We are waiting for detailed results from Oxford). Future updates will allow for the addition of more models as needed.
3.	Data Processing
The data processing step is a crucial component of the MAGGIC Risk Calculator. It involves transforming raw patient data into actionable insights by analyzing the data and calculating relevant risk scores.
The system extracts and structures the information from the uploaded file. For example:
•	In Excel files, data is extracted row by row from specific sheets.
•	In JSON files, structured objects are used to retrieve patient attributes.
Τhen the MAGGIC score is derived from a comprehensive set of patient-specific parameters, including:
•	Demographics: Age and gender.
•	Clinical Parameters: LVEF (Left Ventricular Ejection Fraction), BMI (Body Mass Index), NYHA Class (New York Heart Association Classification), SBP (Systolic Blood Pressure), and creatinine levels.
•	Comorbidities: Smoking status, diabetes, COPD (Chronic Obstructive Pulmonary Disease).
•	Medications: Use of beta-blockers or ACE inhibitors.
Each parameter is assigned a specific point value based on validated scoring tables, and the total score is calculated.
Based on the calculated MAGGIC score, the system categorizes patients into:
•	Low Risk: Score < 20
•	Moderate Risk: Score 20–30
•	High Risk: Score > 30
4.	Mortality risk calculation
The next phase is to estimate the likelihood of patient mortality based on the calculated MAGGIC score. The system calculates the probability of mortality within the first year and three years based on the MAGGIC score. Essentially, these predictions help clinicians prioritize patient care and allocate resources effectively.
5.	Production of Analytical Reports
The purpose of this step is to generate detailed reports that provide a comprehensive summary of the patient’s clinical profile, risk assessment, and personalized recommendations.
The reports include the following:
i)	    Medical Data Interpretation
    Each patient’s clinical parameters, such as LVEF and BMI, are analyzed and interpreted with additional insights to provide a deeper understanding of their health status.
ii)	Risk Predictions
    The reports present the calculated MAGGIC score, the associated risk category (low, moderate, or high), and the predicted probabilities of mortality over 1 and 3 years.  			        iii)   Personalized Messages and Recommendations
        Messages are tailored based on the patient’s MAGGIC score, which determines their risk level.    
Recommendations are further customized to the patient’s specific characteristics, including:           -Guidance on managing comorbidities such as diabetes or COPD.
-Suggested lifestyle changes for conditions like high BMI or systolic blood pressure (SBP).
 -Medication recommendations, such as starting or adjusting beta-blockers or ACE inhibitors, to optimize treatment outcomes.
All detailed descriptions, messages, and recommendations are exported to a .txt file. For the reason to form the dataset to train the Agent, enabling it to generate relevant insights and support decision-making in the future.
 
 

 
 
 
