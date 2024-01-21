from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import pandas as pd
import nltk
import os
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import pos_tag

app = Flask(__name__)

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

def fetch_html_content(url):
    """Fetch the HTML content of a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def extract_data_chunk_ids(html_content):
    """Extract and return data chunk IDs from the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for div in soup.find_all('div', class_='search-results-chunk'):
        if 'data-chunk-ids' in div.attrs:
            return div['data-chunk-ids'].split(',')
    return []

def fetch_abstracts(chunk_ids):
    """Fetch and return the abstract for each PubMed article ID."""
    abstracts = ''
    i = 0
    for chunk_id in chunk_ids:
        url = f'https://pubmed.ncbi.nlm.nih.gov/{chunk_id}/'
        page_content = fetch_html_content(url)
        if page_content:
            soup = BeautifulSoup(page_content, 'html.parser')
            div = soup.find('div', {'class': 'abstract-content selected'})
            if div and i <= 100:
                abstracts = abstracts + div.get_text(strip=True) + '\n\n'
                i = i + 1
            else:
                print(f"Abstract not found for {chunk_id}")
        else:
            print(f"Failed to fetch content for {chunk_id}")
    return abstracts

def get_content_individual_statistics(content):
    """
    Given a piece of content, calculate various statistics about the content including:
    - The content itself
    - The unique words in the content
    - The nouns in the content
    - The adjectives in the content
    - The verbs in the content
    """
    words = word_tokenize(content)
    unique_words = set(words)
    nouns = [word for word, pos in pos_tag(words) if pos.startswith('NN')]
    adjectives = [word for word, pos in pos_tag(words) if pos.startswith('JJ')]
    verbs = [word for word, pos in pos_tag(words) if pos.startswith('VB')]

    return {
        'content': content,
        'unique_words': list(unique_words),
        'nouns': nouns,
        'adjectives': adjectives,
        'verbs': verbs
    }

def calculate_statistics(abstracts):
    """
    Calculate various statistics from a given text abstract.
    @param abstracts - the text abstract to analyze
    @return a pandas DataFrame containing the calculated statistics:
    - num_sentences: the number of sentences in the abstract
    - num_words: the number of words in the abstract
    - average_word_length: the average length of words in the abstract
    - num_unique_words: the number of unique words in the abstract
    - num_characters: the total number of characters in the abstract
    - num_nouns: the number of nouns in the abstract
    - num_adjectives: the number of adjectives in the abstract
    - num_verbs: the number of verbs in the abstract
    """
    sentences = sent_tokenize(abstracts)
    words = word_tokenize(abstracts)
    word_lengths = [len(word) for word in words]
    unique_words = set(words)
    nouns = [word for word, pos in pos_tag(words) if pos.startswith('NN')]
    adjectives = [word for word, pos in pos_tag(words) if pos.startswith('JJ')]
    verbs = [word for word, pos in pos_tag(words) if pos.startswith('VB')]

    stats = [{
        'num_sentences': len(sentences),
        'num_words': len(words),
        'average_word_length': sum(word_lengths) / len(words) if words else 0,
        'num_unique_words': len(unique_words),
        'num_characters': sum(word_lengths),
        'num_nouns': len(nouns),
        'num_adjectives': len(adjectives),
        'num_verbs': len(verbs)
    }]
    return pd.DataFrame(stats)

"""This is a Flask route that compares statistics. It receives a POST request with data in the request body. It performs the following steps:"""
@app.route('/compareStatistics', methods=['POST'])
def compare_statistics():
    content = request.data.decode('utf-8')  # Assuming the content is sent as text
    try :
        if not os.path.isfile('aggregated_results.csv'):
            fetch_analyze_save()
        
        orginal_stats = pd.read_csv('aggregated_results.csv')
        stats = calculate_statistics(content)
        if len(stats) == 0:
            raise Exception('Some Exception Occured. Please Try again later')
        
        orginal_stats = pd.concat([orginal_stats, stats], ignore_index=True)
        orginal_stats['file_type'] = ['Default Statistics', 'User Input Statistics']
        
        return_dict = get_content_individual_statistics(content)
        return_dict['statistics'] = orginal_stats.to_dict(orient='records')
        
        print(return_dict)
        return jsonify(return_dict), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Some Exception Occured when trying to fetch results."}), 500

def fetch_analyze_save():
    """
    This function fetches data from a PubMed search, analyzes the abstracts, and saves the results to a CSV file.
    @return A JSON response with a success message if the process is completed successfully.
    @raises Exception if there is an error fetching the HTML content or if there are no data chunk IDs found.
    """

    search_url = f'https://pubmed.ncbi.nlm.nih.gov/?term=heart&size=200'
    html_content = fetch_html_content(search_url)

    if html_content:
        chunk_ids = extract_data_chunk_ids(html_content)
        if chunk_ids:
            abstracts = fetch_abstracts(chunk_ids)
            aggregated_stats = calculate_statistics(abstracts)
            aggregated_stats.to_csv('aggregated_results.csv', header=True, index=False)
            return jsonify({"message": "Abstracts and aggregated statistics saved to files."})
        else:
            raise Exception('Some Exception Occured. Please Try again later')
    else:
        raise Exception('Some Exception Occured. Please Try again later')

"""Create a Flask route that handles GET requests to the '/get' endpoint. When a GET request is made to this endpoint, 
the function will return a JSON response with the message "Hello" and a status code of 200."""

@app.route('/get', methods=['GET'])
def get_api():
    return jsonify("Helo"), 200

if __name__ == '__main__':
    app.run(debug=True)