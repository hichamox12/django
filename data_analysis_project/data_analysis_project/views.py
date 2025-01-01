from django.shortcuts import render
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import bernoulli, binom, uniform, poisson, expon, norm
import numpy as np
from io import BytesIO
import base64

def home_view(request):
    context = {}

    # Check if a dataframe is available in the session
    df = None
    if 'df' in request.session:
        try:
            df = pd.read_json(request.session['df'])
            context['data_preview'] = df.head().to_html(classes="table table-bordered")
            context['numeric_cols'] = df.select_dtypes(include=['number']).columns.tolist()
            context['columns'] = df.columns.tolist()
        except Exception as e:
            context['error'] = f"Error loading data from session: {str(e)}"

    # Handle File Upload
    if request.method == 'POST' and 'file_upload' in request.POST:
        try:
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file)
            request.session['df'] = df.to_json()  # Save the dataframe as JSON in the session

            context['data_preview'] = df.head().to_html(classes="table table-bordered")
            context['numeric_cols'] = df.select_dtypes(include=['number']).columns.tolist()
            context['columns'] = df.columns.tolist()
        except Exception as e:
            context['error'] = f"Error uploading file: {str(e)}"

    # Handle Statistics Calculation
    if request.method == 'POST' and 'calculate_stats' in request.POST:
        if df is not None:
            try:
                selected_column = request.POST.get('selected_column')
                stats = {
                    'Mean': df[selected_column].mean(),
                    'Median': df[selected_column].median(),
                    'Mode': df[selected_column].mode().iloc[0] if not df[selected_column].mode().empty else "No Mode",
                    'Variance': df[selected_column].var(),
                    'Standard Deviation': df[selected_column].std(),
                    'Range': df[selected_column].max() - df[selected_column].min(),
                }
                context['stats'] = stats
            except Exception as e:
                context['error'] = f"Error calculating statistics: {str(e)}"
        else:
            context['error'] = "No data available. Please upload a file first."

    # Handle Visualization
    if request.method == 'POST' and 'generate_visualization' in request.POST:
        if df is not None:
            try:
                selected_column = request.POST.get('selected_column')
                visualization_type = request.POST.get('visualization_type')

                fig, ax = plt.subplots(figsize=(8, 6))
                if visualization_type == "Line Plot":
                    sns.lineplot(data=df, x=df.index, y=selected_column, ax=ax)
                elif visualization_type == "Box Plot":
                    sns.boxplot(data=df, y=selected_column, ax=ax)
                elif visualization_type == "Histogram":
                    sns.histplot(data=df, x=selected_column, bins=20, ax=ax)
                elif visualization_type == "KDE Plot":
                    sns.kdeplot(data=df, x=selected_column, ax=ax)
                elif visualization_type == "Violin Plot":
                    sns.violinplot(data=df, y=selected_column, ax=ax)
                elif visualization_type == "Scatter Plot" and len(df.columns) > 1:
                    scatter_column = request.POST.get('scatter_column')
                    sns.scatterplot(data=df, x=selected_column, y=scatter_column, ax=ax)

                ax.set_title(f"{visualization_type} of {selected_column}")
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                context['visualization_chart'] = base64.b64encode(buffer.read()).decode('utf-8')  # Modifié ici
                buffer.close()
                plt.close(fig)
            except Exception as e:
                context['error'] = f"Error generating visualization: {str(e)}"
        else:
            context['error'] = "No data available. Please upload a file first."

    # Handle Probability Distributions
    if request.method == 'POST' and 'generate_distribution' in request.POST:
        if df is not None:
            try:
                column = request.POST.get('column', None)
                distribution_type = request.POST.get('distribution_type', '')
                params = {
                    'n': int(request.POST.get('n', 10)),
                    'p': float(request.POST.get('p', 0.5)),
                    'lambda': float(request.POST.get('lambda', 1.0)),
                    'a': float(request.POST.get('a', 0)),
                    'b': float(request.POST.get('b', 1))
                }

                if column and column in df.select_dtypes(include=['number']).columns:
                    data = df[column].dropna()

                    x = np.linspace(data.min(), data.max(), 500)

                    fig, ax = plt.subplots(figsize=(10, 6))
                    if distribution_type == "bernoulli":
                        rv = bernoulli(params['p'])
                        ax.bar([0, 1], rv.pmf([0, 1]), color='skyblue')
                    elif distribution_type == "binomial":
                        rv = binom(params['n'], params['p'])
                        ax.bar(range(params['n'] + 1), rv.pmf(range(params['n'] + 1)), color='skyblue')
                    elif distribution_type == "poisson":
                        rv = poisson(params['lambda'])
                        ax.bar(range(20), rv.pmf(range(20)), color='skyblue')
                    elif distribution_type == "uniform":
                        ax.plot(x, uniform.pdf(x, loc=params['a'], scale=params['b'] - params['a']), color='green')
                    elif distribution_type == "exponential":
                        ax.plot(x, expon.pdf(x, scale=1 / params['lambda']), color='orange')
                    elif distribution_type == "normal":
                        ax.plot(x, norm.pdf(x, loc=data.mean(), scale=data.std()), color='purple')

                    ax.set_title(f"Distribution: {distribution_type.capitalize()} for {column}")
                    ax.grid(True)

                    buffer = BytesIO()
                    plt.savefig(buffer, format="png")
                    buffer.seek(0)
                    context['distribution_chart'] = base64.b64encode(buffer.read()).decode('utf-8')  # Modifié ici
                    buffer.close()
                    plt.close(fig)
                else:
                    context['error'] = "Please select a valid numeric column."
            except Exception as e:
                context['error'] = f"Error generating distribution: {str(e)}"
        else:
            context['error'] = "No data available. Please upload a file first."

    return render(request, 'home.html', context)