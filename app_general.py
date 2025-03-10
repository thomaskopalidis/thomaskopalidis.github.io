from flask import Flask, request, redirect, session, render_template, flash
from werkzeug.utils import secure_filename
import os

# Import the scatter plot generator
from models.chart_file import generate_scatter_plot

from models.maggic_risk_model import run_model as run_maggic  # MAGGIC Risk
from models.maggic_risk_plus import run_model as run_maggic_plus  # MAGGIC Risk Plus

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt', 'json', 'xls', 'xlsx', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Sample translations for English, French, and German
translations = {
    'en': {
        'title': "MAGGIC Risk Calculator - Results",
        'upload_prompt': "Upload Your File",
        'language': "Language",
        'maggic_score': "MAGGIC Score",
        'risk_category': "Risk Category",
        'low_risk': "Low Risk",
        'medium_risk': "Medium Risk",
        'high_risk': "High Risk",
        'results': "MAGGIC Risk Calculator Results",
        'upload_new': "Upload New File"
    },
    'fr': {
        'title': "Calculateur de Risque MAGGIC - Résultats",
        'upload_prompt': "Téléchargez Votre Fichier",
        'language': "Langue",
        'maggic_score': "Score MAGGIC",
        'risk_category': "Catégorie de Risque",
        'low_risk': "Risque Faible",
        'medium_risk': "Risque Moyen",
        'high_risk': "Risque Élevé",
        'results': "Résultats du Calculateur de Risque MAGGIC",
        'upload_new': "Télécharger un Nouveau Fichier"
    },
    'de': {
        'title': "MAGGIC Risiko-Rechner - Ergebnisse",
        'upload_prompt': "Laden Sie Ihre Datei Hoch",
        'language': "Sprache",
        'maggic_score': "MAGGIC-Punkte",
        'risk_category': "Risikokategorie",
        'low_risk': "Niedriges Risiko",
        'medium_risk': "Mittleres Risiko",
        'high_risk': "Hohes Risiko",
        'results': "Ergebnisse des MAGGIC Risiko-Rechners",
        'upload_new': "Neue Datei Hochladen"
    }
}


@app.route('/')
def upload_form():
  """Render the upload form on the homepage."""
  language = request.args.get('lang', 'en')  # Default to English if no language is selected
  session['language'] = language  # Store selected language in session
  return render_template('upload.html', translations=translations[language], language=language)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and model selection."""
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

        selected_model = request.form.get('model')
        language = session.get('language', 'en')  # Get selected language from session
        # Run the appropriate MAGGIC model
        if selected_model == 'maggic_plus':
            results = run_maggic_plus(file_path)
        else:
            results = run_maggic(file_path)

        # Remove the uploaded file after processing
        os.remove(file_path)

        # Generate a scatter plot for all patients (only if there's more than one patient)
        group_chart = None
        if len(results) > 1:
            group_chart = generate_scatter_plot(results)

        # Render the template, passing in the results and the base64-encoded chart
        return render_template('results_update.html',
                               results=results,
                               model=selected_model,
                               group_chart=group_chart,
                               translations=translations[language],
                               language=language)

    else:
        flash('Unsupported file type')
        return redirect(request.url)

if __name__ == "__main__":
    app.run(debug=True)
