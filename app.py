from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from github import Github

app = Flask(__name__)

# Set the folder to temporarily store uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions (customize as needed)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf'}

# GitHub repository details
GITHUB_TOKEN = ''  # Replace with your GitHub token
REPO_NAME = ''        # Replace with your GitHub repo name (e.g., 'username/repo')
BRANCH = 'main'                              # Replace with your branch name

# Initialize GitHub instance
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to upload file to GitHub
def push_to_github(filepath, filename):
    with open(filepath, 'rb') as file:
        content = file.read()

    # GitHub path where the file will be uploaded (e.g., 'uploads/filename')
    git_path = f'uploads/{filename}'

    # Check if file already exists in GitHub to update it instead of creating a new one
    try:
        existing_file = repo.get_contents(git_path, ref=BRANCH)
        repo.update_file(existing_file.path, f"Update {filename}", content, existing_file.sha, branch=BRANCH)
        return f'Updated file {filename} in GitHub'
    except:
        # If file doesn't exist, create it
        repo.create_file(git_path, f"Add {filename}", content, branch=BRANCH)
        return f'Created file {filename} in GitHub'

# Route to handle file upload and push to GitHub
@app.route('/upload-to-github', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    # If no file was selected
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Validate the file type
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)  # Sanitize the filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the file temporarily
        file.save(file_path)

        # Push the file to GitHub
        try:
            github_message = push_to_github(file_path, filename)
            return jsonify({'message': github_message}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Optionally delete the local file after pushing to GitHub
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    # Create the upload directory if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
