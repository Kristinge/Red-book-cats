from flask import Flask, render_template, send_from_directory, request, redirect, url_for
from openpyxl import load_workbook
import urllib.parse
import os

app = Flask(__name__)

# Excel faila atrašanās vieta
EXCEL_FILE = "info_kopsavilkums.xlsx"
BASE_DIR = os.getcwd()

# Fails komentāru saglabāšanai
COMMENTS_FILE = "comments.txt"

def read_excel():
    """Nolasa Excel failu un izveido sarakstu ar kaķu informāciju."""
    try:
        wb = load_workbook(EXCEL_FILE)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]
        cats = []

        for row in sheet.iter_rows(min_row=2, values_only=True):
            cat_info = dict(zip(headers, row))
            cat_name = cat_info.get("Nosaukums", "").strip()
            image_filename = f"{cat_name}.jpg"
            image_path = os.path.join(BASE_DIR, image_filename)

            if os.path.exists(image_path):
                cat_info["Attēls"] = f"/image/{image_filename}"
            else:
                cat_info["Attēls"] = "/image/default.jpg"

            cats.append(cat_info)

        return cats
    except Exception as e:
        return [{"Kļūda": f"Neizdevās atvērt Excel failu: {e}"}]

@app.route('/')
def home():
    """Galvenā lapa ar kaķu sarakstu un attēliem."""
    order = request.args.get("order", "asc")
    cats = read_excel()

    # Sakārtojam kaķus pēc nosaukuma
    cats = sorted(cats, key=lambda x: x["Nosaukums"], reverse=(order == "desc"))
    return render_template('index.html', cats=cats, order=order)

@app.route('/cat/<path:name>')
def cat_detail(name):
    """Atsevišķa kaķa detalizētā informācija."""
    cats = read_excel()
    decoded_name = urllib.parse.unquote(name).replace('-', ' ')
    
    selected_cat = next((cat for cat in cats if cat['Nosaukums'].strip().lower() == decoded_name.strip().lower()), None)

    if selected_cat:
        return render_template('cat.html', cat=selected_cat)
    else:
        return "Kaķis nav atrasts!", 404

@app.route('/image/<filename>')
def get_image(filename):
    """Attēlu apkalpošana."""
    return send_from_directory(BASE_DIR, filename)

@app.route('/comments', methods=["GET", "POST"])
def comments():
    """Lapa komentāru rakstīšanai un skatīšanai."""
    if request.method == "POST":
        comment = request.form.get("comment")
        if comment:
            with open(COMMENTS_FILE, "a", encoding="utf-8") as file:
                file.write(comment + "\n")
        return redirect(url_for('comments'))

    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, "r", encoding="utf-8") as file:
            comments = file.readlines()
    else:
        comments = []

    return render_template('comments.html', comments=comments)

@app.route('/delete_comment/<int:comment_index>', methods=["POST"])
def delete_comment(comment_index):
    """Dzēš konkrētu komentāru pēc tā indeksa."""
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, "r", encoding="utf-8") as file:
            comments = file.readlines()

        if 0 <= comment_index < len(comments):
            del comments[comment_index]

            with open(COMMENTS_FILE, "w", encoding="utf-8") as file:
                file.writelines(comments)

    return redirect(url_for('comments'))

if __name__ == '__main__':
    app.run(debug=True)
