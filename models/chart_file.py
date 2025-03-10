import matplotlib
matplotlib.use('Agg')  # For servers without a display
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.pyplot as plt
from collections import Counter
def generate_scatter_plot(results):
    """
    Generate a 2-in-1 figure with:
      1) A scatter plot of MAGGIC scores vs. patient index (with point annotations).
      2) A bar chart of how many patients fall into each risk category (Low/Medium/High).
    Returns a base64-encoded PNG image.
    """

    # 1. Extract MAGGIC scores
    scores = [r['score'] for r in results]
    # We'll treat each patient index as x = 1..N
    indices = list(range(1, len(scores)+1))

    # 2. Determine risk categories and count how many patients fall in each
    low_count = sum(s < 20 for s in scores)
    medium_count = sum(20 <= s <= 30 for s in scores)
    high_count = sum(s > 30 for s in scores)

    # 3. Create the figure with 2 subplots vertically
    fig, ax = plt.subplots(2, 1, figsize=(8, 10), sharex=False)
    fig.subplots_adjust(hspace=0.4)  # Increase vertical space between subplots

    # -- SUBPLOT 1: SCATTER PLOT --
    ax[0].scatter(indices, scores, c='blue', alpha=0.7)
    ax[0].set_title('MAGGIC Scores by Patient Number', fontsize=14)
    ax[0].set_xlabel('Patient #')
    ax[0].set_ylabel('MAGGIC Score')
    ax[0].grid(True)

    # Annotate each point with its patient index (1-based)
    for i, score in enumerate(scores, start=1):
        # Adjust the x offset (0.1) to avoid overlapping the point
        ax[0].annotate(str(i), (i, score), (i+0.1, score), fontsize=9)

    # -- SUBPLOT 2: BAR CHART OF RISK CATEGORIES --
    categories = ['Low (<20)', 'Medium (20-30)', 'High (>30)']
    counts = [low_count, medium_count, high_count]
    colors = ['yellow', 'orange', 'red']

    ax[1].bar(categories, counts, color=colors, alpha=0.8)
    ax[1].set_title('Number of Patients by Risk Category', fontsize=14)
    ax[1].set_ylabel('Number of Patients')
    # You could also label each bar with the exact count
    for idx, count in enumerate(counts):
        ax[1].text(idx, count + 0.1, str(count), ha='center', va='bottom', fontsize=11)

    # 4. Convert the figure to PNG and then to base64
    png_image = io.BytesIO()
    plt.savefig(png_image, format='png', bbox_inches='tight')
    png_image.seek(0)
    plt.close(fig)

    encoded_png = base64.b64encode(png_image.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded_png}"
